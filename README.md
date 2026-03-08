# RBI Banking Management System

Upgraded from the original project logic into a working FastAPI + SQLite + frontend banking website.

## What This Version Supports
- Customer account creation (random account number and password, opening balance min `10000`)
- Customer sign in with email OTP authentication (on `/`)
- Withdraw with minimum-balance rule (`1000`)
- Deposits:
  - Normal deposit (updates balance)
  - Fixed deposit (projection)
  - Recurring deposit (projection by frequency)
- Cards workflow (activate old/apply new)
- Loans workflow (education/home/auto, optional form URL)
- Transaction history and deposits history
- Contact section
- Admin-only login (on `/admin` only):
  - Name: `Anish`
  - Password: `1939`

## OTP Email Setup
Set these environment variables before running backend:
- `RBI_BANK_EMAIL` (sender email, default: `regalbankofindia@gmail.com`)
- `RBI_BANK_APP_PASSWORD` (email app password)

If `RBI_BANK_APP_PASSWORD` is not set, OTP is printed in backend console for development/testing.

## Run
```bash
cd RBI/backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open customer portal: [http://127.0.0.1:8000](http://127.0.0.1:8000)
Open admin portal: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

## Data
- SQLite DB: `backend/data/rbi_bank.db`
- Existing old DB files are untouched.
