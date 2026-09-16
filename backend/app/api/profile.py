from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.database.supabase import supabase
from app.models.profile import ProfileCreate, ProfileUpdate


router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("")
def create_profile(
    data: ProfileCreate,
    user_id: str = Depends(get_current_user),
):
    try:
        # Check if profile already exists
        existing = (
            supabase
            .table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if existing.data:
            raise HTTPException(
                status_code=409,
                detail="Profile already exists",
            )

        # Get email from authenticated Supabase user
        # auth_user = supabase.auth.get_user(
        #     # The access token is handled by get_current_user.
        #     # Email is not required from the frontend.
        #     ""
        # )

        profile_data = {
            "user_id": user_id,
            "name": data.name,
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


@router.get("")
def get_profile(
    user_id: str = Depends(get_current_user),
):
    try:
        response = (
            supabase
            .table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found",
            )

        return {
            "profile": response.data,
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )


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