# Public Print Kiosk

Scan QR → upload documents → see price → pay via UPI → pick printer → prints.

## Run (dev, no real money, no real printer)
    pip install -r requirements.txt
    uvicorn app.main:app --port 8000     # mock payment + mock printing
    python -m pytest
    python -m app.qr "https://print.example.com/" poster.png   # QR to stick on the wall

## Production
- Run on a machine/Raspberry Pi connected to the printers via **CUPS** (`lp` is used automatically; printers auto-listed).
- Put behind HTTPS (Caddy/nginx/Cloudflare Tunnel) — required for UPI checkout on phones.
- Set `PAYMENT_PROVIDER=razorpay`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`.
  Add webhook `https://<host>/api/webhooks/razorpay` for `payment.captured`.
- Pricing/limits via env: `PRICE_BW_PAISE`, `PRICE_COLOR_PAISE`, `DUPLEX_DISCOUNT_PCT`, `MAX_FILE_MB`, `MAX_PAGES_PER_JOB`.
- Docx/pptx/xlsx need LibreOffice (`soffice`) on the host.

## Design notes
- Price is computed server-side from the real page count; the client never sends an amount.
- Printing only happens after a verified payment (checkout signature or signed webhook); an atomic
  state transition guarantees one print even if both arrive.
- Files are stored under random names and deleted after printing / `RETENTION_MINUTES`.
- A plain `upi://pay` link can't be auto-verified, hence a gateway (Razorpay) is used. Other gateways
  (PhonePe, Cashfree) can be added in `payments.py`.

## Not built yet (suggested next)
Per-kiosk QR (`?k=lobby-1` → fixed printer), page-range selection, rate limiting, admin view for
failed-print refunds, printer paper/ink status.
