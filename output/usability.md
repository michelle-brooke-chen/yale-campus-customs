# Campus Customs — Usability Improvements (Problem 9)

Four usability improvements: two on the front end and two on the agent/backend. Each note says what changed, where, and why it helps a Campus Customs shopper or the business.

---

## Front end

### FE1 — Search, category filter, and sort on the Products page
**What:** The Products page ([frontend/src/pages/Products.tsx](../frontend/src/pages/Products.tsx)) now has a filter bar: a keyword search (matches name + description), a category dropdown (t-shirt, hoodie, fleece jacket, …), and a sort control (name, price low→high, price high→low). A live "N items of 102" count shows how much matched, with a friendly empty state when nothing does. Filtering is instant (client-side over the already-loaded catalogue).

**Why it helps:** The catalogue has 102 products. Scrolling one long alphabetical grid makes it hard to find, say, a hoodie under a budget. Search + filter + sort lets a shopper zero in on what they want in seconds. For the business, faster "find what I want" means fewer bounces and more completed purchases, and price sorting surfaces budget-friendly options for price-sensitive shoppers.

### FE2 — Availability badges on product cards
**What:** Each product card ([frontend/src/components/ProductCard.tsx](../frontend/src/components/ProductCard.tsx)) shows an at-a-glance stock badge computed from `total_stock`: green **In stock**, amber **Low stock** (≤15 total), or gray **Sold out** (0). The badge sits on the product image on both the catalogue grid and the chat-results panel.

**Why it helps:** Shoppers can see availability before clicking into a product, so they don't invest attention in something they can't buy — and an amber "Low stock" nudge creates gentle urgency. For the business, steering attention toward in-stock (and away from sold-out) items reduces disappointment and lost sales, and the scarcity cue can lift conversion on low-stock pieces.

---

## Agent / backend

### BE1 — Smarter, stock-aware product search
**What:** The `search_products` tool ([backend/tools.py](../backend/tools.py), exposed to the agent in [backend/agent.py](../backend/agent.py)) gained two optional filters — `color` (matches base color and design colors) and `max_price` — and now **ranks results in-stock-first, then cheapest, then by name**. The system prompt tells the agent it can combine these for precise questions and to recommend from the top.

**Why it helps:** Shoppers ask precise, natural questions like "gray hoodies under $60." The agent can now answer them directly instead of listing everything and making the shopper filter by hand. Ranking in-stock items first means the assistant recommends things a shopper can actually buy right now — better for the shopper (no dead ends) and for the business (it promotes sellable, and cheaper-first, inventory). Verified live: "gray hoodies under $70" returned only matching gray hoodies, cheapest first.

### BE2 — Chat rate limiting (cost & abuse protection)
**What:** The `/api/chat` route ([backend/main.py](../backend/main.py)) enforces a lightweight per-client limit (15 messages / 60 seconds, keyed by account when signed in, else client address) using an in-memory sliding window. Over the limit, it returns a friendly "give me a few seconds" reply **without** calling the model, so the UX degrades gracefully rather than erroring.

**Why it helps:** Every agent turn is a real, paid model call through Portkey. Without a limit, an accidental loop, an impatient double-click, or a bad actor could rack up cost and slow the service for everyone. The cap protects the business's budget and keeps the assistant responsive, while the limit is high enough that a normal shopper never notices it. The threshold is unit-tested (exactly 15 of 20 rapid calls allowed).

---

## How each was verified
- **FE1:** searching "dad" → 3 items; category "fleece jacket" → 7 items; price-low sort → $32 items first.
- **FE2:** cards render "In stock" badges on the grid and results panel.
- **BE1:** unit-tested color + max_price filtering and in-stock-first ordering; confirmed live via the chat ("gray hoodies under $70").
- **BE2:** unit-tested that the limiter allows exactly 15 of 20 rapid calls and blocks the rest before any model call.
