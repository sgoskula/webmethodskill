"""Validate uploads and count pages. Non-PDF office files are converted with LibreOffice."""
import io
import subprocess
import uuid
from pathlib import Path

from pypdf import PdfReader
from PIL import Image

OFFICE = {".doc", ".docx", ".odt", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".rtf"}
IMAGES = {".jpg", ".jpeg", ".png"}
ALLOWED = OFFICE | IMAGES | {".pdf"}


class BadDocument(ValueError):
    pass


def _sniff_ok(ext: str, head: bytes) -> bool:
    if ext == ".pdf":
        return head.startswith(b"%PDF")
    if ext in (".jpg", ".jpeg"):
        return head.startswith(b"\xff\xd8")
    if ext == ".png":
        return head.startswith(b"\x89PNG")
    return True  # office/text: validated by conversion


def image_to_pdf(src: Path, dst: Path):
    img = Image.open(src).convert("RGB")
    img.save(dst, "PDF", resolution=150.0)


def office_to_pdf(src: Path, outdir: Path) -> Path:
    try:
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(src)],
            check=True, timeout=90, capture_output=True,
            env={"HOME": str(outdir), "PATH": "/usr/bin:/bin:/usr/local/bin"},
        )
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        raise BadDocument("Could not convert this document; please upload a PDF") from e
    out = outdir / (src.stem + ".pdf")
    if not out.exists():
        raise BadDocument("Could not convert this document; please upload a PDF")
    return out


def ingest(name: str, data: bytes, jobdir: Path) -> dict:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED:
        raise BadDocument(f"{ext or 'this file type'} is not supported")
    if not _sniff_ok(ext, data[:8]):
        raise BadDocument(f"{name} does not look like a valid {ext} file")
    jobdir.mkdir(parents=True, exist_ok=True)
    stem = uuid.uuid4().hex[:8]          # never trust user filenames on disk
    raw = jobdir / f"{stem}{ext}"
    raw.write_bytes(data)
    pdf = jobdir / f"{stem}.pdf"
    if ext == ".pdf":
        pdf = raw
    elif ext in IMAGES:
        try:
            image_to_pdf(raw, pdf)
        except Exception as e:
            raise BadDocument(f"{name} is not a readable image") from e
    else:
        conv = office_to_pdf(raw, jobdir)
        conv.rename(pdf)
    try:
        reader = PdfReader(str(pdf))
        if reader.is_encrypted:
            raise BadDocument(f"{name} is password protected")
        pages = len(reader.pages)
    except BadDocument:
        raise
    except Exception as e:
        raise BadDocument(f"{name} is not a readable document") from e
    if pages < 1:
        raise BadDocument(f"{name} has no pages")
    return {"name": Path(name).name[:100], "path": str(pdf), "pages": pages}
