from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user
from app.database.supabase import get_database_client
from app.services.scheduler_service import (
    add_one_time_job,
    remove_one_time_job,
)


router = APIRouter(
    prefix="/scheduled-posts",
    tags=["Scheduled Posts"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class SchedulePostRequest(BaseModel):
    post_id: str
    scheduled_at: datetime
    platform: str = "linkedin"


# =========================================================
# CREATE SCHEDULED POST
# =========================================================

@router.post("")
def create_scheduled_post(
    data: SchedulePostRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        # -------------------------------------------------
        # Supported platforms
        # -------------------------------------------------

        allowed_platforms = {
            "linkedin",
            "instagram",
            "x",
        }

        platform = (
            data.platform or ""
        ).lower().strip()

        if platform not in allowed_platforms:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Scheduling is not supported for platform '{platform}'."
                ),
            )

        # -------------------------------------------------
        # Check that the post belongs to current user
        # -------------------------------------------------

        post_response = (
            db
            .table("posts")
            .select("*")
            .eq("id", data.post_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not post_response.data:
            raise HTTPException(
                status_code=404,
                detail="Post not found.",
            )

        post = post_response.data[0]



        # -------------------------------------------------
        # Post must have content
        # -------------------------------------------------

        if not post.get("caption"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Post content is empty. Generate the post before scheduling."
                ),
            )

        # -------------------------------------------------
        # Scheduled time must be timezone-aware and future
        # -------------------------------------------------

        scheduled_at = data.scheduled_at

        if scheduled_at.tzinfo is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "scheduled_at must include timezone information."
                ),
            )

        if scheduled_at <= datetime.now(
            scheduled_at.tzinfo
        ):
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be in the future.",
            )

        # -------------------------------------------------
        # Prevent duplicate schedule for the SAME
        # post + SAME platform.
        #
        # This intentionally does NOT block another
        # platform from using the same post_id.
        # -------------------------------------------------

        existing_response = (
            db
            .table("scheduled_posts")
            .select("id")
            .eq("user_id", user_id)
            .eq("post_id", data.post_id)
            .eq("platform", platform)
            .eq("status", "scheduled")
            .limit(1)
            .execute()
        )

        if existing_response.data:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"This post is already scheduled for {platform}."
                ),
            )

        # -------------------------------------------------
        # Save schedule
        # -------------------------------------------------

        schedule_data = {
            "user_id": user_id,
            "post_id": data.post_id,
            "platform": platform,
            "scheduled_at": scheduled_at.isoformat(),
            "status": "scheduled",
        }

        response = (
            db
            .table("scheduled_posts")
            .insert(schedule_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Scheduled post could not be created.",
            )

        scheduled_post = response.data[0]

        # -------------------------------------------------
        # Add APScheduler one-time job
        # -------------------------------------------------

        add_one_time_job(
            scheduled_post_id=scheduled_post["id"],
            scheduled_at=scheduled_at,
        )

        return {
            "message": "Post scheduled successfully.",
            "scheduled_post": scheduled_post,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# GET MY SCHEDULED POSTS
# =========================================================

@router.get("")
def get_scheduled_posts(
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        response = (
            db
            .table("scheduled_posts")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "scheduled")
            .order("scheduled_at", desc=False)
            .execute()
        )

        return {
            "scheduled_posts": response.data or [],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# CANCEL SCHEDULED POST
# =========================================================

@router.delete("/{scheduled_post_id}")
def cancel_scheduled_post(
    scheduled_post_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        response = (
            db
            .table("scheduled_posts")
            .update({
                "status": "cancelled",
            })
            .eq("id", scheduled_post_id)
            .eq("user_id", user_id)
            .eq("status", "scheduled")
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Scheduled post not found or already processed."
                ),
            )

        remove_one_time_job(
            scheduled_post_id
        )

        return {
            "message": "Scheduled post cancelled successfully.",
            "scheduled_post": response.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
