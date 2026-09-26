from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.database.supabase import get_database_client
from app.services.ai_orchestrator import run_ai_pipeline
from app.models.post import PostUpdate

from app.services.linkedin_publish_service import (
    publish_linkedin_text_post,
    publish_linkedin_multi_image_post,
)

from app.services.instagram_publish_service import (
    publish_instagram_image_post,
)


router = APIRouter(prefix="/posts", tags=["Posts"])


# =========================================================
# REQUEST MODELS
# =========================================================

class GeneratePostRequest(BaseModel):
    topic: str
    description: str = ""
    platforms: list[str]


class SaveDraftRequest(BaseModel):
    topic: str = ""
    description: str = ""


# =========================================================
# SAVE DRAFT
# =========================================================

@router.post("/draft")
def save_draft(
    data: SaveDraftRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        if not data.topic.strip():
            raise HTTPException(
                status_code=400,
                detail="Topic is required to save a draft.",
            )

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

        draft_data = {
            "user_id": user_id,
            "profile_id": profile.get("id"),
            "niche": profile.get("niche", ""),
            "topic": data.topic.strip(),
            "caption": data.description.strip(),
            "hashtags": [],
            "post_idea": "",
            "style": "",
            "language": profile.get("language", "English"),
            "tone": profile.get("tone", "Professional"),
            "status": "draft",
            "media_urls": [],
            "platforms": [],
            "platform_variants": {},
            "platform_status": {},
        }

        response = (
            db
            .table("posts")
            .insert(draft_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Draft could not be saved.",
            )

        return {
            "message": "Draft saved successfully.",
            "post": response.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# GENERATE ONE POST FOR MULTIPLE PLATFORMS
# =========================================================

@router.post("/generate")
def generate_post(
    data: GeneratePostRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        # -------------------------------------------------
        # VALIDATE TOPIC
        # -------------------------------------------------

        if not data.topic.strip():
            raise HTTPException(
                status_code=400,
                detail="Topic is required.",
            )

        # -------------------------------------------------
        # VALIDATE PLATFORMS
        # -------------------------------------------------

        allowed_platforms = {
            "instagram",
            "linkedin",
            "facebook",
            "x",
        }

        platforms = [
            platform.strip().lower()
            for platform in data.platforms
            if platform and platform.strip()
        ]

        if not platforms:
            raise HTTPException(
                status_code=400,
                detail="At least one platform must be selected.",
            )

        invalid_platforms = [
            platform
            for platform in platforms
            if platform not in allowed_platforms
        ]

        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Unsupported platform selected.",
                    "invalid_platforms": invalid_platforms,
                    "allowed_platforms": sorted(allowed_platforms),
                },
            )

        # Remove duplicate platform selections
        platforms = list(dict.fromkeys(platforms))

        # -------------------------------------------------
        # GET USER PROFILE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # GET PREVIOUS POSTS
        # -------------------------------------------------

        previous_posts_response = (
            db
            .table("posts")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        previous_posts = previous_posts_response.data or []

        previous_styles = [
            post.get("style")
            for post in previous_posts
            if post.get("style")
        ]

        # =================================================
        # IMPORTANT
        # =================================================
        # ONE topic = ONE AI PIPELINE
        #
        # We DO NOT call run_ai_pipeline() inside a
        # platform loop.
        #
        # This prevents:
        #
        # Instagram -> full AI pipeline
        # LinkedIn  -> full AI pipeline again
        #
        # from consuming the Groq quota twice.
        # =================================================

        selected_platform_text = ", ".join(
            platform.upper()
            for platform in platforms
        )

        generation_description = f"""
{data.description.strip()}

IMPORTANT:

The user selected these platforms:
{selected_platform_text}

Generate ONE strong core social-media post based on the topic.

The generated content will be stored under ONE parent post
and reused for the selected social platforms.

Keep the content:
- clear
- engaging
- useful
- natural
- easy to adapt for social media
- consistent with the user's profile
"""

        # -------------------------------------------------
        # ONE AI PIPELINE CALL ONLY
        # -------------------------------------------------

        try:
            result = run_ai_pipeline(
                topic=data.topic,
                description=generation_description,
                previous_styles=previous_styles,
                previous_posts=previous_posts,
                platform="general",
            )

        except Exception as e:
            error_text = str(e)

            # -------------------------------------------------
            # GROQ RATE LIMIT
            # -------------------------------------------------

            if (
                "429" in error_text
                or "rate_limit_exceeded" in error_text
                or "tokens per day" in error_text
                or "TPD" in error_text
            ):
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "AI generation rate limit reached.",
                        "provider": "groq",
                        "detail": error_text,
                        "hint": (
                            "Please wait until the Groq token quota "
                            "resets or increase the provider quota."
                        ),
                    },
                )

            # -------------------------------------------------
            # HUGGING FACE / IMAGE PROVIDER PAYMENT
            # -------------------------------------------------

            if (
                "402" in error_text
                and (
                    "huggingface" in error_text.lower()
                    or "inference" in error_text.lower()
                    or "credits" in error_text.lower()
                )
            ):
                raise HTTPException(
                    status_code=402,
                    detail={
                        "message": "AI image generation credits are exhausted.",
                        "provider": "huggingface",
                        "detail": error_text,
                        "hint": (
                            "Add image-generation credits or configure "
                            "another image provider."
                        ),
                    },
                )

            # -------------------------------------------------
            # OTHER AI ERROR
            # -------------------------------------------------

            raise HTTPException(
                status_code=500,
                detail={
                    "message": "AI generation failed.",
                    "detail": error_text,
                },
            )

        # -------------------------------------------------
        # READ AI RESULT
        # -------------------------------------------------

        planner = result.get("planner") or {}
        style_data = result.get("style") or {}
        content = result.get("content") or {}
        research = result.get("research") or {}

        uploaded_images = result.get("uploaded_images") or []

        # -------------------------------------------------
        # EXTRACT MEDIA URLS
        # -------------------------------------------------

        media_urls = []

        for image in uploaded_images:
            storage = image.get("storage") or {}

            public_url = storage.get("public_url")

            if public_url:
                media_urls.append(public_url)

        # -------------------------------------------------
        # COMMON GENERATED CONTENT
        # -------------------------------------------------

        common_variant = {
            "topic": data.topic,

            "niche": planner.get(
                "inferred_niche",
                profile.get("niche"),
            ),

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

            "media_urls": media_urls,

            "status": "generated",
        }

        # =================================================
        # CREATE PLATFORM VARIANTS
        # =================================================
        #
        # IMPORTANT:
        #
        # We do NOT call the AI again here.
        #
        # Every selected platform gets a variant under
        # the same parent post.
        #
        # This keeps ONE generation and ONE post_id.
        # =================================================

        platform_variants = {}
        platform_status = {}

        for platform in platforms:

            platform_variants[platform] = {
                "platform": platform,

                "niche": common_variant["niche"],

                "topic": common_variant["topic"],

                "caption": common_variant["caption"],

                "hashtags": common_variant["hashtags"],

                "post_idea": common_variant["post_idea"],

                "style": common_variant["style"],

                "language": common_variant["language"],

                "tone": common_variant["tone"],

                "news_title": common_variant["news_title"],

                "news_source": common_variant["news_source"],

                "media_urls": common_variant["media_urls"],

                "status": "generated",
            }

            platform_status[platform] = "pending"

        # -------------------------------------------------
        # FIRST PLATFORM
        # -------------------------------------------------
        #
        # Keep existing top-level fields for backward
        # compatibility with the current frontend/database.
        # -------------------------------------------------

        first_platform = platforms[0]

        first_variant = platform_variants[first_platform]

        # -------------------------------------------------
        # CREATE ONE SINGLE POST ROW
        # -------------------------------------------------

        post_data = {
            "user_id": user_id,

            "profile_id": profile.get("id"),

            # Backward compatibility
            "platform": first_platform,

            # New multi-platform structure
            "platforms": platforms,

            "platform_variants": platform_variants,

            "platform_status": platform_status,

            # Existing fields
            "niche": first_variant.get(
                "niche",
                profile.get("niche"),
            ),

            "topic": data.topic,

            "caption": first_variant.get(
                "caption",
                "",
            ),

            "hashtags": first_variant.get(
                "hashtags",
                [],
            ),

            "post_idea": first_variant.get(
                "post_idea",
                "",
            ),

            "style": first_variant.get(
                "style",
                "",
            ),

            "language": first_variant.get(
                "language",
                profile.get("language", "English"),
            ),

            "tone": first_variant.get(
                "tone",
                profile.get("tone", "Professional"),
            ),

            "news_title": first_variant.get(
                "news_title"
            ),

            "news_source": first_variant.get(
                "news_source"
            ),

            "status": "generated",

            "media_urls": first_variant.get(
                "media_urls",
                [],
            ),
        }

        # -------------------------------------------------
        # SAVE ONLY ONE ROW
        # -------------------------------------------------

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

        saved_post = save_response.data[0]

        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------

        return {
            "message": "One post generated for all selected platforms.",

            "topic": data.topic,

            "post_id": saved_post.get("id"),

            "platforms": platforms,

            "post": saved_post,

            "platform_variants": platform_variants,

            "platform_status": platform_status,

            # Keep AI result for backward compatibility/debugging
            "ai_result": result,
        }

    except HTTPException:
        raise

    except Exception as e:
        error_text = str(e)

        if (
            "429" in error_text
            or "rate_limit_exceeded" in error_text
            or "tokens per day" in error_text
            or "TPD" in error_text
        ):
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "AI generation rate limit reached.",
                    "provider": "groq",
                    "detail": error_text,
                },
            )

        raise HTTPException(
            status_code=500,
            detail=error_text,
        )


