import requests
from datetime import date
from typing import Optional

from app.database.supabase import get_database_client


GRAPH_API_VERSION = "v23.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _get_metric_value(metrics, metric_name):
    """
    Handles Meta's metric response safely.
    """
    for item in metrics or []:
        if item.get("name") == metric_name:
            values = item.get("values") or []

            if values:
                value = values[-1].get("value")
                return _safe_int(value)

            value = item.get("value")
            return _safe_int(value)

    return 0


def collect_instagram_post_analytics(
    user_id: str,
    social_account_id: str,
    instagram_user_id: str,
    access_token: str,
    metric_date: Optional[date] = None,
):
    """
    Collect analytics for Instagram media belonging to the connected account.

    Existing publishing flow is not touched.
    """

    db = get_database_client()

    if metric_date is None:
        metric_date = date.today()

    # ---------------------------------------------------------
    # 1. Get Instagram media
    # ---------------------------------------------------------
    media_url = f"{GRAPH_BASE_URL}/{instagram_user_id}/media"

    media_params = {
        "fields": "id,caption,media_type,media_product_type,timestamp,permalink",
        "access_token": access_token,
        "limit": 100,
    }

    media_response = requests.get(
        media_url,
        params=media_params,
        timeout=30,
    )

    if not media_response.ok:
        raise RuntimeError(
            f"Instagram media API failed: "
            f"{media_response.status_code} "
            f"{media_response.text}"
        )

    media_data = media_response.json().get("data", [])

    collected = []

    # ---------------------------------------------------------
    # 2. Fetch insights for each media
    # ---------------------------------------------------------
    for media in media_data:
        media_id = media.get("id")

        if not media_id:
            continue

        insights_url = f"{GRAPH_BASE_URL}/{media_id}/insights"

        insights_params = {
            "access_token": access_token,
            "metric": (
                "impressions,"
                "reach,"
                "likes,"
                "comments,"
                "shares,"
                "saved"
            ),
        }

        insights_response = requests.get(
            insights_url,
            params=insights_params,
            timeout=30,
        )

        if not insights_response.ok:
            print(
                f"⚠️ Instagram insights failed for media {media_id}: "
                f"{insights_response.status_code} "
                f"{insights_response.text}"
            )
            continue

        insights = insights_response.json().get("data", [])

        impressions = _get_metric_value(insights, "impressions")
        reach = _get_metric_value(insights, "reach")
        likes = _get_metric_value(insights, "likes")
        comments = _get_metric_value(insights, "comments")
        shares = _get_metric_value(insights, "shares")
        saves = _get_metric_value(insights, "saved")

        engagements = (
            likes
            + comments
            + shares
            + saves
        )

        engagement_rate = 0

        if impressions > 0:
            engagement_rate = (
                engagements / impressions
            ) * 100

        # -----------------------------------------------------
        # 3. Store analytics snapshot
        # -----------------------------------------------------
        row = {
            "user_id": user_id,
            "post_id": media_id,
            "social_account_id": social_account_id,
            "platform": "instagram",
            "platform_post_id": media_id,
            "impressions": impressions,
            "reach": reach,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "clicks": 0,
            "followers_gained": 0,
            "engagement_rate": round(engagement_rate, 4),
            "metric_date": metric_date.isoformat(),
            "raw_data": {
                "media": media,
                "insights": insights,
            },
        }

        # -----------------------------------------------------
        # 4. Avoid duplicate daily snapshot
        # -----------------------------------------------------
        existing = (
            db.table("post_analytics")
            .select("id")
            .eq("user_id", user_id)
            .eq("platform", "instagram")
            .eq("platform_post_id", media_id)
            .eq("metric_date", metric_date.isoformat())
            .limit(1)
            .execute()
        )

        if existing.data:
            analytics_id = existing.data[0]["id"]

            (
                db.table("post_analytics")
                .update(row)
                .eq("id", analytics_id)
                .execute()
            )

        else:
            db.table("post_analytics").insert(row).execute()

        collected.append(
            {
                "media_id": media_id,
                "impressions": impressions,
                "reach": reach,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "engagement_rate": round(
                    engagement_rate,
                    2,
                ),
            }
        )

    return {
        "platform": "instagram",
        "metric_date": metric_date.isoformat(),
        "media_found": len(media_data),
        "analytics_collected": len(collected),
        "data": collected,
    }