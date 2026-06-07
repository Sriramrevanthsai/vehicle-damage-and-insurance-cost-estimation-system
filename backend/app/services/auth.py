import hashlib
import hmac
import secrets

from fastapi import Header, HTTPException

from app.services.database import db_execute, db_fetchone, get_connection


ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(digest, expected)
    except ValueError:
        return False


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(40)
    with get_connection() as conn:
        db_execute(
            conn,
            "INSERT INTO sessions (token_hash, user_id) VALUES (?, ?)",
            (_hash_token(token), user_id),
        )
    return token


def get_user_by_token(token: str) -> dict | None:
    with get_connection() as conn:
        row = db_fetchone(
            conn,
            """
            SELECT users.id, users.full_name, users.email, users.role, users.created_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (_hash_token(token),),
        )
    return row


def delete_session(token: str) -> None:
    with get_connection() as conn:
        db_execute(conn, "DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_token(authorization)
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired login session.")
    return user


def get_optional_user(authorization: str | None) -> dict | None:
    if not authorization:
        return None
    try:
        return get_user_by_token(_extract_token(authorization))
    except HTTPException:
        return None


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Login required.")
    return authorization.split(" ", 1)[1].strip()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
