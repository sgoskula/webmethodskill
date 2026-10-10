"""Payment providers. A job is only printed after confirm() is True.

mock     - dev only; /api/jobs/{id}/mock-pay confirms.
razorpay - Orders API + Checkout (UPI). Confirmed via signature check on the
           client callback AND/OR the signed webhook (payment.captured).
"""
import hashlib
import hmac

import httpx

from . import config


def create_order(job_id: str, amount_paise: int) -> dict:
    if config.PAYMENT_PROVIDER == "mock":
        return {"provider": "mock", "order_id": f"mock_{job_id}", "amount": amount_paise}
    r = httpx.post(
        "https://api.razorpay.com/v1/orders",
        auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET),
        json={"amount": amount_paise, "currency": "INR", "receipt": job_id, "notes": {"job_id": job_id}},
        timeout=15,
    )
    r.raise_for_status()
    return {"provider": "razorpay", "order_id": r.json()["id"], "amount": amount_paise,
            "key_id": config.RAZORPAY_KEY_ID}


def _hmac(secret: str, msg: bytes) -> str:
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def verify_checkout(order_id: str, payment_id: str, signature: str) -> bool:
    expected = _hmac(config.RAZORPAY_KEY_SECRET, f"{order_id}|{payment_id}".encode())
    return hmac.compare_digest(expected, signature)


def verify_webhook(body: bytes, signature: str) -> bool:
    expected = _hmac(config.RAZORPAY_WEBHOOK_SECRET, body)
    return hmac.compare_digest(expected, signature or "")
