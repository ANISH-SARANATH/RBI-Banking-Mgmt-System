from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
import os
import random
import smtplib
from typing import Any

from fastapi import HTTPException

from .database import get_connection
from .schemas import (
    AdminLoginResponse,
    CardRequest,
    CardResponse,
    ContactInfo,
    CustomerLoginOTPRequest,
    CustomerLoginVerifyRequest,
    CustomerSignupRequest,
    CustomerSignupResponse,
    CustomerSummary,
    DepositRequest,
    LoanRequest,
    LoanResponse,
    OTPDispatchResponse,
    OperationResponse,
)

ADMIN_NAME = "Anish"
ADMIN_PASSWORD = "1939"
MINIMUM_BALANCE = 1000.0
OTP_TTL_SECONDS = 300
OTP_PURPOSE_LOGIN = "LOGIN"

LOAN_FORM_URLS = {
    "EDUCATION": "https://sites.google.com/view/regalbankofindia-educationloan/home",
    "HOME": "https://sites.google.com/view/regalbankofindia-homeloan/home",
    "AUTO": "https://sites.google.com/view/regalbankofindia-autoloan/home",
}

LOAN_REQUIREMENTS = [
    "Application form with photograph",
    "Identity and Residence proof",
    "Last 6 months bank statements",
    "Processing fee cheque",
    "Educational Qualifications Certificate",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_valid_email(email: str) -> bool:
    parts = email.strip().split("@")
    return len(parts) == 2 and bool(parts[0]) and "." in parts[1]


def _mask_email(email: str) -> str:
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f"{masked_local}@{domain}"


def _generate_otp() -> str:
    digits = "0123456789"
    return "".join(random.choice(digits) for _ in range(6))


def _send_otp_email(recipient: str, otp: str) -> None:
    sender = os.getenv("RBI_BANK_EMAIL", "regalbankofindia@gmail.com")
    app_password = os.getenv("RBI_BANK_APP_PASSWORD", "")

    if not app_password:
        print(f"[OTP DEBUG] OTP for {recipient}: {otp}")
        print("Set RBI_BANK_APP_PASSWORD to enable real email sending.")
        return

    message = MIMEText(f"{otp} is your OTP for Regal Bank of India login. Valid for 5 minutes.")
    message["Subject"] = "RBI Customer Login OTP"
    message["From"] = sender
    message["To"] = recipient

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], message.as_string())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP email: {exc}") from exc


