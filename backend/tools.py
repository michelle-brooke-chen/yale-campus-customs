"""Data-access layer for the catalogue and inventory.

Plain functions (no agent context) so both the HTTP product routes in main.py and
the agent tools in agent.py can share them. Everything here reads the cleaned
database read-only and never touches the `users` table, following the rules in
output/harness.md.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from models import (
    CategoryCount,
    ProductDetail,
    ProductSummary,
    SizeStock,
    StockReport,
    StockStatus,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK = 5
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _image_url(path: str) -> str:
    # Append the file's last-modified time so browsers always fetch the current
    # image after it's been re-processed (cache busting), instead of a stale copy.
    try:
        version = int((DATA_DIR / path).stat().st_mtime)
    except OSError:
        version = 0
    return f"/media/{path}?v={version}"


def _status(quantity: int) -> StockStatus:
    if quantity == 0:
        return "sold_out"
    if quantity <= LOW_STOCK:
        return "low"
    return "in_stock"


def _summary(row: sqlite3.Row) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        category=row["category"],
        description=row["description"],
        price=row["price"],
        image_url=_image_url(row["image_file_path"]),
        total_stock=row["total_stock"],
    )


def list_products(db_path: Path) -> list[ProductSummary]:
    with _connect(db_path) as con:
        rows = con.execute(
            """
            SELECT c.product_id, c.name, c.category, c.description, c.price,
                   c.image_file_path, COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id
            ORDER BY c.name
            """
        ).fetchall()
    return [_summary(r) for r in rows]


def list_categories(db_path: Path) -> list[CategoryCount]:
    with _connect(db_path) as con:
        rows = con.execute(
            "SELECT category, COUNT(*) AS n FROM catalogue GROUP BY category ORDER BY n DESC"
        ).fetchall()
    return [CategoryCount(category=r["category"], count=r["n"]) for r in rows]


def search_products(
    db_path: Path,
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    limit: int = 12,
) -> list[ProductSummary]:
    """Search by keyword across name, description, and search_tags.

    Matches every whitespace-separated word (AND), so "navy hoodie" narrows
    rather than widens. Optional filters: `category`, `color` (matched against the
    garment's base color and design colors), and `max_price` (<=).

    Results are ranked so in-stock items come first, then cheapest, then by name —
    the agent surfaces things a shopper can actually buy.
    """
    clauses: list[str] = []
    params: list[object] = []
    for word in query.split():
        clauses.append(
            "(LOWER(c.name) LIKE ? OR LOWER(c.description) LIKE ? OR LOWER(c.search_tags) LIKE ?)"
        )
        like = f"%{word.lower()}%"
        params += [like, like, like]
    if category:
        clauses.append("LOWER(c.category) = ?")
        params.append(category.lower())
    if color:
        clauses.append("(LOWER(c.base_color) LIKE ? OR LOWER(c.colors) LIKE ?)")
        like = f"%{color.lower()}%"
        params += [like, like]
    if max_price is not None:
        clauses.append("c.price <= ?")
        params.append(max_price)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect(db_path) as con:
        rows = con.execute(
            f"""
            SELECT c.product_id, c.name, c.category, c.description, c.price,
                   c.image_file_path, COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
            {where}
            GROUP BY c.product_id
            ORDER BY (COALESCE(SUM(i.quantity), 0) = 0), c.price, c.name
            LIMIT ?
            """,
            [*params, limit],
        ).fetchall()
    return [_summary(r) for r in rows]


def get_product(db_path: Path, product_id: str) -> ProductDetail | None:
    with _connect(db_path) as con:
        r = con.execute(
            """
            SELECT product_id, name, category, garment_type, description, colors,
                   base_color, price, image_file_path
            FROM catalogue WHERE product_id = ?
            """,
            (product_id,),
        ).fetchone()
        if r is None:
            return None
        inv_rows = con.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    inv_rows = sorted(inv_rows, key=lambda x: SIZE_ORDER.index(x["size"]))
    inventory = [
        SizeStock(size=x["size"], quantity=x["quantity"], status=_status(x["quantity"]))
        for x in inv_rows
    ]
    return ProductDetail(
        product_id=r["product_id"],
        name=r["name"],
        category=r["category"],
        garment_type=r["garment_type"],
        description=r["description"],
        colors=json.loads(r["colors"]),
        base_color=r["base_color"],
        price=r["price"],
        image_url=_image_url(r["image_file_path"]),
        inventory=inventory,
        total_stock=sum(s.quantity for s in inventory),
    )


def check_stock(db_path: Path, product_id: str, size: str | None = None) -> StockReport | None:
    """Live stock for one product, by size. Optionally narrow to a single size.

    Returns None if the product doesn't exist. If `size` is given but isn't a real
    size for the product, `sizes` comes back empty and `in_stock` is False.
    """
    with _connect(db_path) as con:
        head = con.execute(
            "SELECT product_id, name, price, image_file_path FROM catalogue WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if head is None:
            return None
        inv_rows = con.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    inv_rows = sorted(inv_rows, key=lambda x: SIZE_ORDER.index(x["size"]))
    all_sizes = [
        SizeStock(size=x["size"], quantity=x["quantity"], status=_status(x["quantity"]))
        for x in inv_rows
    ]

    if size is not None:
        want = size.strip().upper()
        scope = [s for s in all_sizes if s.size == want]
    else:
        scope = all_sizes

    return StockReport(
        product_id=head["product_id"],
        name=head["name"],
        price=head["price"],
        image_url=_image_url(head["image_file_path"]),
        total_stock=sum(s.quantity for s in scope),
        in_stock=any(s.quantity > 0 for s in scope),
        sizes=scope,
    )
