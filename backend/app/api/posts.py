from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.database.supabase import get_database_client
from app.services.ai_orchestrator import run_ai_pipeline
from app.models.post import PostUpdate


router = APIRouter(prefix="/posts", tags=["Posts"])


class GeneratePostRequest(BaseModel):
    topic: str
    description: str = ""


@router.post("/generate")
def generate_post(
    data: GeneratePostRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        # Create a fresh service-role database client
        db = get_database_client()

        # Validate topic
        if not data.topic.strip():
            raise HTTPException(
                status_code=400,
                detail="Topic is required",
            )

        # Get user's profile
        profile_response = (
            db
            .table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not profile_response.data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found. Please create your profile first.",
            )

        profile = profile_response.data

        # Get previous posts of this user
        previous_posts_response = (
            db
            .table("posts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )

        previous_posts = previous_posts_response.data or []

        previous_styles = [
            post.get("style")
            for post in previous_posts
            if post.get("style")
        ]

        # Run existing AI pipeline
        result = run_ai_pipeline(
            topic=data.topic,
            description=data.description,
            previous_styles=previous_styles,
            previous_posts=previous_posts,
        )

        # Extract AI results
        planner = result.get("planner") or {}
        style_data = result.get("style") or {}
        content = result.get("content") or {}
        research = result.get("research") or {}

        # Get uploaded images
        uploaded_images = result.get("uploaded_images") or []

        media_urls = [
            image.get("storage", {}).get("public_url")
            for image in uploaded_images
            if image.get("storage", {}).get("public_url")
        ]

        # Prepare post data
        post_data = {
            "user_id": user_id,
            "profile_id": profile.get("id"),

            "niche": planner.get(
                "niche",
                profile.get("niche"),
            ),

            "topic": data.topic,

            "caption": content.get(
                "caption",
                "",
            ),

            "hashtags": content.get(
                "hashtags",
                planner.get("hashtags", []),
            ),

            "post_idea": content.get(
                "post_idea",
                planner.get("post_idea", ""),
            ),

            "style": style_data.get(
                "style",
                planner.get("style", ""),
            ),

            "language": planner.get(
                "language",
                profile.get("language", "English"),
            ),

            "tone": planner.get(
                "tone",
                profile.get("tone", "Professional"),
            ),

            "news_title": research.get("title"),

            "news_source": research.get("source"),

            "status": "generated",

            "media_urls": media_urls,
        }

        # Save post using fresh service-role client
        save_response = (
            db
            .table("posts")
            .insert(post_data)
            .execute()
        )

        if not save_response.data:
            raise HTTPException(
                status_code=400,
                detail="Post generated but could not be saved.",
            )

        return {
            "message": "Post generated successfully",
            "post": save_response.data[0],
            "ai_result": result,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("")
def get_my_posts(
    user_id: str = Depends(get_current_user),
):
    try:
        # Create a fresh service-role database client
        db = get_database_client()

        response = (
            db
            .table("posts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "posts": response.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/{post_id}")
def get_post(
    post_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        response = (
            db
            .table("posts")
            .select("*")
            .eq("id", post_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Post not found",
            )

        return {
            "post": response.data
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Post not found",
        )


@router.put("/{post_id}")
def update_post(
    post_id: str,
    data: PostUpdate,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        update_data = data.model_dump(
            exclude_none=True
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update",
            )

        response = (
            db
            .table("posts")
            .update(update_data)
            .eq("id", post_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Post not found",
            )

        return {
            "message": "Post updated successfully",
            "post": response.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )