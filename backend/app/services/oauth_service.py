import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv


load_dotenv()


# =========================================================
# META / INSTAGRAM CONFIGURATION
# =========================================================

META_CLIENT_ID = os.getenv("META_CLIENT_ID")
META_CLIENT_SECRET = os.getenv("META_CLIENT_SECRET")

META_REDIRECT_URI = os.getenv(
    "META_REDIRECT_URI",
    "http://127.0.0.1:8000/social-accounts/oauth/instagram/callback",
).strip()


# Instagram Business Login authorization endpoint
META_AUTHORIZATION_URL = (
    "https://www.instagram.com/oauth/authorize"
)

# Instagram Business Login token endpoint
INSTAGRAM_TOKEN_URL = (
    "https://api.instagram.com/oauth/access_token"
)

# Long-lived token endpoint
INSTAGRAM_LONG_LIVED_TOKEN_URL = (
    "https://graph.instagram.com/access_token"
)


# =========================================================
# INSTAGRAM SCOPES
# =========================================================

INSTAGRAM_SCOPES = os.getenv(
    "INSTAGRAM_SCOPES",
    "instagram_business_basic,instagram_business_content_publish",
).split(",")


# =========================================================
# OAUTH STATE
# =========================================================

def generate_oauth_state() -> str:
    """
    Generate a cryptographically secure OAuth state.
    """

    return secrets.token_urlsafe(32)


def get_oauth_state_expiry(
    minutes: int = 10,
) -> str:
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

def get_instagram_redirect_uri() -> str:
    """
    Return the single canonical Instagram redirect URI.

    The same value is used for:
    1. Authorization request
    2. Authorization-code exchange
    """

    redirect_uri = META_REDIRECT_URI.strip()

    if not redirect_uri:
        raise RuntimeError(
            "META_REDIRECT_URI is not configured."
        )

    return redirect_uri


# =========================================================
# CONFIG VALIDATION
# =========================================================

def validate_oauth_config() -> None:
    """
    Validate Meta OAuth configuration.
    """

    if not META_CLIENT_ID:
        raise RuntimeError(
            "META_CLIENT_ID is not configured."
        )

    if not META_CLIENT_SECRET:
        raise RuntimeError(
            "META_CLIENT_SECRET is not configured."
        )

    get_instagram_redirect_uri()


# =========================================================
# INSTAGRAM SCOPES
# =========================================================

def get_instagram_scopes() -> list[str]:
    """
    Return configured Instagram permissions.
    """

    scopes = [
        scope.strip()
        for scope in INSTAGRAM_SCOPES
        if scope.strip()
    ]

    if not scopes:
        raise RuntimeError(
            "No Instagram OAuth scopes are configured."
        )

    return scopes


# =========================================================
# INSTAGRAM AUTHORIZATION URL
# =========================================================

def build_instagram_authorization_url(
    state: str,
) -> str:
    """
    Build the Instagram Business Login authorization URL.
    """

    validate_oauth_config()

    if not state:
        raise ValueError(
            "OAuth state is required."
        )

    redirect_uri = get_instagram_redirect_uri()
    scopes = get_instagram_scopes()

    params = {
        "client_id": META_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ",".join(scopes),
        "state": state,
        "enable_fb_login": "0",
        "force_reauth": "true",
    }

    authorization_url = (
        f"{META_AUTHORIZATION_URL}"
        f"?{urlencode(params)}"
    )

    # Safe debugging — no secret/token printed
    print(
        "Instagram OAuth authorization configured:"
    )
    print(
        "  client_id:",
        META_CLIENT_ID,
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
# AUTHORIZATION CODE → SHORT-LIVED ACCESS TOKEN
# =========================================================

# =========================================================
# AUTHORIZATION CODE → SHORT-LIVED ACCESS TOKEN
# =========================================================

def exchange_code_for_access_token(code: str) -> dict:
    """
    Exchange Instagram authorization code
    for a short-lived access token.

    The redirect URI must exactly match
    the URI used in the authorization request.
    """

    validate_oauth_config()

    if not code:
        raise ValueError("Authorization code is required.")

    # Use the single canonical redirect URI
    redirect_uri = get_instagram_redirect_uri()

    payload = {
        "client_id": META_CLIENT_ID,
        "client_secret": META_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code,
    }

    # Safe debugging — never print secret or token
    print("Instagram token exchange:")
    print("  client_id:", META_CLIENT_ID)
    print("  redirect_uri:", repr(redirect_uri))
    print("  code_received:", bool(code))

    response = requests.post(
        INSTAGRAM_TOKEN_URL,
        data=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "Instagram token exchange failed: "
            f"{response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError(
            "Instagram returned an invalid token response."
        ) from e

    if not data.get("access_token"):
        raise RuntimeError(
            "Instagram did not return an access token."
        )

    return data
    """
    Exchange Instagram authorization code
    for a short-lived access token.

    IMPORTANT:
    The redirect URI used here MUST be exactly
    the same URI used in the authorization request.
    """

    validate_oauth_config()

    if not code:
        raise ValueError(
            "Authorization code is required."
        )

    # Use the exact URI supplied by the OAuth flow.
    # Fall back to the canonical configured URI.
    final_redirect_uri = (
        redirect_uri.strip()
        if redirect_uri
        else get_instagram_redirect_uri()
    )

    if not final_redirect_uri:
        raise ValueError(
            "Instagram redirect URI is missing."
        )

    payload = {
        "client_id": META_CLIENT_ID,
        "client_secret": META_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": final_redirect_uri,
        "code": code,
    }

    # Safe diagnostics
    print(
        "Instagram token exchange:"
    )
    print(
        "  client_id:",
        META_CLIENT_ID,
    )
    print(
        "  redirect_uri:",
        repr(final_redirect_uri),
    )
    print(
        "  code_received:",
        bool(code),
    )

    response = requests.post(
        INSTAGRAM_TOKEN_URL,
        data=payload,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "Instagram token exchange failed: "
            f"{response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError(
            "Instagram returned an invalid token response."
        ) from e

    if not data.get("access_token"):
        raise RuntimeError(
            "Instagram did not return an access token."
        )

    return data


# =========================================================
# SHORT-LIVED → LONG-LIVED ACCESS TOKEN
# =========================================================

def exchange_for_long_lived_token(
    access_token: str,
) -> dict:
    """
    Exchange short-lived Instagram token
    for a long-lived token.
    """

    validate_oauth_config()

    if not access_token:
        raise ValueError(
            "Access token is required."
        )

    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": META_CLIENT_SECRET,
        "access_token": access_token,
    }

    response = requests.get(
        INSTAGRAM_LONG_LIVED_TOKEN_URL,
        params=params,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "Instagram long-lived token exchange failed: "
            f"{response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError(
            "Instagram returned an invalid long-lived token response."
        ) from e

    if not data.get("access_token"):
        raise RuntimeError(
            "Instagram did not return a long-lived access token."
        )

    return data


