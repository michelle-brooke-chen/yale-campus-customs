"""Append-only audit trail of agent-loop activity.

Each chat turn is logged to output/audit_trail.json while it runs: the run start,
every model step with its stop reason, every tool call with short args and a short
result, and how the run ended. The file is always a valid JSON array. New entries
are spliced in before the closing bracket, so earlier entries are never rewritten.

Shoppers are logged as "user:<id>" or "guest", never by name or email, and text
previews are trimmed and scrubbed of emails and long numbers.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from models import CategoryCount, ProductDetail, ProductSummary, StockReport

AUDIT_PATH = Path(
    os.environ.get(
        "AUDIT_TRAIL", Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
    )
)
MAX_TEXT = 160

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_LONG_NUMBER = re.compile(r"\b(?:\d[ -]?){12,}\b")

_lock = threading.Lock()
logger = logging.getLogger("campus_customs.audit")


def new_run_id() -> str:
    return uuid.uuid4().hex[:8]


def short(value: object, limit: int = MAX_TEXT) -> str:
    """One-line, trimmed, scrubbed text for a log field."""
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = _LONG_NUMBER.sub("[number]", _EMAIL.sub("[email]", " ".join(text.split())))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summarize(result: object) -> str:
    """A short, human-readable summary of what a tool returned."""
    if result is None:
        return "not found"
    if isinstance(result, StockReport):
        sizes = ", ".join(f"{s.size} {s.quantity}" for s in result.sizes) or "no such size"
        return short(f"{result.name} ${result.price:.2f}: {sizes} (total {result.total_stock})")
    if isinstance(result, ProductDetail):
        return short(f"{result.name} ${result.price:.2f}, {result.total_stock} in stock")
    if isinstance(result, list) and all(isinstance(r, ProductSummary) for r in result):
        names = "; ".join(f"{p.name} ${p.price:.0f}" for p in result)
        return short(f"{len(result)} products: {names}" if result else "0 products")
    if isinstance(result, list) and all(isinstance(r, CategoryCount) for r in result):
        return short(f"{len(result)} categories: " + ", ".join(f"{c.category} {c.count}" for c in result))
    return short(result)


def record(run_id: str, event: str, **fields: object) -> None:
    """Append one event. Logging problems never break the chat."""
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "run_id": run_id,
        "event": event,
        **{k: v for k, v in fields.items() if v is not None},
    }
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _lock:
        try:
            _append(line)
        except (OSError, ValueError):
            logger.exception("Could not write the audit trail")


def _append(line: str) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
        AUDIT_PATH.write_text(f"[\n{line}\n]\n", encoding="utf-8")
        return

    with AUDIT_PATH.open("r+b") as f:
        # Walk back past trailing whitespace to the closing "]"...
        pos = f.seek(0, os.SEEK_END)
        while True:
            pos -= 1
            if pos < 0:
                raise ValueError("audit trail is not a JSON array")
            f.seek(pos)
            ch = f.read(1)
            if ch == b"]":
                break
            if not ch.isspace():
                raise ValueError("audit trail is not a JSON array")
        # ...then past whitespace to the last entry (or the opening "[").
        while True:
            pos -= 1
            f.seek(pos)
            ch = f.read(1)
            if not ch.isspace():
                break
        separator = "" if ch == b"[" else ","
        f.seek(pos + 1)
        f.truncate()
        f.write(f"{separator}\n{line}\n]\n".encode("utf-8"))
