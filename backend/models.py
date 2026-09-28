"""Shared Pydantic models and the agent's dependencies.

These types are used by the data-access layer (tools.py), the agent (agent.py),
and the HTTP API (main.py), so the shapes stay consistent everywhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

StockStatus = Literal["in_stock", "low", "sold_out"]


# ---------- catalogue / inventory ----------
class ProductSummary(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    price: float
    image_url: str
    total_stock: int


class SizeStock(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class ProductDetail(ProductSummary):
    garment_type: str
    colors: list[str]
    base_color: str
    inventory: list[SizeStock]


class CategoryCount(BaseModel):
    """One product category and how many items it contains."""

    category: str
    count: int


class StockReport(BaseModel):
    """A focused stock answer for one product, broken down by size.

    Returned by the check_stock tool. `sizes` reflects the requested scope: all
    six sizes normally, or just one when the shopper asked about a specific size.
    `total_stock` and `in_stock` describe that scope so the agent can answer
    "how many mediums?" or "is it in stock?" directly and honestly.
    """

    product_id: str
    name: str
    price: float
    image_url: str
    total_stock: int
    in_stock: bool
    sizes: list[SizeStock]


# ---------- chat API ----------
class ChatProduct(BaseModel):
    """A compact product card the chat widget renders next to a reply."""

    product_id: str
    name: str
    price: float
    image_url: str

    @classmethod
    def from_summary(cls, p: ProductSummary) -> "ChatProduct":
        return cls(product_id=p.product_id, name=p.name, price=p.price, image_url=p.image_url)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message.

    Lets the agent resolve "this"/"it" to the product they're currently viewing.
    """

    path: str | None = None
    product_id: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=50)
    page_context: PageContext | None = None


class ChatResponse(BaseModel):
    reply: str
    products: list[ChatProduct] = Field(default_factory=list)


class ChatHistoryMessage(BaseModel):
    """A saved past message, returned to the widget so it can repaint the thread."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ChatProduct] = Field(default_factory=list)


class ChatHistory(BaseModel):
    messages: list[ChatHistoryMessage] = Field(default_factory=list)


class Customer(BaseModel):
    """The signed-in shopper's identity, as the agent sees it."""

    user_id: int
    name: str
    email: str
    first_name: str | None = None


# ---------- agent dependencies ----------
@dataclass
class AgentDeps:
    """Everything a tool call needs, passed in per request.

    `customer` is the signed-in shopper (or None for a guest). `page_context` is
    where they are on the site, so the agent can resolve "this"/"it". `shown`
    collects the products surfaced during the run so the API can return them as
    cards; tools append to it as they find products.
    """

    db_path: Path
    customer: Customer | None = None
    page_context: PageContext | None = None
    shown: list[ChatProduct] = field(default_factory=list)
