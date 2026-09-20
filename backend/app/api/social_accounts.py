from datetime import datetime, timedelta, timezone


import requests
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.database.supabase import get_database_client

from app.models.social_account import (
    SocialAccountCreate,
    SocialAccountUpdate,
)

from app.services.oauth_service import (
    generate_oauth_state,
    get_oauth_state_expiry,
    build_instagram_authorization_url,
    exchange_code_for_access_token,
    exchange_for_long_lived_token,
)

from app.services.linkedin_oauth_service import (
    generate_linkedin_oauth_state,
    get_linkedin_state_expiry,
    build_linkedin_authorization_url,
    exchange_linkedin_code_for_access_token,
)


router = APIRouter(
    prefix="/social-accounts",
    tags=["Social Accounts"],
)


# =========================================================
# HELPER: PARSE OAUTH EXPIRY
# =========================================================

def parse_oauth_expiry(value) -> datetime:
    """
    Safely parse Supabase OAuth expiry timestamps.

    Supports:
    2026-09-19T13:43:29.06575+00:00
    2026-09-19T13:43:29+00:00
    2026-09-19T13:43:29Z
    """

    if not value:
        raise ValueError(
            "OAuth state expiry is missing."
        )

    # Supabase may already return datetime
    if isinstance(value, datetime):

        expiry = value

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        return expiry.astimezone(timezone.utc)

    value = str(value).strip()

    if not value:
        raise ValueError(
            "OAuth state expiry is empty."
        )

    # Convert UTC Z format
    normalized_value = value.replace(
        "Z",
        "+00:00",
    )

    # Try normal ISO parser first
    try:

        expiry = datetime.fromisoformat(
            normalized_value
        )

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        return expiry.astimezone(
            timezone.utc
        )

    except ValueError:
        pass

    # Fallback formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:

        try:

            expiry = datetime.strptime(
                normalized_value,
                fmt,
            )

            if expiry.tzinfo is None:
                expiry = expiry.replace(
                    tzinfo=timezone.utc
                )

            return expiry.astimezone(
                timezone.utc
            )

        except ValueError:
            continue

    raise ValueError(
        f"Invalid OAuth expiry timestamp: {value}"
    )


# =========================================================
# CONNECT / SAVE SOCIAL ACCOUNT
# =========================================================

