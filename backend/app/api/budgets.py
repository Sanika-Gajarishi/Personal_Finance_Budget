from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetResponse,
    BudgetSummaryItem,
    BudgetUpdate,
    MonthlyBudgetSummary,
)


router = APIRouter()



@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = budget_data.category.strip()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category cannot be empty",
        )

    existing_budget = db.scalar(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.category == category,
            Budget.month == budget_data.month,
            Budget.year == budget_data.year,
        )
    )

    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A budget already exists for this category and month",
        )

    budget = Budget(
        user_id=current_user.id,
        category=category,
        monthly_limit=budget_data.monthly_limit,
        month=budget_data.month,
        year=budget_data.year,
    )

    db.add(budget)

    try:
        db.commit()
        db.refresh(budget)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A budget already exists for this category and month",
        )

    return budget




@router.get(
    "/",
    response_model=list[BudgetResponse],
)
def get_budgets(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Budget).where(
        Budget.user_id == current_user.id
    )

    if month is not None:
        statement = statement.where(Budget.month == month)

    if year is not None:
        statement = statement.where(Budget.year == year)

    statement = statement.order_by(
        Budget.year.desc(),
        Budget.month.desc(),
        Budget.category.asc(),
    )

    return db.scalars(statement).all()




@router.patch(
    "/{budget_id}",
    response_model=BudgetResponse,
)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Budget).where(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
    )

    budget = db.scalar(statement)

    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    budget.monthly_limit = budget_data.monthly_limit

    db.commit()
    db.refresh(budget)

    return budget




@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Budget).where(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
    )

    budget = db.scalar(statement)

    if budget is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    db.delete(budget)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)




@router.get(
    "/summary",
    response_model=MonthlyBudgetSummary,
)
def get_monthly_budget_summary(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budgets = db.scalars(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.month == month,
            Budget.year == year,
        ).order_by(Budget.category.asc())
    ).all()

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    spending_statement = (
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("amount_spent"),
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Transaction.category)
    )

    spending_rows = db.execute(spending_statement).all()

    spending_by_category = {
        category: amount_spent
        for category, amount_spent in spending_rows
    }

    summary_items = []

    for budget in budgets:
        amount_spent = spending_by_category.get(
            budget.category,
            Decimal("0.00"),
        )

        remaining_budget = budget.monthly_limit - amount_spent

        percentage_used = float(
            amount_spent / budget.monthly_limit * 100
        )

        if amount_spent > budget.monthly_limit:
            budget_status = "exceeded"
        elif amount_spent == budget.monthly_limit:
            budget_status = "limit_reached"
        elif percentage_used >= 80:
            budget_status = "warning"
        else:
            budget_status = "within_budget"

        summary_items.append(
            BudgetSummaryItem(
                category=budget.category,
                monthly_limit=budget.monthly_limit,
                amount_spent=amount_spent,
                remaining_budget=remaining_budget,
                percentage_used=round(percentage_used, 2),
                status=budget_status,
            )
        )

    total_budget = sum(
        (item.monthly_limit for item in summary_items),
        Decimal("0.00"),
    )

    total_spent = sum(
        (item.amount_spent for item in summary_items),
        Decimal("0.00"),
    )

    return MonthlyBudgetSummary(
        month=month,
        year=year,
        total_budget=total_budget,
        total_spent=total_spent,
        total_remaining=total_budget - total_spent,
        budgets=summary_items,
    )