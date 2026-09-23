from app.database.supabase import get_database_client

from app.services.analytics.instagram import collect_instagram
from app.services.analytics.linkedin import collect_linkedin
from app.services.analytics.x import collect_x


def collect_all_platform_analytics(user_id: str):
    db = get_database_client()

    response = (
        db.table("social_accounts")
        .select(
            "id, platform, platform_user_id, "
            "access_token, refresh_token, status"
        )
        .eq("user_id", user_id)
        .eq("status", "connected")
        .execute()
    )

    accounts = response.data or []

    results = []

    for account in accounts:
        platform = (
            account.get("platform") or ""
        ).lower().strip()

        try:
            if platform == "instagram":
                result = collect_instagram(
                    user_id=user_id,
                    account=account,
                )

            elif platform == "linkedin":
                result = collect_linkedin(
                    user_id=user_id,
                    account=account,
                )

            elif platform == "x":
                result = collect_x(
                    user_id=user_id,
                    account=account,
                )

            else:
                result = {
                    "status": "unsupported",
                    "message": (
                        f"Analytics not implemented "
                        f"for {platform}"
                    ),
                }

            results.append({
                "platform": platform,
                **result,
            })

        except Exception as exc:
            results.append({
                "platform": platform,
                "status": "error",
                "message": str(exc),
            })

    return {
        "user_id": user_id,
        "accounts_found": len(accounts),
        "results": results,
    }