from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.gemini_service import answer_category_spending_question


router = APIRouter()


# --------------------------------------------------
# 1. Request schema
# --------------------------------------------------

class AskFinanceRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="A question about the user's personal finances.",
    )


# --------------------------------------------------
# 2. Ask the AI finance assistant
# --------------------------------------------------

@router.post("/ask")
def ask_finance_assistant(
    request: AskFinanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty.",
        )

    try:
        result = answer_category_spending_question(
            question=question,
            db=db,
            user_id=current_user.id,
        )

        return result

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        # Do not expose internal errors or API credentials to the client.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant could not process your request.",
        ) from None