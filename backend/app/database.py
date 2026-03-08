from datetime import datetime, timezone
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "rbi_bank.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_password_column(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA table_info(accounts)")
    columns = {row["name"] for row in cursor.fetchall()}
    if "password" not in columns:
        cursor.execute("ALTER TABLE accounts ADD COLUMN password INTEGER NOT NULL DEFAULT 0")


def _ensure_email_column(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA table_info(accounts)")
    columns = {row["name"] for row in cursor.fetchall()}
    if "email" not in columns:
        cursor.execute("ALTER TABLE accounts ADD COLUMN email TEXT NOT NULL DEFAULT ''")


def init_database() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT UNIQUE NOT NULL,
                holder_name TEXT NOT NULL,
                password INTEGER NOT NULL DEFAULT 0,
                email TEXT NOT NULL DEFAULT '',
                account_type TEXT NOT NULL CHECK(account_type IN ('SAVINGS', 'CURRENT')),
                balance REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        _ensure_password_column(cursor)
        _ensure_email_column(cursor)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                txn_type TEXT NOT NULL CHECK(txn_type IN ('CREDIT', 'DEBIT')),
                amount REAL NOT NULL CHECK(amount > 0),
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                deposit_type TEXT NOT NULL CHECK(deposit_type IN ('NORMAL', 'FIXED', 'RECURRING')),
                frequency TEXT CHECK(frequency IN ('MONTHLY', 'QUARTERLY', 'ANNUALLY')),
                amount REAL NOT NULL CHECK(amount > 0),
                expected_total REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS card_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                card_type TEXT NOT NULL CHECK(card_type IN ('DEBIT', 'CREDIT', 'BUSINESS')),
                action TEXT NOT NULL CHECK(action IN ('ACTIVATE_OLD', 'APPLY_NEW')),
                card_number TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS loan_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                loan_type TEXT NOT NULL CHECK(loan_type IN ('EDUCATION', 'HOME', 'AUTO')),
                phone TEXT NOT NULL,
                send_forms INTEGER NOT NULL DEFAULT 0,
                email TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                purpose TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consumed_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
            """
        )

        cursor.execute("SELECT COUNT(*) AS count FROM accounts")
        account_count = cursor.fetchone()["count"]
        if account_count == 0:
            cursor.execute(
                """
                INSERT INTO accounts(account_number, holder_name, password, email, account_type, balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("65001", "Sample Customer", 555, "sample.customer@rbi.local", "SAVINGS", 25000.0, _utc_now()),
            )

        connection.commit()
