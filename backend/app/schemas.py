from datetime import datetime
from pydantic import BaseModel, Field


class Account(BaseModel):
    account_number: str
    holder_name: str
    account_type: str
    balance: float
    created_at: datetime


class Transaction(BaseModel):
    id: int
    account_number: str
    txn_type: str
    amount: float
    description: str
    created_at: datetime


class TransferRequest(BaseModel):
    from_account_number: str = Field(..., min_length=8)
    to_account_number: str = Field(..., min_length=8)
    amount: float = Field(..., gt=0)
    description: str = Field(default="Fund transfer", min_length=3, max_length=120)


class TransferResponse(BaseModel):
    transfer_id: int
    from_account_number: str
    to_account_number: str
    amount: float
    from_balance_after: float
    to_balance_after: float
    created_at: datetime
