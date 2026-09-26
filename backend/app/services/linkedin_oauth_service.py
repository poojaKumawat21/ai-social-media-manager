import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# LINKEDIN CONFIGURATION
# =========================================================

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

LINKEDIN_REDIRECT_URI = os.getenv(
    "LINKEDIN_REDIRECT_URI",
    "http://127.0.0.1:8000/social-accounts/oauth/linkedin/callback",
).strip()


# LinkedIn OAuth endpoints
LINKEDIN_AUTHORIZATION_URL = (
    "https://www.linkedin.com/oauth/v2/authorization"
)

LINKEDIN_TOKEN_URL = (
    "https://www.linkedin.com/oauth/v2/accessToken"
)


# =========================================================
# LINKEDIN SCOPES
# =========================================================

LINKEDIN_SCOPES = os.getenv(
    "LINKEDIN_SCOPES",
    "openid profile email w_member_social",
).split()


# =========================================================
# OAUTH STATE
# =========================================================

def generate_linkedin_oauth_state() -> str:
    """
    Generate a cryptographically secure OAuth state.
    """

    return secrets.token_urlsafe(32)


def get_linkedin_state_expiry(minutes: int = 10) -> str:
    """
    Return OAuth state expiry in UTC ISO format.
    """

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=minutes)
    )

    return expires_at.isoformat()


# =========================================================
# REDIRECT URI
# =========================================================

def get_linkedin_redirect_uri() -> str:
    """
    Return the canonical LinkedIn redirect URI.
    """

    redirect_uri = LINKEDIN_REDIRECT_URI.strip()

    if not redirect_uri:
        raise RuntimeError(
            "LINKEDIN_REDIRECT_URI is not configured."
        )

    return redirect_uri


# =========================================================
# CONFIG VALIDATION
# =========================================================

def validate_linkedin_oauth_config() -> None:
    """
    Validate LinkedIn OAuth configuration.
    """

    if not LINKEDIN_CLIENT_ID:
        raise RuntimeError(
            "LINKEDIN_CLIENT_ID is not configured."
        )

    if not LINKEDIN_CLIENT_SECRET:
        raise RuntimeError(
            "LINKEDIN_CLIENT_SECRET is not configured."
        )

    get_linkedin_redirect_uri()


# =========================================================
# SCOPES
# =========================================================

def get_linkedin_scopes() -> list[str]:
    """
    Return configured LinkedIn OAuth scopes.
    """

    scopes = [
        scope.strip()
        for scope in LINKEDIN_SCOPES
        if scope.strip()
    ]

    if not scopes:
        raise RuntimeError(
            "No LinkedIn OAuth scopes are configured."
        )

    return scopes


# =========================================================
# AUTHORIZATION URL
# =========================================================

def build_linkedin_authorization_url(
    state: str,
) -> str:
    """
    Build LinkedIn OAuth 2.0 authorization URL.
    """

    validate_linkedin_oauth_config()

    if not state:
        raise ValueError(
            "OAuth state is required."
        )

    redirect_uri = get_linkedin_redirect_uri()
    scopes = get_linkedin_scopes()

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": " ".join(scopes),
    }

    authorization_url = (
        f"{LINKEDIN_AUTHORIZATION_URL}"
        f"?{urlencode(params)}"
    )

    # Safe debugging
    print("LinkedIn OAuth authorization configured:")
    print(
        "  client_id:",
        LINKEDIN_CLIENT_ID,
    )
    print(
        "  redirect_uri:",
        repr(redirect_uri),
    )
    print(
        "  scopes:",
        scopes,
    )

    return authorization_url


# =========================================================
# AUTHORIZATION CODE → ACCESS TOKEN
# =========================================================

def exchange_linkedin_code_for_access_token(
    code: str,
) -> dict:
    """
    Exchange LinkedIn authorization code
    for an access token.
    """

    validate_linkedin_oauth_config()

    if not code:
        raise ValueError(
            "Authorization code is required."
        )

    redirect_uri = get_linkedin_redirect_uri()

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
    }

    print("LinkedIn token exchange:")
    print(
        "  client_id:",
        LINKEDIN_CLIENT_ID,
    )
    print(
        "  redirect_uri:",
        repr(redirect_uri),
    )
    print(
        "  code_received:",
        bool(code),
    )

    response = requests.post(
        LINKEDIN_TOKEN_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "LinkedIn token exchange failed: "
            f"{response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError(
            "LinkedIn returned an invalid token response."
        ) from e

    if not data.get("access_token"):
        raise RuntimeError(
            "LinkedIn did not return an access token."
        )

    return data