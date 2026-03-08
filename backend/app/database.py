from pathlib import Path
import sqlite3
from datetime import datetime, timezone

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


def init_database() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT UNIQUE NOT NULL,
                holder_name TEXT NOT NULL,
                account_type TEXT NOT NULL CHECK(account_type IN ('SAVINGS', 'CURRENT')),
                balance REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )

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
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_account_id INTEGER NOT NULL,
                to_account_id INTEGER NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(from_account_id) REFERENCES accounts(id),
                FOREIGN KEY(to_account_id) REFERENCES accounts(id)
            )
            """
        )

        cursor.execute("SELECT COUNT(*) AS count FROM accounts")
        account_count = cursor.fetchone()["count"]

        if account_count == 0:
            seed_accounts = [
                ("RBI0001001", "Anish Saranath", "SAVINGS", 248000.00, _utc_now()),
                ("RBI0001002", "Regal Payroll", "CURRENT", 999500.00, _utc_now()),
                ("RBI0001003", "Vendor Services", "CURRENT", 133250.00, _utc_now()),
            ]

            cursor.executemany(
                """
                INSERT INTO accounts(account_number, holder_name, account_type, balance, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                seed_accounts,
            )

            cursor.execute("SELECT id, account_number FROM accounts")
            id_lookup = {row["account_number"]: row["id"] for row in cursor.fetchall()}

            seed_transactions = [
                (id_lookup["RBI0001001"], "CREDIT", 86000, "Salary credit", _utc_now()),
                (id_lookup["RBI0001001"], "DEBIT", 24000, "Rent payment", _utc_now()),
                (id_lookup["RBI0001001"], "DEBIT", 2140, "Electricity bill", _utc_now()),
                (id_lookup["RBI0001002"], "DEBIT", 125000, "Vendor payout", _utc_now()),
                (id_lookup["RBI0001003"], "CREDIT", 125000, "Settlement received", _utc_now()),
            ]

            cursor.executemany(
                """
                INSERT INTO transactions(account_id, txn_type, amount, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                seed_transactions,
            )

            cursor.execute(
                """
                INSERT INTO transfers(from_account_id, to_account_id, amount, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    id_lookup["RBI0001002"],
                    id_lookup["RBI0001003"],
                    125000,
                    "Initial seeded transfer",
                    _utc_now(),
                ),
            )

        connection.commit()
