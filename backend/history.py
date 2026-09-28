"""Persistent chat history for signed-in shoppers.

Saved in the existing `chat_messages` table of the cleaned database:
    id, user_id, role, content, products_json, created_at
so a returning shopper's conversation is reloaded. Guests are not persisted.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from models import ChatHistoryMessage, ChatProduct, ChatTurn

# How much prior conversation to feed the agent (turns) and to show the widget.
AGENT_TURN_LIMIT = 20
DISPLAY_LIMIT = 50


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def save_message(
    db_path: Path,
    user_id: int,
    role: str,
    content: str,
    products: list[ChatProduct] | None = None,
) -> None:
    """Append one message. `products` (assistant cards) are stored as JSON."""
    products_json = (
        json.dumps([p.model_dump() for p in products]) if products else None
    )
    with _connect(db_path) as con:
        con.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )
        con.commit()


def load_recent_turns(db_path: Path, user_id: int, limit: int = AGENT_TURN_LIMIT) -> list[ChatTurn]:
    """Recent turns (text only) to give the agent as conversation memory."""
    with _connect(db_path) as con:
        rows = con.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE user_id = ? ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    rows.reverse()  # back to chronological order
    return [ChatTurn(role=r["role"], content=r["content"]) for r in rows]


def load_history_messages(
    db_path: Path, user_id: int, limit: int = DISPLAY_LIMIT
) -> list[ChatHistoryMessage]:
    """Recent messages with their product cards, to repaint the widget on return."""
    with _connect(db_path) as con:
        rows = con.execute(
            """
            SELECT role, content, products_json FROM chat_messages
            WHERE user_id = ? ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    rows.reverse()
    messages: list[ChatHistoryMessage] = []
    for r in rows:
        products = (
            [ChatProduct(**p) for p in json.loads(r["products_json"])]
            if r["products_json"]
            else []
        )
        messages.append(
            ChatHistoryMessage(role=r["role"], content=r["content"], products=products)
        )
    return messages
