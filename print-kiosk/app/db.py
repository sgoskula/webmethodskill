import json
import sqlite3
import time
from contextlib import contextmanager

from . import config


def init():
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,          -- created|awaiting_payment|paid|printing|printed|failed
                files TEXT NOT NULL,           -- json [{name,path,pages}]
                options TEXT NOT NULL,         -- json
                amount_paise INTEGER NOT NULL,
                printer TEXT,
                payment_ref TEXT,
                error TEXT,
                created REAL NOT NULL,
                updated REAL NOT NULL)"""
        )


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def create(job_id, files, options, amount):
    now = time.time()
    with conn() as c:
        c.execute(
            "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
            (job_id, "created", json.dumps(files), json.dumps(options), amount, None, None, None, now, now),
        )


def get(job_id):
    with conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["files"] = json.loads(d["files"])
    d["options"] = json.loads(d["options"])
    return d


def transition(job_id, from_states, to_state, **fields):
    """Atomic compare-and-set. Returns True if this caller won the transition
    (makes payment confirmation + printing idempotent across webhook/verify races)."""
    sets = ["status=?", "updated=?"] + [f"{k}=?" for k in fields]
    args = [to_state, time.time(), *fields.values(), job_id, *from_states]
    q = f"UPDATE jobs SET {', '.join(sets)} WHERE id=? AND status IN ({','.join('?' * len(from_states))})"
    with conn() as c:
        return c.execute(q, args).rowcount == 1


def expired(older_than_s):
    with conn() as c:
        rows = c.execute("SELECT * FROM jobs WHERE updated<?", (time.time() - older_than_s,)).fetchall()
    return [dict(r) | {"files": json.loads(r["files"])} for r in rows]


def delete(job_id):
    with conn() as c:
        c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
