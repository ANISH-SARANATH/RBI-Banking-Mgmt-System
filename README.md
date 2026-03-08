# RBI Banking Management System

Full-stack banking demo for **Regal Bank of India** with:
- Python API (FastAPI)
- SQLite database
- YONO-inspired responsive web UI

## Project Layout
- `backend/app/main.py` - API + static UI server
- `backend/app/database.py` - SQLite schema and seed data
- `backend/app/services.py` - account and transfer logic
- `backend/app/schemas.py` - request/response models
- `frontend/index.html` - UI shell
- `frontend/styles.css` - custom visual design
- `frontend/app.js` - API integration for accounts, transactions, transfers
- `docs/Computer Project Report.pdf` - documentation report

## API Endpoints
- `GET /api/health`
- `GET /api/accounts`
- `GET /api/accounts/{account_number}`
- `GET /api/accounts/{account_number}/transactions?limit=10`
- `POST /api/transfers`

## Run Locally
```bash
cd RBI/backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Notes
- SQLite file is created automatically at `backend/data/rbi_bank.db`.
- Sample accounts and transactions are seeded on first startup.
