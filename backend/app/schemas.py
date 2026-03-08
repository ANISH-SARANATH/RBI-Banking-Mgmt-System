from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AdminLoginRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=1, max_length=32)


class AdminLoginResponse(BaseModel):
    message: str
    admin_name: str


class CustomerSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., min_length=6, max_length=120)
    opening_balance: float = Field(..., ge=10000)


class CustomerSignupResponse(BaseModel):
    account_number: str
    password: int
    holder_name: str
    email: str
    balance: float
    message: str


class CustomerLoginOTPRequest(BaseModel):
    account_number: str = Field(..., min_length=5, max_length=20)
    password: int = Field(..., ge=0)
    email: str | None = Field(default=None, max_length=120)


class CustomerLoginVerifyRequest(BaseModel):
    account_number: str = Field(..., min_length=5, max_length=20)
    password: int = Field(..., ge=0)
    otp: str = Field(..., min_length=6, max_length=6)


class OTPDispatchResponse(BaseModel):
    message: str
    expires_in_seconds: int
    destination: str


class CustomerSummary(BaseModel):
    account_number: str
    holder_name: str
    balance: float
    minimum_balance: float
    created_at: datetime


class AmountRequest(BaseModel):
    password: int = Field(..., ge=0)
    amount: float = Field(..., gt=0)


class DepositRequest(BaseModel):
    password: int = Field(..., ge=0)
    deposit_type: Literal["NORMAL", "FIXED", "RECURRING"]
    amount: float = Field(..., gt=0)
    recurring_frequency: Literal["MONTHLY", "QUARTERLY", "ANNUALLY"] | None = None

    @model_validator(mode="after")
    def validate_frequency(self) -> "DepositRequest":
        if self.deposit_type == "RECURRING" and self.recurring_frequency is None:
            raise ValueError("recurring_frequency is required for RECURRING deposits")
        return self


class OperationResponse(BaseModel):
    message: str
    balance: float
    expected_total: float | None = None


class Transaction(BaseModel):
    id: int
    account_number: str
    txn_type: str
    amount: float
    description: str
    created_at: datetime


class DepositRecord(BaseModel):
    id: int
    account_number: str
    deposit_type: str
    frequency: str | None
    amount: float
    expected_total: float | None
    created_at: datetime


class CardRequest(BaseModel):
    password: int = Field(..., ge=0)
    card_type: Literal["DEBIT", "CREDIT", "BUSINESS"]
    action: Literal["ACTIVATE_OLD", "APPLY_NEW"]
    card_number: str | None = Field(default=None, max_length=32)


class CardResponse(BaseModel):
    message: str
    status: str


class LoanRequest(BaseModel):
    password: int = Field(..., ge=0)
    loan_type: Literal["EDUCATION", "HOME", "AUTO"]
    phone: str = Field(..., min_length=10, max_length=10)
    send_forms: bool = False
    email: str | None = Field(default=None, max_length=120)


class LoanResponse(BaseModel):
    message: str
    requirements: list[str]
    form_url: str | None = None


class ContactInfo(BaseModel):
    phones: list[str]
    email: str


class Account(BaseModel):
    account_number: str
    holder_name: str
    email: str
    account_type: str
    balance: float
    created_at: datetime
