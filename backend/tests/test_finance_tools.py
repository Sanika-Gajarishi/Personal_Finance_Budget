import pytest
from datetime import date
from decimal import Decimal

from app.models.user import User
from app.models.transaction import Transaction
from app.tools.finance_tools import get_category_spending


def create_test_user(db, user_id: int, email: str):
    """Create a user required by the transaction foreign key."""
    user = User(
        id=user_id,
        email=email,
        hashed_password="test-password-hash",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def add_transaction(
    db,
    user_id: int,
    amount: str,
    category: str,
    transaction_type: str,
    transaction_date: date,
):
    """Insert a transaction into the test database."""
    transaction = Transaction(
        user_id=user_id,
        amount=Decimal(amount),
        category=category,
        transaction_type=transaction_type,
        transaction_date=transaction_date,
        description=f"Test {category} transaction",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


def test_category_spending_calculates_expenses(db_session):
    create_test_user(db_session, 1, "user1@example.com")

    add_transaction(
        db_session, 1, "250.00", "Food", "expense", date(2026, 10, 5)
    )
    add_transaction(
        db_session, 1, "400.00", "Food", "expense", date(2026, 10, 12)
    )
    add_transaction(
        db_session, 1, "1200.00", "Shopping", "expense", date(2026, 10, 15)
    )
    add_transaction(
        db_session, 1, "500.00", "Food", "income", date(2026, 10, 21)
    )

    result = get_category_spending(
        db=db_session,
        user_id=1,
        category="Food",
        month=10,
        year=2026,
    )

    assert result["total_spending"] == "650.00"
    assert result["category"] == "Food"
    assert result["month"] == 10
    assert result["year"] == 2026
    assert result["currency"] == "INR"


def test_category_spending_is_case_insensitive(db_session):
    create_test_user(db_session, 1, "user1@example.com")

    add_transaction(
        db_session, 1, "300.00", "Food", "expense", date(2026, 10, 5)
    )

    result = get_category_spending(
        db=db_session,
        user_id=1,
        category="food",
        month=10,
        year=2026,
    )

    assert result["total_spending"] == "300.00"


def test_category_spending_filters_by_month(db_session):
    create_test_user(db_session, 1, "user1@example.com")

    add_transaction(
        db_session, 1, "300.00", "Food", "expense", date(2026, 10, 5)
    )
    add_transaction(
        db_session, 1, "700.00", "Food", "expense", date(2026, 9, 15)
    )

    result = get_category_spending(
        db=db_session,
        user_id=1,
        category="Food",
        month=10,
        year=2026,
    )

    assert result["total_spending"] == "300.00"


def test_category_spending_isolates_users(db_session):
    create_test_user(db_session, 1, "user1@example.com")
    create_test_user(db_session, 2, "user2@example.com")

    add_transaction(
        db_session, 1, "300.00", "Food", "expense", date(2026, 10, 5)
    )
    add_transaction(
        db_session, 2, "900.00", "Food", "expense", date(2026, 10, 10)
    )

    result = get_category_spending(
        db=db_session,
        user_id=1,
        category="Food",
        month=10,
        year=2026,
    )

    assert result["total_spending"] == "300.00"


def test_category_spending_returns_zero_when_no_expenses(db_session):
    result = get_category_spending(
        db=db_session,
        user_id=1,
        category="Travel",
        month=10,
        year=2026,
    )

    assert result["total_spending"] == "0.00"


def test_category_spending_rejects_invalid_month(db_session):
    with pytest.raises(
        ValueError,
        match="Month must be between 1 and 12.",
    ):
        get_category_spending(
            db=db_session,
            user_id=1,
            category="Food",
            month=13,
            year=2026,
        )