def _get_account_row(cursor: Any, account_number: str) -> Any:
    cursor.execute(
        """
        SELECT id, account_number, holder_name, password, email, account_type, balance, created_at
        FROM accounts
        WHERE account_number = ?
        """,
        (account_number,),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return row


def _assert_customer_password(account_row: Any, password: int) -> None:
    if int(account_row["password"]) != int(password):
        raise HTTPException(status_code=401, detail="Invalid password")


def _verify_login_otp(cursor: Any, account_id: int, otp: str) -> None:
    cursor.execute(
        """
        SELECT id, otp_code, expires_at
        FROM otp_codes
        WHERE account_id = ? AND purpose = ? AND consumed_at IS NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (account_id, OTP_PURPOSE_LOGIN),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="No active OTP. Please request OTP first")

    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="OTP expired. Please request a new OTP")

    if row["otp_code"] != otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    cursor.execute("UPDATE otp_codes SET consumed_at = ? WHERE id = ?", (_utc_now(), row["id"]))


def list_accounts() -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT account_number, holder_name, email, account_type, balance, created_at
            FROM accounts
            ORDER BY id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]


def get_account(account_number: str) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.cursor()
        row = _get_account_row(cursor, account_number)
        return {
            "account_number": row["account_number"],
            "holder_name": row["holder_name"],
            "email": row["email"],
            "account_type": row["account_type"],
            "balance": row["balance"],
            "created_at": row["created_at"],
        }


def login_admin(name: str, password: str) -> AdminLoginResponse:
    if name.strip() != ADMIN_NAME or str(password).strip() != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    return AdminLoginResponse(message="Admin authenticated successfully", admin_name=ADMIN_NAME)


def create_customer_account(request: CustomerSignupRequest) -> CustomerSignupResponse:
    email = request.email.strip().lower()
    if not _is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    with get_connection() as connection:
        cursor = connection.cursor()

        account_number = None
        for _ in range(3000):
            candidate = str(random.randint(60000, 70000))
            cursor.execute("SELECT 1 FROM accounts WHERE account_number = ?", (candidate,))
            if cursor.fetchone() is None:
                account_number = candidate
                break

        if account_number is None:
            raise HTTPException(status_code=500, detail="Could not generate unique account number")

        password = random.randint(200, 999)
        now = _utc_now()

        cursor.execute(
            """
            INSERT INTO accounts(account_number, holder_name, password, email, account_type, balance, created_at)
            VALUES (?, ?, ?, ?, 'SAVINGS', ?, ?)
            """,
            (account_number, request.name.strip(), password, email, request.opening_balance, now),
        )
        connection.commit()

    return CustomerSignupResponse(
        account_number=account_number,
        password=password,
        holder_name=request.name.strip(),
        email=email,
        balance=request.opening_balance,
        message="Welcome to the REGAL BANK OF INDIA",
    )


def request_customer_login_otp(request: CustomerLoginOTPRequest) -> OTPDispatchResponse:
    provided_email = (request.email or "").strip().lower()
    if provided_email and not _is_valid_email(provided_email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    with get_connection() as connection:
        cursor = connection.cursor()
        row = _get_account_row(cursor, request.account_number)
        _assert_customer_password(row, request.password)

        email = (row["email"] or "").strip().lower()
        if not email:
            if not provided_email:
                raise HTTPException(
                    status_code=400,
                    detail="No registered email found. Provide email once to enable OTP login",
                )
            cursor.execute("UPDATE accounts SET email = ? WHERE id = ?", (provided_email, row["id"]))
            email = provided_email

        otp = _generate_otp()
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=OTP_TTL_SECONDS)).isoformat()

        cursor.execute(
            """
            INSERT INTO otp_codes(account_id, purpose, otp_code, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (row["id"], OTP_PURPOSE_LOGIN, otp, expires_at, now.isoformat()),
        )
        _send_otp_email(email, otp)
        connection.commit()

    return OTPDispatchResponse(
        message="OTP sent to registered email",
        expires_in_seconds=OTP_TTL_SECONDS,
        destination=_mask_email(email),
    )


def verify_customer_login(request: CustomerLoginVerifyRequest) -> CustomerSummary:
    with get_connection() as connection:
        cursor = connection.cursor()
        row = _get_account_row(cursor, request.account_number)
        _assert_customer_password(row, request.password)
        _verify_login_otp(cursor, row["id"], request.otp.strip())
        connection.commit()

        return CustomerSummary(
            account_number=row["account_number"],
            holder_name=row["holder_name"],
            balance=row["balance"],
            minimum_balance=MINIMUM_BALANCE,
            created_at=datetime.fromisoformat(row["created_at"]),
        )


def withdraw(account_number: str, password: int, amount: float) -> OperationResponse:
    with get_connection() as connection:
        cursor = connection.cursor()
        row = _get_account_row(cursor, account_number)
        _assert_customer_password(row, password)

        new_balance = float(row["balance"]) - amount
        if new_balance < MINIMUM_BALANCE:
            raise HTTPException(status_code=400, detail="Withdrawal denied. Minimum balance must be maintained")

        now = _utc_now()
        cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, row["id"]))
        cursor.execute(
            """
            INSERT INTO transactions(account_id, txn_type, amount, description, created_at)
            VALUES (?, 'DEBIT', ?, ?, ?)
            """,
            (row["id"], amount, "Withdrawal", now),
        )
        connection.commit()

        return OperationResponse(message="Withdrawal successful", balance=new_balance)


