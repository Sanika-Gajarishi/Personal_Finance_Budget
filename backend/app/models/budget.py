from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Budget(Base):
    __tablename__ = "budgets"

    __table_args__ = (
        CheckConstraint(
            "monthly_limit > 0",
            name="ck_budgets_limit_positive",
        ),
        CheckConstraint(
            "month >= 1 AND month <= 12",
            name="ck_budgets_month_valid",
        ),
        CheckConstraint(
            "year >= 2000",
            name="ck_budgets_year_valid",
        ),
        UniqueConstraint(
            "user_id",
            "category",
            "month",
            "year",
            name="uq_budgets_user_category_period",
        ),
        Index(
            "ix_budgets_user_period",
            "user_id",
            "year",
            "month",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    monthly_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )