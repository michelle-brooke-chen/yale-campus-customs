"""Account creation, login, and session handling for Campus Customs.

Passwords are hashed with bcrypt (a slow, salted, one-way hash), so the stored
value can never be turned back into the original password. Login state is kept in
a signed, HttpOnly session cookie: the browser can't read or forge it.
"""
import os
import sqlite3
from pathlib import Path

import bcrypt
from fastapi import APIRouter, Cookie, HTTPException, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel, EmailStr, Field

from models import Customer

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("CAMPUS_DB", ROOT / "output" / "campus_customs_clean.db"))

COOKIE_NAME = "cc_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 14  # 14 days
# bcrypt only uses the first 72 bytes of a password; reject longer inputs rather
# than silently truncating them.
MAX_PASSWORD_BYTES = 72

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _secret_key() -> str:
    """Key that signs session cookies. Kept out of the code and out of git."""
    env = os.environ.get("SESSION_SECRET")
    if env:
        return env
    secret_file = Path(__file__).resolve().parent / ".session_secret"
    if secret_file.exists():
        return secret_file.read_text().strip()
    secret = os.urandom(32).hex()
    secret_file.write_text(secret)
    return secret


_serializer = URLSafeTimedSerializer(_secret_key(), salt="cc-session")

# A real bcrypt hash to check against when the email is unknown, so login takes
# about the same time whether or not the account exists.
_DUMMY_HASH = bcrypt.hashpw(b"unused-placeholder", bcrypt.gensalt()).decode()


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


# ---------- request / response models ----------
class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    confirm_password: str

    def cleaned(self) -> "SignupRequest":
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class PublicUser(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    name: str
    email: str
    created_at: str


def _public_user(row: sqlite3.Row) -> PublicUser:
    # password_hash is deliberately never included.
    return PublicUser(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        name=row["name"],
        email=row["email"],
        created_at=row["created_at"],
    )


# ---------- password + session helpers ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), stored.encode())
    except (ValueError, TypeError):
        # Seed accounts use a different (pbkdf2) hash format bcrypt can't read.
        return False


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = _serializer.dumps({"uid": user_id})
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,      # JavaScript can't read it -> safe from XSS theft
        samesite="lax",     # not sent on cross-site requests -> CSRF resistant
        secure=False,       # dev is http://localhost; set True behind HTTPS
        path="/",
    )


def _current_user_id(token: str | None) -> int | None:
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("uid")


def current_customer(token: str | None) -> Customer | None:
    """The signed-in shopper as a Customer (user_id, name, email, first_name), or None.

    Reads only the current user's own row; never exposes other users' data. The
    agent uses this to know who it's talking to; password_hash is never included.
    """
    user_id = _current_user_id(token)
    if user_id is None:
        return None
    with connect() as con:
        row = con.execute(
            "SELECT id, name, email, first_name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return Customer(
        user_id=row["id"], name=row["name"], email=row["email"], first_name=row["first_name"]
    )


# ---------- routes ----------
@router.post("/signup", response_model=PublicUser, status_code=201)
def signup(req: SignupRequest, response: Response) -> PublicUser:
    req = req.cleaned()
    if req.password != req.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match.")
    if len(req.password.encode()) > MAX_PASSWORD_BYTES:
        raise HTTPException(status_code=422, detail="Password is too long.")

    email = req.email.lower()
    name = f"{req.first_name} {req.last_name}"
    with connect() as con:
        exists = con.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="An account with that email already exists.")
        cur = con.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, hash_password(req.password), req.first_name, req.last_name),
        )
        con.commit()
        row = con.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()

    _set_session_cookie(response, row["id"])
    return _public_user(row)


@router.post("/login", response_model=PublicUser)
def login(req: LoginRequest, response: Response) -> PublicUser:
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (req.email.lower(),)).fetchone()

    # Always run a hash check, even when the email is unknown, so the response
    # time doesn't reveal whether an email is registered.
    stored = row["password_hash"] if row else _DUMMY_HASH
    if not verify_password(req.password, stored) or row is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    _set_session_cookie(response, row["id"])
    return _public_user(row)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=PublicUser)
def me(cc_session: str | None = Cookie(default=None)) -> PublicUser:
    user_id = _current_user_id(cc_session)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return _public_user(row)
