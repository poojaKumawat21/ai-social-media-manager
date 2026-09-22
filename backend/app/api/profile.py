from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.core.security import get_current_user, get_current_user_with_email
from app.database.supabase import supabase
from app.models.profile import ProfileCreate, ProfileUpdate


router = APIRouter(prefix="/profile", tags=["Profile"])


# =========================================================
# CREATE PROFILE
# =========================================================

@router.post("")
def create_profile(
    data: ProfileCreate,
    auth_user=Depends(get_current_user_with_email),
):
    try:
        # Check if profile already exists
        existing = (
            supabase
            .table("profiles")
            .select("*")
            .eq("user_id", auth_user["user_id"])
            .execute()
        )

        if existing.data:
            raise HTTPException(
                status_code=409,
                detail="Profile already exists",
            )

        # Email comes directly from authenticated Supabase user
        profile_data = {
            "user_id": auth_user["user_id"],
            "name": data.name,
            "email": auth_user["email"],
            "niche": data.niche,
            "language": data.language,
            "tone": data.tone,
        }

        response = (
            supabase
            .table("profiles")
            .insert(profile_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Profile creation failed",
            )

        return {
            "message": "Profile created successfully",
            "profile": response.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# =========================================================
# GET PROFILE
# =========================================================

@router.get("")
def get_profile(
    auth_user=Depends(get_current_user_with_email),
):
    try:
        response = (
            supabase
            .table("profiles")
            .select("*")
            .eq("user_id", auth_user["user_id"])
            .single()
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        profile = response.data

        # Automatically fix email if old profile has NULL email
        if not profile.get("email") and auth_user.get("email"):
            update_response = (
                supabase
                .table("profiles")
                .update({
                    "email": auth_user["email"]
                })
                .eq("user_id", auth_user["user_id"])
                .execute()
            )

            if update_response.data:
                profile = update_response.data[0]

        return {
            "profile": profile,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )


# =========================================================
# UPDATE PROFILE
# =========================================================

@router.put("")
def update_profile(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user),
):
    try:
        update_data = data.model_dump(exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No profile fields provided",
            )

        response = (
            supabase
            .table("profiles")
            .update(update_data)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        return {
            "message": "Profile updated successfully",
            "profile": response.data[0],
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# =========================================================
# UPLOAD AVATAR
# =========================================================

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    try:
        file_content = await file.read()

        file_extension = file.filename.split(".")[-1]
        file_path = f"{user_id}/avatar.{file_extension}"

        supabase.storage.from_("avatars").upload(
            file_path,
            file_content,
            {
                "content-type": file.content_type,
                "upsert": "true",
            },
        )

        avatar_url = supabase.storage.from_("avatars").get_public_url(
            file_path
        )

        response = (
            supabase
            .table("profiles")
            .update({
                "avatar_url": avatar_url
            })
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )