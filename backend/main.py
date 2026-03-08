"""
Main banking script based on the original source-code flow from the project PDF.
Adapted to SQLite so it runs locally without MySQL setup.
"""

import math
import os
import random
import smtplib
import sqlite3
from email.mime.text import MIMEText
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "rbi_pdf_main.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS client (
                accountnum INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                password INTEGER NOT NULL,
                totalbal REAL NOT NULL
            )
            """
        )
        con.commit()


def generate_otp() -> str:
    digits = "0123456789"
    otp = ""
    for _ in range(6):
        otp += digits[math.floor(random.random() * 10)]
    return otp


def send_otp_email(recipient: str, otp: str) -> None:
    sender = os.getenv("RBI_BANK_EMAIL", "regalbankofindia@gmail.com")
    app_password = os.getenv("RBI_BANK_APP_PASSWORD", "")

    if not app_password:
        print(f"[OTP DEBUG] OTP for {recipient}: {otp}")
        print("Set RBI_BANK_APP_PASSWORD to enable real email sending.")
        return

    msg = MIMEText(f"{otp} is your OTP")
    msg["Subject"] = "RBI OTP Verification"
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], msg.as_string())


def verify_otp_flow() -> bool:
    email_id = input("Enter your email: ").strip()
    otp = generate_otp()
    send_otp_email(email_id, otp)

    first_try = input("Enter Your OTP: ").strip()
    if first_try == otp:
        print("Verified")
        return True

    print("Please Check your OTP again")
    second_try = input("Enter Your OTP: ").strip()
    if second_try == otp:
        print("Verified")
        return True

    print("Access Denied")
    return False


def create_account(cur: sqlite3.Cursor, con: sqlite3.Connection) -> tuple[int, int, float]:
    name = input("Enter your name: ").strip()

    while True:
        acc = random.randint(60000, 70000)
        cur.execute("SELECT 1 FROM client WHERE accountnum = ?", (acc,))
        if cur.fetchone() is None:
            break

    password = random.randint(200, 999)
    print("Your Account Number is:", acc)
    print("Your Password is:", password)
    print("Please enter the amount to be deposited into your account")
    print("(Minimum Amount 10000):")
    money = float(input().strip())

    if money < 10000:
        raise ValueError("Minimum opening balance is 10000")

    cur.execute(
        "INSERT INTO client(accountnum, name, password, totalbal) VALUES (?, ?, ?, ?)",
        (acc, name, password, money),
    )
    con.commit()
    print("Welcome to the REGAL BANK OF INDIA")
    return acc, password, money


def sign_in(cur: sqlite3.Cursor) -> tuple[int, int, float]:
    account = input("Enter your Account Number: ").strip()
    if not account.isdigit():
        raise ValueError("Invalid Account Number")

    cur.execute("SELECT * FROM client WHERE accountnum = ?", (int(account),))
    row = cur.fetchone()
    if row is None:
        raise ValueError("Invalid Account Number")

    for attempt in range(2):
        entered = input("Enter your password: ").strip()
        if entered.isdigit() and int(entered) == row["password"]:
            print("Welcome to the REGAL BANK OF INDIA")
            return row["accountnum"], row["password"], float(row["totalbal"])

        if attempt == 0:
            print("Invalid Password. Please try again.")
            print("(This is your last chance!)")

    raise PermissionError("You have exceeded your number of attempts.")


def cards_menu() -> None:
    print("Choose one of the following:")
    print("1.Debit Card")
    print("2.Credit Card")
    print("3.Business Card")
    choice = int(input("Enter your choice: ").strip())

    if choice not in (1, 2, 3):
        print("Invalid Choice. Try again.....")
        return

    print("Choose one of the following:")
    print("1.Activating old card")
    print("2.Applying for New Card")
    action = int(input("Enter your choice:").strip())

    if action == 1:
        if not verify_otp_flow():
            return
        card = input("Enter your 16 digit card number:").strip()
        if card.isdigit() and len(card) == 16:
            print("The card will be activated soon")
        else:
            print("Invalid Card Number...")
    elif action == 2:
        print("DOCUMENTS REQUIRED")
        print("a)Aadhar Card")
        print("b)PAN Card")
        print("c)Driving License")
        print("d)Social security card")
        print("The Application will be available at home branch")
        print("VISIT THE HOME BRANCH FOR FURTHER DETAILS")
    else:
        print("Invalid Choice. Try again.....")


def loans_menu() -> None:
    loan_map = {
        1: ("Education Loans", "https://sites.google.com/view/regalbankofindia-educationloan/home"),
        2: ("Home Loans", "https://sites.google.com/view/regalbankofindia-homeloan/home"),
        3: ("Auto Loans", "https://sites.google.com/view/regalbankofindia-autoloan/home"),
    }

    print("Choose one of the following:")
    print("1.Education Loans")
    print("2.Home Loans")
    print("3.Auto Loans")
    choice = int(input("Enter your choice: ").strip())

    if choice not in loan_map:
        print("Invalid Choice. Try again.....")
        return

    phone = input("Enter your phone number: ").strip()
    if not (phone.isdigit() and len(phone) == 10):
        print("Invalid phone number...")
        return

    print("DOCUMENTS REQUIRED")
    print("a)Application form with photograph")
    print("b)Identity and Residence proof")
    print("c)Last 6 months bank statements")
    print("d)Processing fee cheque")
    print("e)Educational Qualifications Certificate")
    print("VISIT YOUR HOME BRANCH FOR FURTHER DETAILS")

    ask = input("Would you like us to send you the forms (Y/N)").strip().upper()
    if ask == "Y":
        loan_name, url = loan_map[choice]
        recipient = input("Enter your email:").strip()
        print(f"{loan_name} Form URL sent to {recipient}")
        print(f"URL - {url}")


def main() -> None:
    init_db()
    con = get_connection()
    cur = con.cursor()

    print("Choose one of the following:")
    print("1. Create account")
    print("2. Sign in")
    signin_choice = input("Enter your choice: ").strip()

    try:
        if signin_choice == "1":
            account_num, password, curr_bal = create_account(cur, con)
        elif signin_choice == "2":
            account_num, password, curr_bal = sign_in(cur)
        else:
            print("Invalid Choice.")
            return
    except Exception as exc:
        print(exc)
        return

    transactions: list[tuple[str, float]] = []
    savings: list[tuple[str, float]] = []
    minimum_balance = 1000.0
    m = 1

    while True:
        print("\nChoose one of the following:")
        print("1. Withdraw")
        print("2. Deposit")
        print("3. Cards")
        print("4. Loans")
        print("5. Check current balance")
        print("6. Transaction History")
        print("7. Deposits History")
        print("8. Contact Us")
        print("9. Logout")

        choice = int(input("Enter your choice: ").strip())

        if choice == 1:
            if not verify_otp_flow():
                break

            print("Current Balance in INR:", curr_bal)
            print("Minimum Balance in INR:", minimum_balance)
            withd = float(input("Enter amount to be withdrawn: ").strip())
            if curr_bal - withd < minimum_balance:
                print("Withdrawal denied. Minimum balance must be maintained.")
                continue
            curr_bal -= withd
            print("Current Balance in INR:", curr_bal)
            transactions.append(("Withdrawn", withd))

        elif choice == 2:
            if not verify_otp_flow():
                break

            print("Choose one of the following:")
            print("1.Normal Deposit")
            print("2.Fixed Deposit")
            print("3.Recurring Deposit")
            deposit_type = int(input("Enter your choice: ").strip())

            if deposit_type == 1:
                print("Current Balance in INR:", curr_bal)
                print("Minimum Balance in INR:", minimum_balance)
                dep_t = float(input("Enter amount to be deposited: ").strip())
                curr_bal += dep_t
                print("Current Balance in INR:", curr_bal)
                transactions.append(("Deposited", dep_t))

            elif deposit_type == 2:
                print("The rate of Interest per annum: 12%")
                print("Current Balance:", curr_bal)
                print("Minimum Balance:", minimum_balance)
                dep_t = float(input("Enter amount to be deposited: ").strip())
                annual_calc_total = dep_t + (dep_t * 1 * 12 / 100)
                print("Expected Total Balance-Annually:", annual_calc_total)
                savings.append(("Savings - Fixed Deposit", dep_t))

            elif deposit_type == 3:
                print("The rate of Interest per annum: 12%")
                print("Current Balance:", curr_bal)
                print("Minimum Balance:", minimum_balance)
                dep_t = float(input("Enter amount to be deposited: ").strip())
                print("Choose one of the following")
                print("1.Monthly")
                print("2.Quarterly")
                print("3.Annually")
                freq = int(input("Enter your choice: ").strip())

                if freq == 1:
                    month_calc_total = dep_t * ((1 + 12 / (m * 12)) ** (m * 1))
                    print("Expected Total Balance-Monthly", month_calc_total)
                elif freq == 2:
                    quarter_calc_total = dep_t * ((1 + 12 / (m * 4)) ** (m * 1))
                    print("Expected Total Balance-Quarterly", quarter_calc_total)
                elif freq == 3:
                    annual_calc_total = dep_t * ((1 + 12 / (m * 1)) ** (m * 1))
                    print("Expected Total Balance-Annually", annual_calc_total)
                else:
                    print("Invalid choice.")

                savings.append(("Savings - Recurring Deposit", dep_t))
                m += 1
            else:
                print("Invalid Choice. Try again.....")

        elif choice == 3:
            cards_menu()

        elif choice == 4:
            loans_menu()

        elif choice == 5:
            print("Your Current balance is:", curr_bal)

        elif choice == 6:
            print("TRANSACTION HISTORY")
            for item in transactions:
                print(item)

        elif choice == 7:
            print("DEPOSITS HISTORY")
            for item in savings:
                print(item)

        elif choice == 8:
            print("CONTACT US")
            print("Phone Numbers:")
            print("   9980259715")
            print("   6364336888")
            print("Email:")
            print("   RegalBankofIndia@gmail.com")

        elif choice == 9:
            log = input("Are you sure you want to logout? (Y/N)").strip().upper()
            if log == "Y":
                cur.execute(
                    "UPDATE client SET totalbal = ? WHERE accountnum = ? AND password = ?",
                    (curr_bal, account_num, password),
                )
                con.commit()
                print("Logged out successfully.")
                break

        else:
            print("Invalid choice. Try again.....")

    con.close()


if __name__ == "__main__":
    main()
