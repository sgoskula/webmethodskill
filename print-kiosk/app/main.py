import asyncio
import json
import logging
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, db, documents, payments, pricing, printing

log = logging.getLogger("kiosk")
STATIC = Path(__file__).parent / "static"


async def _janitor():
    while True:
        for j in db.expired(config.RETENTION_MINUTES * 60):
            shutil.rmtree(config.UPLOAD_DIR / j["id"], ignore_errors=True)
            db.delete(j["id"])
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_):
    db.init()
    task = asyncio.create_task(_janitor())
    yield
    task.cancel()


app = FastAPI(title="Public Print Kiosk", lifespan=lifespan)


def _public(job: dict) -> dict:
    return {
        "id": job["id"], "status": job["status"], "amount_paise": job["amount_paise"],
        "files": [{"name": f["name"], "pages": f["pages"]} for f in job["files"]],
        "options": job["options"], "printer": job["printer"], "error": job["error"],
    }


def _job_or_404(job_id: str) -> dict:
    job = db.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found or expired")
    return job


@app.get("/api/config")
def get_config():
    return {"price_bw_paise": config.PRICE_BW_PAISE, "price_color_paise": config.PRICE_COLOR_PAISE,
            "provider": config.PAYMENT_PROVIDER, "max_file_mb": config.MAX_FILE_MB}


@app.get("/api/printers")
def printers():
    return printing.list_printers()


@app.post("/api/jobs")
async def create_job(
    files: list[UploadFile] = File(...),
    copies: int = Form(1), color: bool = Form(False), duplex: bool = Form(False),
):
    """Upload -> page count -> server-computed price."""
    if not 1 <= len(files) <= config.MAX_FILES_PER_JOB:
        raise HTTPException(400, f"Upload 1 to {config.MAX_FILES_PER_JOB} files")
    if not 1 <= copies <= 20:
        raise HTTPException(400, "Copies must be between 1 and 20")
    job_id = uuid.uuid4().hex
    jobdir = config.UPLOAD_DIR / job_id
    ingested = []
    try:
        for f in files:
            data = await f.read(config.MAX_FILE_MB * 1024 * 1024 + 1)
            if len(data) > config.MAX_FILE_MB * 1024 * 1024:
                raise HTTPException(413, f"{f.filename} exceeds {config.MAX_FILE_MB} MB")
            ingested.append(await asyncio.to_thread(documents.ingest, f.filename or "file", data, jobdir))
        if sum(d["pages"] for d in ingested) > config.MAX_PAGES_PER_JOB:
            raise HTTPException(400, f"Max {config.MAX_PAGES_PER_JOB} pages per job")
    except documents.BadDocument as e:
        shutil.rmtree(jobdir, ignore_errors=True)
        raise HTTPException(400, str(e))
    except HTTPException:
        shutil.rmtree(jobdir, ignore_errors=True)
        raise
    options = {"copies": copies, "color": color, "duplex": duplex}
    total_pages = sum(d["pages"] for d in ingested)
    amount = pricing.compute(total_pages, copies, color, duplex)
    db.create(job_id, ingested, options, amount)
    return _public(db.get(job_id))


class PayReq(BaseModel):
    printer: str


@app.post("/api/jobs/{job_id}/pay")
def start_payment(job_id: str, req: PayReq):
    """Choose printer, lock it in, create the payment order."""
    job = _job_or_404(job_id)
    if job["status"] not in ("created", "awaiting_payment"):
        raise HTTPException(409, f"Job is {job['status']}")
    printer = next((p for p in printing.list_printers() if p["id"] == req.printer), None)
    if not printer:
        raise HTTPException(400, "Unknown printer")
    if job["options"]["color"] and not printer["color"]:
        raise HTTPException(400, "This printer cannot print in color")
    if job["options"]["duplex"] and not printer["duplex"]:
        raise HTTPException(400, "This printer does not support double-sided")
    order = payments.create_order(job_id, job["amount_paise"])
    db.transition(job_id, ("created", "awaiting_payment"), "awaiting_payment",
                  printer=printer["id"], payment_ref=order["order_id"])
    return order


def _print_job(job_id: str):
    """Runs once per job: the CAS on 'paid' -> 'printing' prevents double printing."""
    if not db.transition(job_id, ("paid",), "printing"):
        return
    job = db.get(job_id)
    try:
        printing.submit(job["printer"], job["files"], job["options"])
        db.transition(job_id, ("printing",), "printed")
    except Exception as e:  # paid but print failed -> operator must refund/reprint
        log.exception("print failed for %s", job_id)
        db.transition(job_id, ("printing",), "failed", error=str(e)[:200])
    shutil.rmtree(config.UPLOAD_DIR / job_id, ignore_errors=True)


def _mark_paid(job_id: str) -> bool:
    ok = db.transition(job_id, ("awaiting_payment",), "paid")
    if ok:
        _print_job(job_id)
    return ok


class VerifyReq(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@app.post("/api/jobs/{job_id}/verify")
def verify(job_id: str, req: VerifyReq):
    job = _job_or_404(job_id)
    if config.PAYMENT_PROVIDER != "razorpay" or req.razorpay_order_id != job["payment_ref"]:
        raise HTTPException(400, "Order mismatch")
    if not payments.verify_checkout(req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature):
        raise HTTPException(400, "Bad signature")
    _mark_paid(job_id)
    return _public(db.get(job_id))


@app.post("/api/webhooks/razorpay")
async def razorpay_webhook(request: Request):
    """Source of truth: covers users who pay but close the browser before the callback."""
    body = await request.body()
    if not payments.verify_webhook(body, request.headers.get("X-Razorpay-Signature", "")):
        raise HTTPException(400, "Bad signature")
    event = json.loads(body)
    if event.get("event") in ("payment.captured", "order.paid"):
        pay = event["payload"]["payment"]["entity"]
        job = db.get(pay.get("notes", {}).get("job_id") or "")
        if job and pay["order_id"] == job["payment_ref"] and pay["amount"] == job["amount_paise"]:
            _mark_paid(job["id"])
    return {"ok": True}


@app.post("/api/jobs/{job_id}/mock-pay")
def mock_pay(job_id: str):
    if config.PAYMENT_PROVIDER != "mock":
        raise HTTPException(404)
    _job_or_404(job_id)
    _mark_paid(job_id)
    return _public(db.get(job_id))


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    return _public(_job_or_404(job_id))


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
