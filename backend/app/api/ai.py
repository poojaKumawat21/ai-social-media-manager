from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.ai_ideas_service import generate_ai_ideas


router = APIRouter(prefix="/ai", tags=["AI"])


class GenerateIdeasRequest(BaseModel):
    topic: str


@router.post("/ideas")
def generate_ideas(
    data: GenerateIdeasRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        topic = data.topic.strip()

        if not topic:
            raise HTTPException(
                status_code=400,
                detail="Topic is required.",
            )

        ideas = generate_ai_ideas(topic)

        if not ideas:
            raise HTTPException(
                status_code=500,
                detail="AI could not generate ideas.",
            )

        return {
            "ideas": ideas
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )