# RBI Banking Management System

Updated so the **main Python code is based on the source flow from your PDF report**.

## Main Python Code (PDF-based)
- `backend/main.py`
- Includes the original project flow: create account, sign in, withdraw, deposit (normal/fixed/recurring), cards, loans, transaction history, deposits history, contact, logout.
- Uses SQLite (`backend/data/rbi_pdf_main.db`) instead of MySQL for easy local execution.

## Web UI (Burgundy/Purple/White)
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

## API Layer (existing)
- `backend/app/main.py` and related files remain available for the web UI APIs.

## Run PDF-based Main Code
```bash
cd RBI/backend
python main.py
```

## Run Web UI + API
```bash
cd RBI/backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open: http://127.0.0.1:8000
