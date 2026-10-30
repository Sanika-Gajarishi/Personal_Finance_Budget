from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.transactions import router as transactions_router
from app.api.budgets import router as budgets_router
from app.api.ai import router as ai_router


app = FastAPI(
    title="Personal Finance & Expense Agent",
    description=(
        "An AI-powered personal finance "
        "and expense management API."
    ),
    version="0.1.0",
)


# Authentication endpoints
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)


# Transaction endpoints
app.include_router(
    transactions_router,
    prefix="/transactions",
    tags=["Transactions"],
)


# Budget endpoints
app.include_router(
    budgets_router,
    prefix="/budgets",
    tags=["Budgets"],
)


# AI finance assistant endpoints
app.include_router(
    ai_router,
    prefix="/ai",
    tags=["AI Finance Assistant"],
)


@app.get("/")
def root():
    return {
        "message": (
            "Welcome to the Personal Finance Agent API"
        )
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}