from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from .database import get_connection
from .schemas import TransferRequest, TransferResponse


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_accounts() -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT account_number, holder_name, account_type, balance, created_at
            FROM accounts
            ORDER BY id
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_account(account_number: str) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT account_number, holder_name, account_type, balance, created_at
            FROM accounts
            WHERE account_number = ?
            """,
            (account_number,),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Account not found")
        return dict(row)


def list_transactions(account_number: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
        account_row = cursor.fetchone()

        if account_row is None:
            raise HTTPException(status_code=404, detail="Account not found")

        cursor.execute(
            """
            SELECT t.id, a.account_number, t.txn_type, t.amount, t.description, t.created_at
            FROM transactions t
            JOIN accounts a ON a.id = t.account_id
            WHERE t.account_id = ?
            ORDER BY t.id DESC
            LIMIT ?
            """,
            (account_row["id"], limit),
        )

        return [dict(row) for row in cursor.fetchall()]


def transfer_funds(request: TransferRequest) -> TransferResponse:
    if request.from_account_number == request.to_account_number:
        raise HTTPException(status_code=400, detail="Source and destination accounts must differ")

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, account_number, balance FROM accounts WHERE account_number = ?",
            (request.from_account_number,),
        )
        from_account = cursor.fetchone()

        cursor.execute(
            "SELECT id, account_number, balance FROM accounts WHERE account_number = ?",
            (request.to_account_number,),
        )
        to_account = cursor.fetchone()

        if from_account is None or to_account is None:
            raise HTTPException(status_code=404, detail="One or both accounts not found")

        if from_account["balance"] < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        from_new_balance = from_account["balance"] - request.amount
        to_new_balance = to_account["balance"] + request.amount
        now = _utc_now()

        cursor.execute("BEGIN")
        try:
            cursor.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?",
                (from_new_balance, from_account["id"]),
            )
            cursor.execute(
                "UPDATE accounts SET balance = ? WHERE id = ?",
                (to_new_balance, to_account["id"]),
            )
            cursor.execute(
                """
                INSERT INTO transactions(account_id, txn_type, amount, description, created_at)
                VALUES (?, 'DEBIT', ?, ?, ?)
                """,
                (
                    from_account["id"],
                    request.amount,
                    f"Transfer to {request.to_account_number}: {request.description}",
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO transactions(account_id, txn_type, amount, description, created_at)
                VALUES (?, 'CREDIT', ?, ?, ?)
                """,
                (
                    to_account["id"],
                    request.amount,
                    f"Transfer from {request.from_account_number}: {request.description}",
                    now,
                ),
            )
            cursor.execute(
                """
                INSERT INTO transfers(from_account_id, to_account_id, amount, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (from_account["id"], to_account["id"], request.amount, request.description, now),
            )
            transfer_id = cursor.lastrowid
            connection.commit()
        except Exception as exc:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"Transfer failed: {exc}") from exc

    return TransferResponse(
        transfer_id=transfer_id,
        from_account_number=request.from_account_number,
        to_account_number=request.to_account_number,
        amount=request.amount,
        from_balance_after=from_new_balance,
        to_balance_after=to_new_balance,
        created_at=datetime.fromisoformat(now),
    )
