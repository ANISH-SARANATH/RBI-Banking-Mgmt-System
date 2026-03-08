from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_database
from .schemas import (
    Account,
    AdminLoginRequest,
    AdminLoginResponse,
    AmountRequest,
    CardRequest,
    CardResponse,
    ContactInfo,
    CustomerLoginOTPRequest,
    CustomerLoginVerifyRequest,
    CustomerSignupRequest,
    CustomerSignupResponse,
    CustomerSummary,
    DepositRecord,
    DepositRequest,
    LoanRequest,
    LoanResponse,
    OTPDispatchResponse,
    OperationResponse,
    Transaction,
)
from .services import (
    contact_info,
    create_customer_account,
    deposit,
    get_account,
    list_accounts,
    list_deposits,
    list_transactions,
    login_admin,
    process_card_request,
    process_loan_request,
    request_customer_login_otp,
    verify_customer_login,
    withdraw,
)

app = FastAPI(
    title="RBI Banking Management System",
    version="2.1.0",
    description="Customer-first banking web system with email OTP authentication.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
init_database()


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/admin/login", response_model=AdminLoginResponse)
def admin_login(request: AdminLoginRequest) -> AdminLoginResponse:
    return login_admin(name=request.name, password=request.password)


@app.post("/api/auth/customer/signup", response_model=CustomerSignupResponse)
def customer_signup(request: CustomerSignupRequest) -> CustomerSignupResponse:
    return create_customer_account(request)


@app.post("/api/auth/customer/login/request-otp", response_model=OTPDispatchResponse)
def customer_login_request_otp(request: CustomerLoginOTPRequest) -> OTPDispatchResponse:
    return request_customer_login_otp(request)


@app.post("/api/auth/customer/login/verify", response_model=CustomerSummary)
def customer_login_verify(request: CustomerLoginVerifyRequest) -> CustomerSummary:
    return verify_customer_login(request)


@app.get("/api/accounts", response_model=list[Account])
def get_accounts() -> list[dict]:
    return list_accounts()


@app.get("/api/accounts/{account_number}", response_model=Account)
def get_account_by_number(account_number: str) -> dict:
    return get_account(account_number)


@app.post("/api/accounts/{account_number}/withdraw", response_model=OperationResponse)
def withdraw_amount(account_number: str, request: AmountRequest) -> OperationResponse:
    return withdraw(account_number=account_number, password=request.password, amount=request.amount)


@app.post("/api/accounts/{account_number}/deposit", response_model=OperationResponse)
def deposit_amount(account_number: str, request: DepositRequest) -> OperationResponse:
    return deposit(account_number=account_number, request=request)


@app.get("/api/accounts/{account_number}/transactions", response_model=list[Transaction])
def get_transactions(account_number: str, limit: int = 20) -> list[dict]:
    return list_transactions(account_number=account_number, limit=limit)


@app.get("/api/accounts/{account_number}/deposits", response_model=list[DepositRecord])
def get_deposits(account_number: str, limit: int = 20) -> list[dict]:
    return list_deposits(account_number=account_number, limit=limit)


@app.post("/api/accounts/{account_number}/cards", response_model=CardResponse)
def cards(account_number: str, request: CardRequest) -> CardResponse:
    return process_card_request(account_number=account_number, request=request)


@app.post("/api/accounts/{account_number}/loans", response_model=LoanResponse)
def loans(account_number: str, request: LoanRequest) -> LoanResponse:
    return process_loan_request(account_number=account_number, request=request)


@app.get("/api/contact", response_model=ContactInfo)
def contact() -> ContactInfo:
    return contact_info()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/admin")
def admin_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "admin.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
