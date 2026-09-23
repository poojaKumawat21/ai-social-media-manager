from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.supabase_auth import supabase_auth

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: RegisterRequest):
    try:
        response = supabase_auth.auth.sign_up(
            {
                "email": data.email,
                "password": data.password,
            }
        )

        if not response.user:
            raise HTTPException(
                status_code=400,
                detail="Registration failed",
            )

        return {
            "message": "Registration successful",
            "user_id": response.user.id,
            "email": response.user.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post("/login")
def login(data: LoginRequest):
    try:
        response = supabase_auth.auth.sign_in_with_password(
            {
                "email": data.email,
                "password": data.password,
            }
        )

        if not response.user or not response.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        return {
            "message": "Login successful",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id,
            "email": response.user.email,
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest):
    try:
        response = supabase_auth.auth.refresh_session(
            data.refresh_token
        )

        if not response or not response.session:
            raise HTTPException(
                status_code=401,
                detail="Unable to refresh session",
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Unable to refresh session",
        )    


@router.post("/resend-confirmation")
def resend_confirmation(data: RegisterRequest):
    try:
        supabase_auth.auth.resend(
            {
                "type": "signup",
                "email": data.email,
            }
        )

        return {
            "message": "Confirmation email sent successfully",
            "email": data.email,
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not resend confirmation email",
        )
    