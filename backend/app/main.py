from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.transactions import router as transactions_router
from app.api.budgets import router as budgets_router

app = FastAPI(
    title="Personal Finance & Expense Agent",
    description=(
        "An AI-powered personal finance "
        "and expense management API."
    ),
    version="0.1.0",
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)
app.include_router(
    transactions_router,
    prefix="/transactions",
    tags=["Transactions"],
)
app.include_router(
    budgets_router,
    prefix="/budgets",
    tags=["Budgets"],
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