import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, ".github", "skills", "webmethods-fsd", "scripts")
PACKAGES = [os.path.join(ROOT, "sample", p) for p in ("OrderProcessing", "CommonUtils")]
sys.path.insert(0, SCRIPTS)

import check_mermaid  # noqa: E402
import wm_extract  # noqa: E402


def run_extractor(out):
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "wm_extract.py"), "--out", out, *PACKAGES],
                   check=True, capture_output=True)


class ExtractorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = cls.tmp.name
        run_extractor(cls.out)
        with open(os.path.join(cls.out, "inventory.json")) as f:
            cls.inv = json.load(f)
        cls.arch = cls.inv["architecture"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, rel):
        with open(os.path.join(self.out, rel)) as f:
            return f.read()

    def service_md(self, name):
        return self.read(os.path.join("services", name.replace(":", "__") + ".md"))

    def flags(self, name):
        return " | ".join(self.inv["semantic_flags"].get(name, []))

    def test_inventory(self):
        self.assertEqual(self.inv["entry_points"],
                         ["order.api.orders:_get", "order.process:cancelOrder", "order.process:submitOrder"])
        self.assertEqual(self.inv["triggered"], ["order.process:cancelOrder", "order.process:submitOrder"])
        self.assertEqual(len(self.inv["nodes"]), 12)
        self.assertIn("HTTP/REST call", self.inv["integrations"])
        self.assertIn("Adapter service (jdbc)", self.inv["integrations"])

    def test_secrets_redacted(self):
        md = self.service_md("order.jdbc:insertOrder")
        self.assertIn("***redacted***", md)
        self.assertNotIn("placeholder-do-not-use", md)
        self.assertIn("INSERT INTO ORDERS", md)

    def test_java_body_extracted(self):
        self.assertIn("Double.parseDouble", self.service_md("order.process:validateOrder"))

    def test_repeat_loops_back_and_exits_from_repeat_node(self):
        md = self.service_md("order.process:submitOrder")
        rid = re.search(r'(n\d+)\(\["REPEAT', md).group(1)
        self.assertRegex(md, rf'n\d+ -->\|"retry"\| {rid}\n')
        self.assertRegex(md, rf'{rid} --> n\d+\n')

    def test_repeat_counts_total_attempts(self):
        self.assertIn("max 4 attempts", self.service_md("order.process:submitOrder"))

    def test_semantic_flags_submit_order(self):
        f = self.flags("order.process:submitOrder")
        for expected in ("`$default` also catches", "`lineAmounts` is set but never used", "`lastError`",
                         "`header/status`", "`status` is passed to adapter", "floating-point",
                         "discards the outputs"):
            self.assertIn(expected, f)

    def test_no_false_positive_flags(self):
        f = self.flags("order.process:submitOrder")
        for used in ("orderId", "customerId", "amount", "url"):
            self.assertNotIn(f"`{used}` is set but never used", f)
        for clean in ("order.jdbc:insertOrder", "order.process:cancelOrder", "order.api.orders:_get",
                      "common.util:logEvent"):
            self.assertNotIn(clean, self.inv["semantic_flags"])

    def test_semantic_flags_java_and_triggers(self):
        self.assertIn("floating-point", self.flags("order.process:validateOrder"))
        self.assertIn("ISRuntimeException", self.flags("order.triggers:orderTrigger"))
        self.assertIn("ISRuntimeException", self.flags("order.triggers:cancelTrigger"))

    def test_architecture_roles(self):
        roles = self.arch["roles"]
        self.assertEqual(roles["order.api.orders:_get"], "Entry: REST GET /rest/order/api/orders")
        self.assertEqual(roles["order.process:submitOrder"], "Entry: trigger order.triggers:orderTrigger")
        self.assertEqual(roles["common.util:logEvent"], "Shared utility")
        self.assertEqual(roles["order.jdbc:updateOrderStatus"], "Data access (adapter)")
        self.assertEqual(roles["order.process:validateOrder"], "Business logic (Java)")
        self.assertEqual(self.arch["shared_components"], ["common.util:logEvent"])

    def test_architecture_data_access_and_cross_package(self):
        self.assertEqual(self.arch["data_access"]["ORDERS"], {
            "order.api.orders:_get": ["SELECT"],
            "order.process:cancelOrder": ["UPDATE"],
            "order.process:submitOrder": ["INSERT"]})
        self.assertEqual(list(self.arch["cross_package_calls"]), ["OrderProcessing -> CommonUtils"])
        self.assertEqual(self.arch["endpoints"]["order.process:submitOrder"], ["https://payments.internal/charge"])

    def test_architecture_observations(self):
        obs = " | ".join(self.arch["observations"])
        self.assertIn("Table `ORDERS` is shared by 3 capabilities", obs)
        self.assertIn("`order.process:submitOrder` has no logging", obs)
        self.assertIn("Error handling is inconsistent", obs)
        self.assertIn("Hard-coded URL", obs)
        self.assertIn("share connection `OrderDB_Conn`", obs)
        self.assertNotIn("doesn't declare it", obs)

    def test_architecture_md_and_role_lines(self):
        md = self.read("architecture.md")
        self.assertIn("## Component diagram (component level)", md)
        self.assertIn('x_tbl_0[("ORDERS table")]', md)
        self.assertIn("- **Role:** Shared utility", self.service_md("common.util:logEvent"))

    def test_all_generated_mermaid_is_valid(self):
        files = [os.path.join(self.out, "architecture.md"), os.path.join(self.out, "callgraphs.md")]
        files += [os.path.join(self.out, "services", f) for f in os.listdir(os.path.join(self.out, "services"))]
        self.assertEqual(check_mermaid.main(files), 0)