def deposit(account_number: str, request: DepositRequest) -> OperationResponse:
    with get_connection() as connection:
        cursor = connection.cursor()
        row = _get_account_row(cursor, account_number)
        _assert_customer_password(row, request.password)

        balance = float(row["balance"])
        expected_total = None
        frequency = request.recurring_frequency
        now = _utc_now()

        if request.deposit_type == "NORMAL":
            balance += request.amount
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (balance, row["id"]))
            cursor.execute(
                """
                INSERT INTO transactions(account_id, txn_type, amount, description, created_at)
                VALUES (?, 'CREDIT', ?, ?, ?)
                """,
                (row["id"], request.amount, "Normal deposit", now),
            )
            message = "Deposit successful"

        elif request.deposit_type == "FIXED":
            expected_total = request.amount + (request.amount * 1 * 12 / 100)
            message = "Fixed deposit projection calculated"

        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS recurring_count
                FROM deposits
                WHERE account_id = ? AND deposit_type = 'RECURRING'
                """,
                (row["id"],),
            )
            m = int(cursor.fetchone()["recurring_count"]) + 1

            if frequency == "MONTHLY":
                expected_total = request.amount * ((1 + 12 / (m * 12)) ** (m * 1))
            elif frequency == "QUARTERLY":
                expected_total = request.amount * ((1 + 12 / (m * 4)) ** (m * 1))
            else:
                expected_total = request.amount * ((1 + 12 / (m * 1)) ** (m * 1))
            message = "Recurring deposit projection calculated"

        cursor.execute(
            """
            INSERT INTO deposits(account_id, deposit_type, frequency, amount, expected_total, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (row["id"], request.deposit_type, frequency, request.amount, expected_total, now),
        )
        connection.commit()

        return OperationResponse(message=message, balance=balance, expected_total=expected_total)


def list_transactions(account_number: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        account_row = _get_account_row(cursor, account_number)

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


def list_deposits(account_number: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        account_row = _get_account_row(cursor, account_number)

        cursor.execute(
            """
            SELECT d.id, a.account_number, d.deposit_type, d.frequency, d.amount, d.expected_total, d.created_at
            FROM deposits d
            JOIN accounts a ON a.id = d.account_id
            WHERE d.account_id = ?
            ORDER BY d.id DESC
            LIMIT ?
            """,
            (account_row["id"], limit),
        )

        return [dict(row) for row in cursor.fetchall()]


def process_card_request(account_number: str, request: CardRequest) -> CardResponse:
    with get_connection() as connection:
        cursor = connection.cursor()
        account_row = _get_account_row(cursor, account_number)
        _assert_customer_password(account_row, request.password)

        status = "RECEIVED"
        if request.action == "ACTIVATE_OLD":
            if request.card_number is None or not request.card_number.isdigit() or len(request.card_number) != 16:
                raise HTTPException(status_code=400, detail="Invalid card number")
            message = "The card will be activated soon"
            status = "ACTIVATION_PENDING"
        else:
            message = "Application received. Visit your home branch for document verification"
            status = "BRANCH_VISIT_REQUIRED"

        cursor.execute(
            """
            INSERT INTO card_requests(account_id, card_type, action, card_number, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (account_row["id"], request.card_type, request.action, request.card_number, status, _utc_now()),
        )
        connection.commit()

    return CardResponse(message=message, status=status)


def process_loan_request(account_number: str, request: LoanRequest) -> LoanResponse:
    if not request.phone.isdigit() or len(request.phone) != 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    if request.send_forms and not request.email:
        raise HTTPException(status_code=400, detail="Email is required when send_forms is true")

    with get_connection() as connection:
        cursor = connection.cursor()
        account_row = _get_account_row(cursor, account_number)
        _assert_customer_password(account_row, request.password)

        cursor.execute(
            """
            INSERT INTO loan_requests(account_id, loan_type, phone, send_forms, email, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                account_row["id"],
                request.loan_type,
                request.phone,
                int(request.send_forms),
                request.email,
                _utc_now(),
            ),
        )
        connection.commit()

    message = "Request saved. Visit your home branch for further details"
    form_url = LOAN_FORM_URLS[request.loan_type] if request.send_forms else None

    return LoanResponse(message=message, requirements=LOAN_REQUIREMENTS, form_url=form_url)


def contact_info() -> ContactInfo:
    return ContactInfo(
        phones=["9980259715", "6364336888"],
        email="RegalBankofIndia@gmail.com",
    )
