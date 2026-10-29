from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TransactionType = Literal["income", "expense"]


class TransactionCreate(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    transaction_type: TransactionType

    transaction_date: date = Field(
        default_factory=date.today,
    )


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    transaction_type: TransactionType | None = None

    transaction_date: date | None = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    category: str
    description: str | None
    transaction_type: TransactionType
    transaction_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)