class LargeApplicationTest(unittest.TestCase):
    def test_component_diagram_falls_back_to_folder_level(self):
        with tempfile.TemporaryDirectory() as out, \
                mock.patch.object(wm_extract, "MAX_DIAGRAM_NODES", 5), \
                mock.patch.object(sys, "argv", ["wm_extract.py", "--out", out, *PACKAGES]):
            wm_extract.main()
            with open(os.path.join(out, "architecture.md")) as f:
                md = f.read()
        self.assertIn("## Component diagram (folder level)", md)
        self.assertIn('fd_OrderProcessing_order_jdbc["order.jdbc - 3 component(s)"]', md)
        self.assertEqual(check_mermaid.lint_block(md.split("```mermaid\n")[2].split("```")[0])[1], [])

    def test_undeclared_package_dependency_is_flagged(self):
        nodes = {
            "a:x": {"name": "a:x", "package": "A", "folder": "a", "svc_type": "flow", "node_type": "service",
                    "ndf": {}, "flow": {"invokes": ["b:y"], "lines": [], "endpoints": []}},
            "b:y": {"name": "b:y", "package": "B", "folder": "b", "svc_type": "flow", "node_type": "service",
                    "ndf": {}, "flow": {"invokes": [], "lines": [], "endpoints": []}},
        }
        pkgs = [{"package": "A", "requires": [], "nodes": [nodes["a:x"]]},
                {"package": "B", "requires": [], "nodes": [nodes["b:y"]]}]
        arch = wm_extract.build_architecture(pkgs, nodes, {}, ["a:x"], [], {})
        self.assertTrue(any("doesn't declare it" in o for o in arch["observations"]))
        self.assertIn('-->|"undeclared"|', arch["package_mermaid"])


class AssembleTest(unittest.TestCase):
    def test_sections_joined_in_name_order(self):
        with tempfile.TemporaryDirectory() as d:
            for name, body in (("30-b.md", "B\n"), ("00-a.md", "A\n"), ("90-c.md", "C\n"), ("notes.txt", "x")):
                with open(os.path.join(d, name), "w") as f:
                    f.write(body)
            out = os.path.join(d, "out", "FSD.md")
            subprocess.run([sys.executable, os.path.join(SCRIPTS, "assemble_fsd.py"), "--sections", d, "--out", out],
                           check=True, capture_output=True)
            with open(out) as f:
                self.assertEqual(f.read(), "A\n\nB\n\nC\n")


class MermaidLintTest(unittest.TestCase):
    def test_detects_common_errors(self):
        _, errs = check_mermaid.lint_block("sequenceDiagram\n  alt x\n  A->>B: one; two\n")
        self.assertTrue(any("';'" in e for e in errs))
        self.assertTrue(any("missing 'end'" in e for e in errs))
        _, errs = check_mermaid.lint_block('flowchart TD\n  A["unclosed] --> B\n')
        self.assertTrue(errs)
        _, errs = check_mermaid.lint_block('flowchart LR\n  subgraph g["G"]\n    a["A"]\n')
        self.assertTrue(any("missing 'end'" in e for e in errs))

    def test_accepts_valid_multiline_blocks(self):
        self.assertEqual(check_mermaid.lint_block("classDiagram\n  class A {\n    +string x\n  }\n")[1], [])
        self.assertEqual(check_mermaid.lint_block('flowchart LR\n  subgraph g["G"]\n    a["A"]\n  end\n')[1], [])

    def test_generated_fsd_diagrams_are_valid(self):
        self.assertEqual(check_mermaid.main([os.path.join(ROOT, "docs", "FSD.md")]), 0)


class FsdContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "docs", "FSD.md")) as f:
            cls.fsd = f.read()

    def test_is_one_overall_fsd_with_architecture(self):
        self.assertIn("## 3. Existing Architecture", self.fsd)
        for cap in ("### 5.1 CAP-01", "### 5.2 CAP-02", "### 5.3 CAP-03"):
            self.assertIn(cap, self.fsd)
        self.assertIn("stateDiagram-v2", self.fsd)
        self.assertIn("**How the capabilities behave together**", self.fsd)

    def test_has_reimplementation_section_and_tests(self):
        self.assertIn("## 12. Re-implementation Notes", self.fsd)
        self.assertIn("**12.5 Acceptance test cases**", self.fsd)

    def test_every_node_is_covered(self):
        with tempfile.TemporaryDirectory() as out:
            run_extractor(out)
            with open(os.path.join(out, "inventory.json")) as f:
                names = json.load(f)["nodes"]
        for name in names:
            self.assertIn(f"`{name}`", self.fsd)

    def test_cross_references_resolve(self):
        for prefix in ("D", "Q", "A", "T"):
            defined = set(re.findall(rf"^\| {prefix}(\d+) \|", self.fsd, re.M))
            used = set(re.findall(rf"\b{prefix}(\d+)\b", self.fsd))
            self.assertEqual(used - defined, set(), prefix)

    def test_corrected_statements(self):
        self.assertNotIn("amount <= 1000", self.fsd)
        self.assertNotIn("POST https://", self.fsd)
        self.assertIn("4 attempts", self.fsd)
        self.assertIn("**Discarded**", self.fsd)


if __name__ == "__main__":
    unittest.main()
