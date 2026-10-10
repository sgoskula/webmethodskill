import logging
import shutil
import subprocess

from . import config

log = logging.getLogger("print")


def _backend():
    if config.PRINT_BACKEND == "auto":
        return "cups" if shutil.which("lp") else "mock"
    return config.PRINT_BACKEND


def list_printers() -> list[dict]:
    """[{id,name,color,duplex}]. For CUPS, color/duplex come from `lpoptions -p X -l`."""
    if _backend() == "mock":
        out = []
        for spec in config.MOCK_PRINTERS.split(","):
            pid, name, col, dup = spec.split(":")
            out.append({"id": pid, "name": name, "color": col == "1", "duplex": dup == "1"})
        return out
    res = subprocess.run(["lpstat", "-e"], capture_output=True, text=True)
    printers = []
    for pid in res.stdout.split():
        opts = subprocess.run(["lpoptions", "-p", pid, "-l"], capture_output=True, text=True).stdout
        printers.append({
            "id": pid, "name": pid.replace("_", " "),
            "color": "ColorModel" in opts or "ColorMode" in opts,
            "duplex": "Duplex" in opts,
        })
    return printers


def submit(printer: str, files: list[dict], options: dict) -> None:
    """Raises RuntimeError on failure. `printer` must already be validated against list_printers()."""
    for f in files:
        if _backend() == "mock":
            log.info("MOCK PRINT %s x%s on %s opts=%s", f["name"], options["copies"], printer, options)
            continue
        cmd = ["lp", "-d", printer, "-n", str(options["copies"])]
        cmd += ["-o", "sides=two-sided-long-edge" if options["duplex"] else "sides=one-sided"]
        cmd += ["-o", "print-color-mode=color" if options["color"] else "print-color-mode=monochrome"]
        cmd += ["--", f["path"]]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or "lp failed")