# =========================================================
# META CLIENT SECRET
# =========================================================

def get_meta_client_secret() -> str:
    """
    Return Meta client secret for server-side operations.
    """

    if not META_CLIENT_SECRET:
        raise RuntimeError(
            "META_CLIENT_SECRET is not configured."
        )

    return META_CLIENT_SECRET
# =========================================================
# X / TWITTER OAUTH 2.0 PKCE CONFIGURATION
# =========================================================

X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")

X_REDIRECT_URI = os.getenv(
    "X_REDIRECT_URI",
    "http://127.0.0.1:8000/social-accounts/oauth/x/callback",
).strip()

X_AUTHORIZATION_URL = "https://twitter.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.x.com/2/oauth2/token"
X_USER_ME_URL = "https://api.x.com/2/users/me"

X_SCOPES = [
    "tweet.read",
    "tweet.write",
    "users.read",
    "media.write",
    "offline.access",
]

def generate_x_code_verifier() -> str:
    """
    Generate a secure PKCE code verifier.
    """
    return secrets.token_urlsafe(64)


def generate_x_code_challenge(code_verifier: str) -> str:
    """
    Generate PKCE S256 code challenge.
    """
    import hashlib
    import base64

    digest = hashlib.sha256(
        code_verifier.encode("utf-8")
    ).digest()

    return base64.urlsafe_b64encode(
        digest
    ).decode("utf-8").rstrip("=")


def get_x_redirect_uri() -> str:
    """
    Return the canonical X OAuth redirect URI.
    """
    redirect_uri = X_REDIRECT_URI.strip()

    if not redirect_uri:
        raise RuntimeError(
            "X_REDIRECT_URI is not configured."
        )

    return redirect_uri


def validate_x_oauth_config() -> None:
    """
    Validate X OAuth configuration.
    """
    if not X_CLIENT_ID:
        raise RuntimeError(
            "X_CLIENT_ID is not configured."
        )

    if not X_CLIENT_SECRET:
        raise RuntimeError(
            "X_CLIENT_SECRET is not configured."
        )

    get_x_redirect_uri()


def build_x_authorization_url(
    state: str,
    code_challenge: str,
) -> str:
    """
    Build X OAuth 2.0 authorization URL.
    """

    validate_x_oauth_config()

    if not state:
        raise ValueError(
            "OAuth state is required."
        )

    if not code_challenge:
        raise ValueError(
            "PKCE code challenge is required."
        )

    params = {
        "response_type": "code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": get_x_redirect_uri(),
        "scope": " ".join(X_SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = (
        f"{X_AUTHORIZATION_URL}"
        f"?{urlencode(params)}"
    )

    print("X OAuth authorization configured:")
    print("  client_id:", X_CLIENT_ID)
    print("  redirect_uri:", repr(get_x_redirect_uri()))
    print("  scopes:", X_SCOPES)

    return authorization_url


def exchange_x_code_for_access_token(
    code: str,
    code_verifier: str,
) -> dict:
    """
    Exchange X OAuth authorization code
    for access + refresh tokens.
    """

    validate_x_oauth_config()

    if not code:
        raise ValueError(
            "X authorization code is required."
        )

    if not code_verifier:
        raise ValueError(
            "X PKCE code verifier is required."
        )

    payload = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": get_x_redirect_uri(),
        "code_verifier": code_verifier,
    }

    response = requests.post(
        X_TOKEN_URL,
        data=payload,
        auth=(
            X_CLIENT_ID,
            X_CLIENT_SECRET,
        ),
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "X token exchange failed: "
            f"{response.status_code} - "
            f"{response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError(
            "X returned an invalid token response."
        ) from e

    if not data.get("access_token"):
        raise RuntimeError(
            "X did not return an access token."
        )

    return data


def get_x_current_user(
    access_token: str,
) -> dict:
    """
    Get the X account associated with
    the OAuth access token.
    """

    if not access_token:
        raise ValueError(
            "X access token is required."
        )

    response = requests.get(
        X_USER_ME_URL,
        params={
            "user.fields": "id,name,username",
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "X user lookup failed: "
            f"{response.status_code} - "
            f"{response.text}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise RuntimeError(
            "X returned an invalid user response."
        ) from e

    user = data.get("data")

    if not user or not user.get("id"):
        raise RuntimeError(
            "X did not return the authenticated user."
        )

    return user