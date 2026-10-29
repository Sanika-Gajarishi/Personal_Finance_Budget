from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category: str = Field(min_length=1, max_length=100)

    monthly_limit: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class BudgetUpdate(BaseModel):
    monthly_limit: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category: str
    monthly_limit: Decimal
    month: int
    year: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetSummaryItem(BaseModel):
    category: str
    monthly_limit: Decimal
    amount_spent: Decimal
    remaining_budget: Decimal
    percentage_used: float
    status: str


class MonthlyBudgetSummary(BaseModel):
    month: int
    year: int
    total_budget: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    budgets: list[BudgetSummaryItem]