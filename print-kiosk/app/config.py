import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "jobs.db"

MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "25"))
MAX_FILES_PER_JOB = int(os.getenv("MAX_FILES_PER_JOB", "5"))
MAX_PAGES_PER_JOB = int(os.getenv("MAX_PAGES_PER_JOB", "200"))

# Pricing in paise (integers avoid float money bugs)
PRICE_BW_PAISE = int(os.getenv("PRICE_BW_PAISE", "200"))        # Rs 2 / page
PRICE_COLOR_PAISE = int(os.getenv("PRICE_COLOR_PAISE", "1000"))  # Rs 10 / page
DUPLEX_DISCOUNT_PCT = int(os.getenv("DUPLEX_DISCOUNT_PCT", "0"))

# "mock" (simulated payment, for dev) or "razorpay"
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "mock")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

# "cups" (uses `lp`) or "mock" (logs only). Auto: cups if `lp` exists.
PRINT_BACKEND = os.getenv("PRINT_BACKEND", "auto")
# Used when CUPS is absent / for mock backend: "id:Name:color(1|0):duplex(1|0)" comma separated
MOCK_PRINTERS = os.getenv("MOCK_PRINTERS", "hp-bw:HP LaserJet (B/W):0:1,epson-color:Epson EcoTank (Color):1:0")

# Delete uploaded files this long after job completion/expiry
RETENTION_MINUTES = int(os.getenv("RETENTION_MINUTES", "30"))