# =========================================================
# GET ALL POSTS
# =========================================================

@router.get("")
def get_my_posts(
    user_id: str = Depends(get_current_user),
):
    try:
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


# =========================================================
# GET SINGLE POST
# =========================================================

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


# =========================================================
# DELETE POST
# =========================================================

@router.delete("/{post_id}")
def delete_post(
    post_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        response = (
            db
            .table("posts")
            .delete()
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
            "message": "Post deleted successfully.",
            "post_id": post_id,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# UPDATE POST
# =========================================================

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


# =========================================================
# PUBLISH ONE POST TO LINKEDIN
# =========================================================

@router.post("/{post_id}/publish/linkedin")
def publish_post_to_linkedin(
    post_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        # -------------------------------------------------
        # GET POST
        # -------------------------------------------------

        post_response = (
            db
            .table("posts")
            .select("*")
            .eq("id", post_id)
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
        # CHECK LINKEDIN WAS SELECTED
        # -------------------------------------------------

        platforms = post.get("platforms") or []

        if "linkedin" not in platforms:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn was not selected for this post.",
            )

        # -------------------------------------------------
        # GET LINKEDIN VARIANT
        # -------------------------------------------------

        platform_variants = post.get(
            "platform_variants"
        ) or {}

        linkedin_variant = platform_variants.get(
            "linkedin"
        )

        if not linkedin_variant:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn content is not available for this post.",
            )

        # -------------------------------------------------
        # GET LINKEDIN ACCOUNT
        # -------------------------------------------------

        account_response = (
            db
            .table("social_accounts")
            .select("*")
            .eq("user_id", user_id)
            .eq("platform", "linkedin")
            .eq("status", "connected")
            .limit(1)
            .execute()
        )

        if not account_response.data:
            raise HTTPException(
                status_code=404,
                detail="LinkedIn account is not connected.",
            )

        linkedin_account = account_response.data[0]

        access_token = linkedin_account.get(
            "access_token"
        )

        author_id = linkedin_account.get(
            "platform_user_id"
        )

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn access token is missing.",
            )

        if not author_id:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn profile ID is missing.",
            )

        # -------------------------------------------------
        # GET CAPTION
        # -------------------------------------------------

        caption = linkedin_variant.get(
            "caption"
        ) or ""

        if not caption.strip():
            raise HTTPException(
                status_code=400,
                detail="LinkedIn post caption is empty.",
            )

        # -------------------------------------------------
        # ADD HASHTAGS
        # -------------------------------------------------

        hashtags = linkedin_variant.get(
            "hashtags"
        ) or []

        if hashtags:
            hashtag_text = " ".join(
                hashtag
                if str(hashtag).startswith("#")
                else f"#{hashtag}"
                for hashtag in hashtags
            )

            caption = (
                f"{caption.strip()}\n\n"
                f"{hashtag_text}"
            )

        # -------------------------------------------------
        # GET MEDIA
        # -------------------------------------------------

        media_urls = linkedin_variant.get(
            "media_urls"
        ) or []

        # -------------------------------------------------
        # PUBLISH
        # -------------------------------------------------

        if len(media_urls) >= 2:

            result = publish_linkedin_multi_image_post(
                access_token=access_token,
                author_id=author_id,
                text=caption,
                image_urls=media_urls,
            )

        elif len(media_urls) == 1:

            result = publish_linkedin_text_post(
                access_token=access_token,
                author_id=author_id,
                text=caption,
                image_url=media_urls[0],
            )

        else:

            result = publish_linkedin_text_post(
                access_token=access_token,
                author_id=author_id,
                text=caption,
            )

        # -------------------------------------------------
        # UPDATE ONLY LINKEDIN STATUS
        # -------------------------------------------------

        platform_status = (
            post.get("platform_status")
            or {}
        )

        platform_status["linkedin"] = "published"

        db.table("posts").update({
            "platform_status": platform_status,
        }).eq(
            "id",
            post_id,
        ).eq(
            "user_id",
            user_id,
        ).execute()

        return {
            "message": "Post published to LinkedIn successfully.",
            "platform": "linkedin",
            "post_id": post_id,
            "linkedin_post_id": result.get(
                "post_id"
            ),
            "status": "published",
            "platform_status": platform_status,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# PUBLISH ONE POST TO INSTAGRAM
# =========================================================

@router.post("/{post_id}/publish/instagram")
def publish_post_to_instagram(
    post_id: str,
    user_id: str = Depends(get_current_user),
):
    try:
        db = get_database_client()

        # -------------------------------------------------
        # GET POST
        # -------------------------------------------------

        post_response = (
            db
            .table("posts")
            .select("*")
            .eq("id", post_id)
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
        # CHECK INSTAGRAM WAS SELECTED
        # -------------------------------------------------

        platforms = post.get("platforms") or []

        if "instagram" not in platforms:
            raise HTTPException(
                status_code=400,
                detail="Instagram was not selected for this post.",
            )

        # -------------------------------------------------
        # GET INSTAGRAM VARIANT
        # -------------------------------------------------

        platform_variants = (
            post.get("platform_variants")
            or {}
        )

        instagram_variant = platform_variants.get(
            "instagram"
        )

        if not instagram_variant:
            raise HTTPException(
                status_code=400,
                detail="Instagram content is not available for this post.",
            )

        # -------------------------------------------------
        # GET INSTAGRAM ACCOUNT
        # -------------------------------------------------

        account_response = (
            db
            .table("social_accounts")
            .select("*")
            .eq("user_id", user_id)
            .eq("platform", "instagram")
            .eq("status", "connected")
            .limit(1)
            .execute()
        )

        if not account_response.data:
            raise HTTPException(
                status_code=404,
                detail="Instagram account is not connected.",
            )

        instagram_account = account_response.data[0]

        access_token = instagram_account.get(
            "access_token"
        )

        instagram_user_id = instagram_account.get(
            "platform_user_id"
        )

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Instagram access token is missing.",
            )

        if not instagram_user_id:
            raise HTTPException(
                status_code=400,
                detail="Instagram user ID is missing.",
            )

        # -------------------------------------------------
        # GET CAPTION
        # -------------------------------------------------

        caption = instagram_variant.get(
            "caption"
        ) or ""

        if not caption.strip():
            raise HTTPException(
                status_code=400,
                detail="Instagram post caption is empty.",
            )

        # -------------------------------------------------
        # ADD HASHTAGS
        # -------------------------------------------------

        hashtags = instagram_variant.get(
            "hashtags"
        ) or []

        if hashtags:
            hashtag_text = " ".join(
                hashtag
                if str(hashtag).startswith("#")
                else f"#{hashtag}"
                for hashtag in hashtags
            )

            caption = (
                f"{caption.strip()}\n\n"
                f"{hashtag_text}"
            )

        # -------------------------------------------------
        # GET IMAGE
        # -------------------------------------------------

        media_urls = instagram_variant.get(
            "media_urls"
        ) or []

        if not media_urls:
            raise HTTPException(
                status_code=400,
                detail="Instagram post does not contain an image.",
            )

        image_url = media_urls[0]

        # -------------------------------------------------
        # PUBLISH
        # -------------------------------------------------

        result = publish_instagram_image_post(
            instagram_user_id=instagram_user_id,
            access_token=access_token,
            image_url=image_url,
            caption=caption,
        )

        # -------------------------------------------------
        # UPDATE ONLY INSTAGRAM STATUS
        # -------------------------------------------------

        platform_status = (
            post.get("platform_status")
            or {}
        )

        platform_status["instagram"] = "published"

        db.table("posts").update({
            "platform_status": platform_status,
        }).eq(
            "id",
            post_id,
        ).eq(
            "user_id",
            user_id,
        ).execute()

        return {
            "message": "Post published to Instagram successfully.",
            "platform": "instagram",
            "post_id": post_id,
            "instagram_media_id": result.get(
                "media_id"
            ),
            "status": "published",
            "platform_status": platform_status,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )