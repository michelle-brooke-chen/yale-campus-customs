# Campus Customs

A Yale apparel shop with a chat assistant. A React + Vite website talks to a FastAPI backend, where a PydanticAI agent (Claude via Portkey) answers shopping questions from the product database and shows matching items as product cards.

## Project layout

| Path | What's there |
|---|---|
| `frontend/` | React + Vite + TypeScript website |
| `backend/` | FastAPI app (`main.py`), the agent (`agent.py`, `tools.py`, `models.py`, `prompts/prompt.md`), accounts, chat history, and the audit logger |
| `data/` | Original database and product photos |
| `output/` | Cleaned database, reports, and the agent's audit trail |
| `requirements.txt` | Python packages for the backend |
| `AI_prompts.md` | Every prompt used during the homework, by problem |

## Setup

**Backend** (Python 3.10+). Create a venv in `backend/` and install the packages from the hw4 folder:

```bash
python3 -m venv backend/.venv-mac
backend/.venv-mac/bin/pip install -r requirements.txt
```

On Windows, use `backend\.venv` and `backend\.venv\Scripts\pip install -r requirements.txt`.

Copy `backend/.env.example` to `backend/.env` and set `PORTKEY_API_KEY` (plus `PORTKEY_BASE_URL` and `CHATBOT_MODEL` if your course gave different values).

**Data** (not in the repo). The database and product photos are kept out of version control. Add the course's `data/campus_customs.db` and photos in `data/products/`, then build the clean copy the app runs on:

```bash
backend/.venv-mac/bin/python output/clean_db.py
```

`output/normalize_images.py` puts every product photo on a white background (it needs `pip install rembg onnxruntime pillow numpy`).

**Frontend** (Node 20+):

```bash
npm --prefix frontend install
```

## Run

Start the backend from the `backend/` folder:

```bash
cd backend && .venv-mac/bin/python -m uvicorn main:app --reload --port 8000
```

Then start the frontend in another terminal and open http://localhost:5173:

```bash
npm --prefix frontend run dev
```

Vite forwards `/api` and `/media` requests to the backend on port 8000. Without an API key the site still works, and the chat replies with a friendly fallback message.

## Reports

| File | Contents |
|---|---|
| `output/harness.md` | Model fields, tools, safety rules, and specs |
| `output/usability.md` | Usability improvements (Problem 9) |
| `output/design.md` | Design changes and customer retention (Problem 10) |
| `output/app_check.html` | Live site test with screenshots in `output/app_check_images/` (Problem 11) |
| `output/audit_trail.json` | Append-only log of agent-loop activity (Problem 12) |