@router.post("")
def create_social_account(
    data: SocialAccountCreate,
    user_id: str = Depends(get_current_user),
):
    try:

        db = get_database_client()

        platform = data.platform.strip().lower()

        if not platform:
            raise HTTPException(
                status_code=400,
                detail="Platform is required.",
            )

        allowed_platforms = {
            "instagram",
            "linkedin",
            "whatsapp",
        }

        if platform not in allowed_platforms:
            raise HTTPException(
                status_code=400,
                detail="Unsupported social platform.",
            )

        # -------------------------------------------------
        # Check existing connection
        # -------------------------------------------------

        existing = (
            db.table("social_accounts")
            .select("id")
            .eq("user_id", user_id)
            .eq("platform", platform)
            .execute()
        )

        if existing.data:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{platform.title()} account "
                    "is already connected."
                ),
            )

        # -------------------------------------------------
        # Prepare account data
        # -------------------------------------------------

        account_data = {
            "user_id": user_id,
            "platform": platform,
            "platform_user_id": data.platform_user_id,
            "account_name": data.account_name,
            "access_token": data.access_token,
            "refresh_token": data.refresh_token,
            "token_expires_at": (
                data.token_expires_at.isoformat()
                if data.token_expires_at
                else None
            ),
            "scopes": data.scopes,
            "status": "connected",
        }

        response = (
            db.table("social_accounts")
            .insert(account_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Social account could not "
                    "be connected."
                ),
            )

        account = response.data[0]

        # NEVER expose OAuth tokens
        account.pop(
            "access_token",
            None,
        )

        account.pop(
            "refresh_token",
            None,
        )

        return {
            "message": (
                "Social account connected successfully."
            ),
            "account": account,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# GET CONNECTED ACCOUNTS
# =========================================================

@router.get("")
def get_social_accounts(
    user_id: str = Depends(get_current_user),
):
    try:

        db = get_database_client()

        response = (
            db.table("social_accounts")
            .select(
                "id, platform, platform_user_id, "
                "account_name, token_expires_at, "
                "scopes, status, created_at, updated_at"
            )
            .eq(
                "user_id",
                user_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return {
            "accounts": response.data or []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# GET SINGLE CONNECTED ACCOUNT
# =========================================================

@router.get("/{account_id}")
def get_social_account(
    account_id: str,
    user_id: str = Depends(get_current_user),
):
    try:

        db = get_database_client()

        response = (
            db.table("social_accounts")
            .select(
                "id, platform, platform_user_id, "
                "account_name, token_expires_at, "
                "scopes, status, created_at, updated_at"
            )
            .eq(
                "id",
                account_id,
            )
            .eq(
                "user_id",
                user_id,
            )
            .single()
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Social account not found.",
            )

        return {
            "account": response.data
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Social account not found.",
        )


# =========================================================
# UPDATE SOCIAL ACCOUNT
# =========================================================

@router.put("/{account_id}")
def update_social_account(
    account_id: str,
    data: SocialAccountUpdate,
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
                detail="No fields provided for update.",
            )

        if "token_expires_at" in update_data:

            expiry = update_data[
                "token_expires_at"
            ]

            if expiry:

                update_data[
                    "token_expires_at"
                ] = expiry.isoformat()

        response = (
            db.table("social_accounts")
            .update(update_data)
            .eq(
                "id",
                account_id,
            )
            .eq(
                "user_id",
                user_id,
            )
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Social account not found.",
            )

        account = response.data[0]

        # NEVER expose OAuth tokens
        account.pop(
            "access_token",
            None,
        )

        account.pop(
            "refresh_token",
            None,
        )

        return {
            "message": (
                "Social account updated successfully."
            ),
            "account": account,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# DISCONNECT SOCIAL ACCOUNT
# =========================================================

@router.delete("/{account_id}")
def disconnect_social_account(
    account_id: str,
    user_id: str = Depends(get_current_user),
):
    try:

        db = get_database_client()

        response = (
            db.table("social_accounts")
            .delete()
            .eq(
                "id",
                account_id,
            )
            .eq(
                "user_id",
                user_id,
            )
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Social account not found.",
            )

        return {
            "message": (
                "Social account disconnected successfully."
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# START INSTAGRAM OAUTH
# =========================================================

@router.get("/oauth/instagram/start")
def start_instagram_oauth(
    user_id: str = Depends(get_current_user),
):
    try:

        db = get_database_client()

        # -------------------------------------------------
        # Generate secure state
        # -------------------------------------------------

        state = generate_oauth_state()

        expires_at = get_oauth_state_expiry(
            minutes=10
        )

        # -------------------------------------------------
        # Save state
        # -------------------------------------------------

        state_response = (
            db.table("oauth_states")
            .insert(
                {
                    "user_id": user_id,
                    "platform": "instagram",
                    "state": state,
                    "expires_at": expires_at,
                    "used": False,
                }
            )
            .execute()
        )

        if not state_response.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not create OAuth state."
                ),
            )

        # -------------------------------------------------
        # Build authorization URL
        # -------------------------------------------------

        authorization_url = (
            build_instagram_authorization_url(
                state=state
            )
        )

        return {
            "message": (
                "Instagram OAuth started."
            ),
            "authorization_url": authorization_url,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =========================================================
# INSTAGRAM OAUTH CALLBACK
# =========================================================

@router.get("/oauth/instagram/callback")
def instagram_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    try:

        # =================================================
        # 1. INSTAGRAM RETURNED AN ERROR
        # =================================================

        if error:

            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Instagram OAuth failed."
                    ),
                    "error": error,
                    "error_description": (
                        error_description
                    ),
                },
            )

        # =================================================
        # 2. VALIDATE CODE
        # =================================================

        if not code:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Authorization code is missing."
                ),
            )

        # =================================================
        # 3. VALIDATE STATE
        # =================================================

        if not state:

            raise HTTPException(
                status_code=400,
                detail="OAuth state is missing.",
            )

        db = get_database_client()

        # =================================================
        # 4. FIND OAUTH STATE
        # =================================================

        response = (
            db.table("oauth_states")
            .select(
                "id, user_id, platform, state, "
                "expires_at, used"
            )
            .eq(
                "state",
                state,
            )
            .eq(
                "platform",
                "instagram",
            )
            .single()
            .execute()
        )

        oauth_state = response.data

        if not oauth_state:

            raise HTTPException(
                status_code=400,
                detail="Invalid OAuth state.",
            )

        # =================================================
        # 5. PREVENT STATE REUSE
        # =================================================

        if oauth_state.get("used"):

            raise HTTPException(
                status_code=400,
                detail=(
                    "OAuth state has already been used."
                ),
            )

        # =================================================
        # 6. CHECK STATE EXPIRATION
        # =================================================

        expires_at_value = (
            oauth_state.get("expires_at")
        )

        try:

            expires_at = parse_oauth_expiry(
                expires_at_value
            )

        except ValueError as e:

            raise HTTPException(
                status_code=500,
                detail=str(e),
            )

        now = datetime.now(
            timezone.utc
        )

        if expires_at <= now:

            raise HTTPException(
                status_code=400,
                detail=(
                    "OAuth state has expired."
                ),
            )

# =================================================
# 7. EXCHANGE AUTHORIZATION CODE
# =================================================

        try:

            token_data = (
        exchange_code_for_access_token(
            code=code
        )
    )

        except Exception as e:

            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Instagram token exchange failed."
                    ),
                    "error": str(e),
                },
            )

        # =================================================
        # 9. GET SHORT-LIVED ACCESS TOKEN
        # =================================================

        short_lived_token = (
            token_data.get("access_token")
        )

        if not short_lived_token:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Instagram access token "
                    "was not returned."
                ),
            )

        # =================================================
        # 10. EXCHANGE FOR LONG-LIVED TOKEN
        # =================================================

        try:

            long_lived_data = (
                exchange_for_long_lived_token(
                    access_token=short_lived_token
                )
            )

        except Exception as e:

            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Instagram long-lived token "
                        "exchange failed."
                    ),
                    "error": str(e),
                },
            )

        access_token = (
            long_lived_data.get(
                "access_token"
            )
        )

        if not access_token:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Long-lived Instagram token "
                    "was not returned."
                ),
            )

        # =================================================
        # 11. GET INSTAGRAM USER ID
        # =================================================

        instagram_user_id = (
            long_lived_data.get("user_id")
            or token_data.get("user_id")
        )

        if not instagram_user_id:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Instagram user ID "
                    "was not returned."
                ),
            )

        instagram_user_id = str(
            instagram_user_id
        )

        # =================================================
        # 12. GET INSTAGRAM USERNAME
        # =================================================

        username = None

        try:

            profile_response = requests.get(
                (
                    "https://graph.instagram.com/"
                    f"{instagram_user_id}"
                ),
                params={
                    "fields": "id,username",
                    "access_token": access_token,
                },
                timeout=30,
            )

            if profile_response.ok:

                profile_data = (
                    profile_response.json()
                )

                username = (
                    profile_data.get(
                        "username"
                    )
                )

        except Exception:

            # Username lookup failure should
            # not prevent account connection.
            username = None

        # =================================================
        # 13. CALCULATE TOKEN EXPIRY
        # =================================================

        expires_in = (
            long_lived_data.get(
                "expires_in"
            )
        )

        token_expires_at = None

        if expires_in:

            try:

                token_expires_at = (
                    datetime.now(
                        timezone.utc
                    )
                    + timedelta(
                        seconds=int(
                            expires_in
                        )
                    )
                ).isoformat()

            except (
                TypeError,
                ValueError,
            ):

                token_expires_at = None

        # =================================================
        # 14. CHECK EXISTING INSTAGRAM ACCOUNT
        # =================================================

        existing_account = (
            db.table("social_accounts")
            .select("id")
            .eq(
                "user_id",
                oauth_state["user_id"],
            )
            .eq(
                "platform",
                "instagram",
            )
            .execute()
        )

        # =================================================
        # 15. PREPARE ACCOUNT DATA
        # =================================================

        account_data = {
            "user_id": (
                oauth_state["user_id"]
            ),
            "platform": "instagram",
            "platform_user_id": (
                instagram_user_id
            ),
            "account_name": username,
            "access_token": access_token,
            "refresh_token": None,
            "token_expires_at": (
                token_expires_at
            ),
            "scopes": [
                "instagram_business_basic",
                "instagram_business_content_publish",
            ],
            "status": "connected",
            "updated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        }

        # =================================================
        # 16. SAVE / UPDATE ACCOUNT
        # =================================================

        if existing_account.data:

            account_id = (
                existing_account.data[0]["id"]
            )

            update_response = (
                db.table("social_accounts")
                .update(account_data)
                .eq(
                    "id",
                    account_id,
                )
                .eq(
                    "user_id",
                    oauth_state["user_id"],
                )
                .execute()
            )

            if not update_response.data:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Instagram account "
                        "could not be updated."
                    ),
                )

        else:

            insert_response = (
                db.table("social_accounts")
                .insert(account_data)
                .execute()
            )

            if not insert_response.data:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Instagram account "
                        "could not be saved."
                    ),
                )

        # =================================================
        # 17. MARK OAUTH STATE USED
        # =================================================

        db.table("oauth_states").update(
            {
                "used": True,
            }
        ).eq(
            "id",
            oauth_state["id"],
        ).execute()

        # =================================================
        # 18. SUCCESS
        # =================================================

        return {
            "message": (
                "Instagram connected successfully."
            ),
            "platform": "instagram",
            "instagram_user_id": (
                instagram_user_id
            ),
            "account_name": username,
            "status": "connected",
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

# =========================================================
# START LINKEDIN OAUTH
# =========================================================

@router.get("/oauth/linkedin/start")
def start_linkedin_oauth(
    user_id: str = Depends(get_current_user),
):
    try:

        db = get_database_client()

        # -------------------------------------------------
        # Generate secure LinkedIn OAuth state
        # -------------------------------------------------

        state = generate_linkedin_oauth_state()

        expires_at = get_linkedin_state_expiry(
            minutes=10
        )

        # -------------------------------------------------
        # Save state
        # -------------------------------------------------

        state_response = (
            db.table("linkedin_oauth_states")
            .insert(
                {
                    "user_id": user_id,
                    "state": state,
                    "expires_at": expires_at,
                    "used": False,
                }
            )
            .execute()
        )

        if not state_response.data:
            raise HTTPException(
                status_code=500,
                detail="Could not create LinkedIn OAuth state.",
            )

        # -------------------------------------------------
        # Build LinkedIn authorization URL
        # -------------------------------------------------

        authorization_url = (
            build_linkedin_authorization_url(
                state=state
            )
        )

        return {
            "message": "LinkedIn OAuth started.",
            "authorization_url": authorization_url,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

# =========================================================
# LINKEDIN OAUTH CALLBACK
# =========================================================

@router.get("/oauth/linkedin/callback")
def linkedin_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
):
    try:

        # -------------------------------------------------
        # LinkedIn returned an OAuth error
        # -------------------------------------------------

        if error:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "LinkedIn authorization failed.",
                    "error": error,
                    "error_description": error_description,
                },
            )

        # -------------------------------------------------
        # Validate callback parameters
        # -------------------------------------------------

        if not code:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn authorization code is missing.",
            )

        if not state:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn OAuth state is missing.",
            )

        # -------------------------------------------------
        # Database
        # -------------------------------------------------

        db = get_database_client()

        # -------------------------------------------------
        # Find OAuth state
        # -------------------------------------------------

        state_response = (
            db.table("linkedin_oauth_states")
            .select("*")
            .eq("state", state)
            .eq("used", False)
            .limit(1)
            .execute()
        )

        if not state_response.data:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired LinkedIn OAuth state.",
            )

        oauth_state = state_response.data[0]

        # -------------------------------------------------
        # Check expiry
        # -------------------------------------------------

        expires_at = oauth_state.get("expires_at")

        if expires_at:
            expires_at_dt = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expires_at_dt < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="LinkedIn OAuth state has expired.",
                )

        user_id = oauth_state["user_id"]

        # -------------------------------------------------
        # Mark state as used
        # -------------------------------------------------

        (
            db.table("linkedin_oauth_states")
            .update({"used": True})
            .eq("id", oauth_state["id"])
            .execute()
        )

        # -------------------------------------------------
        # Exchange code for access token
        # -------------------------------------------------

        token_data = exchange_linkedin_code_for_access_token(
            code
        )

        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn access token was not returned.",
            )

        # -------------------------------------------------
        # Get LinkedIn profile information
        # -------------------------------------------------

        profile_response = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=30,
        )

        if not profile_response.ok:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Could not fetch LinkedIn profile.",
                    "response": profile_response.text,
                },
            )

        profile_data = profile_response.json()

        linkedin_user_id = profile_data.get("sub")
        name = profile_data.get("name")

        if not linkedin_user_id:
            raise HTTPException(
                status_code=400,
                detail="LinkedIn user ID was not returned.",
            )

        # -------------------------------------------------
        # Token expiry
        # -------------------------------------------------

        expires_in = token_data.get("expires_in")

        token_expires_at = None

        if expires_in:
            token_expires_at = (
                datetime.now(timezone.utc)
                + timedelta(seconds=int(expires_in))
            ).isoformat()

        # -------------------------------------------------
        # Save / update LinkedIn account
        # -------------------------------------------------

        existing_account = (
            db.table("social_accounts")
            .select("id")
            .eq("user_id", user_id)
            .eq("platform", "linkedin")
            .limit(1)
            .execute()
        )

        account_data = {
            "user_id": user_id,
            "platform": "linkedin",
            "platform_user_id": linkedin_user_id,
            "account_name": name or "LinkedIn Account",
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": token_expires_at,
            "scopes": [
                "openid",
                "profile",
                "email",
                "w_member_social",
            ],
            "status": "connected",
        }

        if existing_account.data:

            (
                db.table("social_accounts")
                .update(account_data)
                .eq("id", existing_account.data[0]["id"])
                .execute()
            )

        else:

            (
                db.table("social_accounts")
                .insert(account_data)
                .execute()
            )

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        return {
            "message": "LinkedIn account connected successfully.",
            "platform": "linkedin",
            "platform_user_id": linkedin_user_id,
            "account_name": name or "LinkedIn Account",
            "status": "connected",
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )