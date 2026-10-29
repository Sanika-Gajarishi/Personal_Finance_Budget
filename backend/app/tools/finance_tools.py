from calendar import monthrange
from decimal import Decimal
from datetime import date
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def get_category_spending(
    db: Session,
    user_id: int,
    category: str,
    month: int,
    year: int,
) -> dict:
    """
    Calculate a user's total expenses for a category
    during a specific month.

    Args:
        db: Active SQLAlchemy database session.
        user_id: ID of the authenticated user.
        category: Expense category, such as Food or Shopping.
        month: Month number from 1 to 12.
        year: Four-digit year.

    Returns:
        A dictionary containing the category's total spending.
    """

    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")

    if year < 1900 or year > 9999:
        raise ValueError("Year must be between 1900 and 9999.")

    if not category or not category.strip():
        raise ValueError("Category cannot be empty.")

    # Calculate the date range for the selected month.
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    # Query only the authenticated user's expense transactions.
    statement = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            func.lower(Transaction.category) == category.strip().lower(),
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
    )

    total = db.execute(statement).scalar_one()

    # Convert Decimal to string to preserve monetary precision.
    total_spending = Decimal(str(total)).quantize(
        Decimal("0.01")
    )

    return {
        "category": category.strip(),
        "month": month,
        "year": year,
        "total_spending": str(total_spending),
        "currency": "INR",
    }