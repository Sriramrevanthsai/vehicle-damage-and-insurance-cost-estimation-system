from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.auth import create_session, delete_session, get_current_user, hash_password, verify_password
from app.services.database import db_fetchone, db_insert_returning_id, get_connection

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


@router.post("/register")
def register(payload: RegisterRequest):
    with get_connection() as conn:
        existing = db_fetchone(conn, "SELECT id FROM users WHERE lower(email) = lower(?)", (payload.email,))
        if existing:
            raise HTTPException(status_code=409, detail="An account already exists for this email.")
        role = "admin" if payload.email == "admin@demo.com" else "customer"
        user_id = db_insert_returning_id(
            conn,
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (payload.full_name.strip(), payload.email.lower(), hash_password(payload.password), role),
        )

    token = create_session(user_id)
    return {"token": token, "user": _get_public_user(user_id)}


@router.post("/login")
def login(payload: LoginRequest):
    with get_connection() as conn:
        row = db_fetchone(
            conn,
            "SELECT id, password_hash FROM users WHERE lower(email) = lower(?)",
            (payload.email,),
        )
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_session(row["id"])
    return {"token": token, "user": _get_public_user(row["id"])}


@router.post("/logout")
def logout(user: dict = Depends(get_current_user), authorization: str | None = Header(default=None)):
    token = authorization.split(" ", 1)[1].strip() if authorization else ""
    if token:
        delete_session(token)
    return {"status": "ok", "user": user}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": user}


def _get_public_user(user_id: int) -> dict:
    with get_connection() as conn:
        row = db_fetchone(
            conn,
            "SELECT id, full_name, email, role, created_at FROM users WHERE id = ?",
            (user_id,),
        )
    return row
