import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, ".github", "skills", "webmethods-fsd", "scripts")
SAMPLE = os.path.join(ROOT, "sample", "OrderProcessing")
sys.path.insert(0, SCRIPTS)

import check_mermaid  # noqa: E402


class ExtractorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = cls.tmp.name
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "wm_extract.py"), "--out", cls.out, SAMPLE],
                       check=True, capture_output=True)
        with open(os.path.join(cls.out, "inventory.json")) as f:
            cls.inv = json.load(f)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def service_md(self, name):
        with open(os.path.join(self.out, "services", name.replace(":", "__") + ".md")) as f:
            return f.read()

    def flags(self, name):
        return " | ".join(self.inv["semantic_flags"].get(name, []))

    def test_inventory(self):
        self.assertEqual(self.inv["entry_points"], ["order.process:submitOrder"])
        self.assertIn("order.process:submitOrder", self.inv["triggered"])
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

    def test_no_false_positive_unused_values(self):
        f = self.flags("order.process:submitOrder")
        for used in ("orderId", "customerId", "amount", "url"):
            self.assertNotIn(f"`{used}` is set but never used", f)
        self.assertNotIn("order.jdbc:insertOrder", self.inv["semantic_flags"])

    def test_semantic_flags_java_and_trigger(self):
        self.assertIn("floating-point", self.flags("order.process:validateOrder"))
        self.assertIn("ISRuntimeException", self.flags("order.triggers:orderTrigger"))


class MermaidLintTest(unittest.TestCase):
    def test_detects_common_errors(self):
        _, errs = check_mermaid.lint_block("sequenceDiagram\n  alt x\n  A->>B: one; two\n")
        self.assertTrue(any("';'" in e for e in errs))
        self.assertTrue(any("missing 'end'" in e for e in errs))
        _, errs = check_mermaid.lint_block('flowchart TD\n  A["unclosed] --> B\n')
        self.assertTrue(errs)

    def test_accepts_multiline_class_diagram(self):
        _, errs = check_mermaid.lint_block("classDiagram\n  class A {\n    +string x\n  }\n")
        self.assertEqual(errs, [])

    def test_generated_fsd_diagrams_are_valid(self):
        self.assertEqual(check_mermaid.main([os.path.join(ROOT, "docs", "FSD.md")]), 0)


class FsdContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "docs", "FSD.md")) as f:
            cls.fsd = f.read()

    def test_has_reimplementation_section_and_tests(self):
        self.assertIn("## 11. Re-implementation Notes", self.fsd)
        self.assertIn("**11.5 Acceptance test cases**", self.fsd)

    def test_every_node_is_covered(self):
        for name in ("order.process:submitOrder", "order.process:validateOrder", "order.jdbc:insertOrder",
                     "order.triggers:orderTrigger", "order.docs:OrderDoc"):
            self.assertIn(f"`{name}`", self.fsd)

    def test_corrected_statements(self):
        self.assertNotIn("amount <= 1000", self.fsd)
        self.assertNotIn("POST https://", self.fsd)
        self.assertIn("4 attempts", self.fsd)
        self.assertIn("**Discarded**", self.fsd)


if __name__ == "__main__":
    unittest.main()
