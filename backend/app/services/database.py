import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "insurance_app.db"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
IS_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


def init_db() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with get_connection() as conn:
        if IS_POSTGRES:
            _init_postgres(conn)
        else:
            _init_sqlite(conn)


@contextmanager
def get_connection():
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        DATA_DIR.mkdir(exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def db_fetchone(conn, query: str, params: tuple = ()):
    cursor = _execute(conn, query, params)
    return row_to_dict(cursor.fetchone())


def db_fetchall(conn, query: str, params: tuple = ()) -> list[dict]:
    cursor = _execute(conn, query, params)
    return [row_to_dict(row) for row in cursor.fetchall()]


def db_execute(conn, query: str, params: tuple = ()):
    return _execute(conn, query, params)


def db_insert_returning_id(conn, query: str, params: tuple = ()) -> int:
    if IS_POSTGRES:
        cursor = _execute(conn, f"{query} RETURNING id", params)
        return int(cursor.fetchone()["id"])
    cursor = _execute(conn, query, params)
    return int(cursor.lastrowid)


def row_to_dict(row) -> dict | None:
    return dict(row) if row else None


def json_dump(value) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True)


def json_load(value: str):
    return json.loads(value) if value else None


def _execute(conn, query: str, params: tuple = ()):
    if IS_POSTGRES:
        query = query.replace("?", "%s")
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    return conn.execute(query, params)


def _init_sqlite(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_number TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            vehicle_segment TEXT NOT NULL,
            workshop_type TEXT NOT NULL,
            car_model TEXT NOT NULL DEFAULT 'maruti_swift',
            damage_category TEXT NOT NULL DEFAULT 'auto',
            status TEXT NOT NULL DEFAULT 'AI Assessed',
            severity TEXT NOT NULL,
            severity_score REAL NOT NULL,
            estimated_cost_min INTEGER NOT NULL,
            estimated_cost_max INTEGER NOT NULL,
            estimated_cost_range TEXT NOT NULL,
            damage_detected INTEGER NOT NULL,
            num_damages INTEGER NOT NULL,
            damage_area_ratio REAL NOT NULL,
            damage_types TEXT NOT NULL,
            detections TEXT NOT NULL,
            preprocessing TEXT NOT NULL,
            cost_breakdown TEXT NOT NULL,
            model TEXT NOT NULL,
            annotated_image TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    _ensure_sqlite_column(conn, "claims", "car_model", "TEXT NOT NULL DEFAULT 'maruti_swift'")
    _ensure_sqlite_column(conn, "claims", "damage_category", "TEXT NOT NULL DEFAULT 'auto'")


def _init_postgres(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS claims (
                id SERIAL PRIMARY KEY,
                claim_number TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                file_name TEXT NOT NULL,
                vehicle_segment TEXT NOT NULL,
                workshop_type TEXT NOT NULL,
                car_model TEXT NOT NULL DEFAULT 'maruti_swift',
                damage_category TEXT NOT NULL DEFAULT 'auto',
                status TEXT NOT NULL DEFAULT 'AI Assessed',
                severity TEXT NOT NULL,
                severity_score DOUBLE PRECISION NOT NULL,
                estimated_cost_min INTEGER NOT NULL,
                estimated_cost_max INTEGER NOT NULL,
                estimated_cost_range TEXT NOT NULL,
                damage_detected INTEGER NOT NULL,
                num_damages INTEGER NOT NULL,
                damage_area_ratio DOUBLE PRECISION NOT NULL,
                damage_types TEXT NOT NULL,
                detections TEXT NOT NULL,
                preprocessing TEXT NOT NULL,
                cost_breakdown TEXT NOT NULL,
                model TEXT NOT NULL,
                annotated_image TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_user_id ON claims(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_created_at ON claims(created_at DESC)")


def _ensure_sqlite_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
