from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_database
from .schemas import Account, Transaction, TransferRequest, TransferResponse
from .services import get_account, list_accounts, list_transactions, transfer_funds

app = FastAPI(
    title="RBI Banking Management System",
    version="1.0.0",
    description="Python + SQLite backend for Regal Bank of India management flows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/accounts", response_model=list[Account])
def get_accounts() -> list[dict]:
    return list_accounts()


@app.get("/api/accounts/{account_number}", response_model=Account)
def get_account_by_number(account_number: str) -> dict:
    return get_account(account_number)


@app.get("/api/accounts/{account_number}/transactions", response_model=list[Transaction])
def get_transactions(account_number: str, limit: int = 20) -> list[dict]:
    return list_transactions(account_number=account_number, limit=limit)


@app.post("/api/transfers", response_model=TransferResponse)
def post_transfer(request: TransferRequest) -> TransferResponse:
    return transfer_funds(request)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
