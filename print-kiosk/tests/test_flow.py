import io, os, tempfile
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["PAYMENT_PROVIDER"] = "mock"
os.environ["PRINT_BACKEND"] = "mock"

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from app.main import app


def pdf(pages):
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=595, height=842)
    b = io.BytesIO(); w.write(b); return b.getvalue()


def test_full_flow_prices_pays_and_prints_once():
    with TestClient(app) as c:
        j = c.post("/api/jobs", files=[("files", ("a.pdf", pdf(3), "application/pdf"))],
                   data={"copies": 2, "color": "false", "duplex": "false"}).json()
        assert j["amount_paise"] == 3 * 2 * 200
        # B/W-only printer can't do color; color job on it is rejected
        j2 = c.post("/api/jobs", files=[("files", ("a.pdf", pdf(1), "application/pdf"))], data={"color": "true"}).json()
        assert c.post(f"/api/jobs/{j2['id']}/pay", json={"printer": "hp-bw"}).status_code == 400
        assert c.post(f"/api/jobs/{j['id']}/pay", json={"printer": "hp-bw"}).status_code == 200
        assert c.post(f"/api/jobs/{j['id']}/mock-pay").json()["status"] == "printed"
        assert c.post(f"/api/jobs/{j['id']}/mock-pay").json()["status"] == "printed"  # idempotent


def test_unpaid_job_never_prints_and_bad_files_rejected():
    with TestClient(app) as c:
        j = c.post("/api/jobs", files=[("files", ("a.pdf", pdf(1), "application/pdf"))]).json()
        assert c.get(f"/api/jobs/{j['id']}").json()["status"] == "created"
        assert c.post("/api/jobs", files=[("files", ("x.exe", b"MZ", "application/octet-stream"))]).status_code == 400
        assert c.post("/api/jobs", files=[("files", ("fake.pdf", b"not a pdf", "application/pdf"))]).status_code == 400
