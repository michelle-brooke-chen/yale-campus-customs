"""Campus Customs API.

The FastAPI application, run with Uvicorn from the backend/ folder:
    uvicorn main:app --reload --port 8000
(using this project's venv, e.g. .venv/Scripts/python -m uvicorn main:app --reload --port 8000)

It serves the product catalogue, the product photos, the auth routes (see
auth.py), and the chat route that drives the PydanticAI shop agent (see agent.py).
"""
from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

import audit
import history
import tools
from agent import AgentNotConfigured, run_agent
from auth import current_customer
from auth import router as auth_router
from models import (
    AgentDeps,
    ChatHistory,
    ChatProduct,
    ChatRequest,
    ChatResponse,
    ProductDetail,
    ProductSummary,
)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("CAMPUS_DB", ROOT / "output" / "campus_customs_clean.db"))
DATA_DIR = ROOT / "data"

logger = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")
app.include_router(auth_router)


# ---------- products ----------
@app.get("/api/products", response_model=list[ProductSummary])
def list_products() -> list[ProductSummary]:
    return tools.list_products(DB_PATH)


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> ProductDetail:
    product = tools.get_product(DB_PATH, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------- chat ----------
FALLBACK_REPLY = (
    "Thanks for your message! Our Bulldog shopping assistant isn’t available right "
    "now, but you can browse the full collection on the Products page."
)

# Lightweight per-client rate limit. Each agent turn is a real (paid) model call,
# so this protects against runaway cost and abuse while staying invisible in normal use.
RATE_LIMIT_MAX = 15          # messages allowed...
RATE_LIMIT_WINDOW = 60.0     # ...per this many seconds
RATE_LIMIT_REPLY = (
    "You’re sending messages quickly! 🐶 Give me a few seconds to catch up, then try again."
)
_recent_calls: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(key: str) -> bool:
    now = time.monotonic()
    hits = _recent_calls[key]
    while hits and now - hits[0] > RATE_LIMIT_WINDOW:
        hits.popleft()
    if len(hits) >= RATE_LIMIT_MAX:
        return True
    hits.append(now)
    return False


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)
) -> ChatResponse:
    # Identify the signed-in shopper (if any). The agent sees their name and email
    # for personalization, plus the page they're on to resolve "this"/"it".
    customer = current_customer(cc_session)

    # Rate-limit per shopper (by account when signed in, else by client address).
    client_host = request.client.host if request.client else "anon"
    if _rate_limited(f"user:{customer.user_id}" if customer else f"ip:{client_host}"):
        audit.record(
            audit.new_run_id(),
            "run_blocked",
            shopper=f"user:{customer.user_id}" if customer else "guest",
            stop_reason="rate_limited",
        )
        return ChatResponse(reply=RATE_LIMIT_REPLY)

    deps = AgentDeps(db_path=DB_PATH, customer=customer, page_context=req.page_context)

    # For signed-in shoppers, memory is the database (source of truth); guests use
    # the ephemeral history the browser sends.
    turns = history.load_recent_turns(DB_PATH, customer.user_id) if customer else req.history

    try:
        reply = await run_agent(req.message, turns, deps)
    except AgentNotConfigured:
        # No API key configured yet — degrade gracefully instead of erroring.
        return ChatResponse(reply=FALLBACK_REPLY)
    except Exception:
        logger.exception("Agent run failed")
        raise HTTPException(status_code=502, detail="The shop assistant had a problem. Please try again.")

    products: list[ChatProduct] = deps.shown
    if customer:
        # Persist this turn so it's reloaded when the shopper returns.
        history.save_message(DB_PATH, customer.user_id, "user", req.message)
        history.save_message(DB_PATH, customer.user_id, "assistant", reply, products)
    return ChatResponse(reply=reply, products=products)


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(cc_session: str | None = Cookie(default=None)) -> ChatHistory:
    """The signed-in shopper's saved conversation (empty for guests)."""
    customer = current_customer(cc_session)
    if customer is None:
        return ChatHistory(messages=[])
    return ChatHistory(messages=history.load_history_messages(DB_PATH, customer.user_id))


# /media/products/<file>.jpg -> data/products/<file>.jpg
# Only the photo folder is served, never data/ itself (it holds the raw database).
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="media")
