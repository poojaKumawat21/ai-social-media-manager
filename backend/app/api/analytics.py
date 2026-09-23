from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.database.supabase import get_database_client
from app.services.analytics.collector import (
    collect_all_platform_analytics,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def _get_date_range(
    days: int = 30,
):
    if days not in {7, 30, 90}:
        raise HTTPException(
            status_code=400,
            detail="days must be 7, 30, or 90",
        )

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    return start_date, end_date


@router.get("/overview")
def get_analytics_overview(
    days: int = 30,
    platform: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    db = get_database_client()

    start_date, end_date = _get_date_range(days)

    query = (
        db.table("post_analytics")
        .select(
            "impressions,reach,likes,comments,shares,"
            "saves,clicks,followers_gained,engagement_rate,"
            "platform,post_id,metric_date"
        )
        .eq("user_id", user_id)
        .gte("metric_date", start_date.isoformat())
        .lte("metric_date", end_date.isoformat())
    )

    if platform:
        query = query.eq("platform", platform.lower())

    response = query.execute()

    rows = response.data or []

    total_impressions = sum(
        row.get("impressions") or 0
        for row in rows
    )

    total_reach = sum(
        row.get("reach") or 0
        for row in rows
    )

    total_likes = sum(
        row.get("likes") or 0
        for row in rows
    )

    total_comments = sum(
        row.get("comments") or 0
        for row in rows
    )

    total_shares = sum(
        row.get("shares") or 0
        for row in rows
    )

    total_saves = sum(
        row.get("saves") or 0
        for row in rows
    )

    total_clicks = sum(
        row.get("clicks") or 0
        for row in rows
    )

    total_followers_gained = sum(
        row.get("followers_gained") or 0
        for row in rows
    )

    total_engagements = (
        total_likes
        + total_comments
        + total_shares
        + total_saves
        + total_clicks
    )

    if total_impressions > 0:
        engagement_rate = (
            total_engagements / total_impressions
        ) * 100
    else:
        engagement_rate = 0

    unique_posts = len(
        {
            row.get("post_id")
            for row in rows
            if row.get("post_id")
        }
    )

    return {
        "days": days,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "platform": platform,
        "total_posts": unique_posts,
        "total_impressions": total_impressions,
        "total_reach": total_reach,
        "total_engagements": total_engagements,
        "engagement_rate": round(
            engagement_rate,
            2,
        ),
        "followers_gained": total_followers_gained,
        "breakdown": {
            "likes": total_likes,
            "comments": total_comments,
            "shares": total_shares,
            "saves": total_saves,
            "clicks": total_clicks,
        },
    }


@router.get("/platform/{platform}")
def get_platform_analytics(
    platform: str,
    days: int = 30,
    user_id: str = Depends(get_current_user),
):
    platform = platform.lower().strip()

    allowed_platforms = {
        "instagram",
        "linkedin",
        "x",
    }

    if platform not in allowed_platforms:
        raise HTTPException(
            status_code=400,
            detail=(
                "Supported platforms: "
                "instagram, linkedin, x"
            ),
        )

    db = get_database_client()

    start_date, end_date = _get_date_range(days)

    response = (
        db.table("post_analytics")
        .select("*")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .gte(
            "metric_date",
            start_date.isoformat(),
        )
        .lte(
            "metric_date",
            end_date.isoformat(),
        )
        .order(
            "metric_date",
            desc=False,
        )
        .execute()
    )

    rows = response.data or []

    return {
        "platform": platform,
        "days": days,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "data": rows,
    }


@router.get("/timeseries")
def get_analytics_timeseries(
    days: int = 30,
    platform: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    db = get_database_client()

    start_date, end_date = _get_date_range(days)

    query = (
        db.table("post_analytics")
        .select(
            "metric_date,platform,impressions,reach,"
            "likes,comments,shares,saves,clicks,"
            "followers_gained"
        )
        .eq("user_id", user_id)
        .gte(
            "metric_date",
            start_date.isoformat(),
        )
        .lte(
            "metric_date",
            end_date.isoformat(),
        )
    )

    if platform:
        query = query.eq(
            "platform",
            platform.lower(),
        )

    response = (
        query
        .order("metric_date", desc=False)
        .execute()
    )

    rows = response.data or []

    grouped = {}

    for row in rows:
        metric_date = row.get("metric_date")

        if metric_date not in grouped:
            grouped[metric_date] = {
                "date": metric_date,
                "impressions": 0,
                "reach": 0,
                "engagements": 0,
                "followers_gained": 0,
            }

        grouped[metric_date]["impressions"] += (
            row.get("impressions") or 0
        )

        grouped[metric_date]["reach"] += (
            row.get("reach") or 0
        )

        grouped[metric_date]["engagements"] += (
            (row.get("likes") or 0)
            + (row.get("comments") or 0)
            + (row.get("shares") or 0)
            + (row.get("saves") or 0)
            + (row.get("clicks") or 0)
        )

        grouped[metric_date]["followers_gained"] += (
            row.get("followers_gained") or 0
        )

    return {
        "days": days,
        "platform": platform,
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "data": list(grouped.values()),
    }


@router.get("/top-posts")
def get_top_posts(
    days: int = 30,
    platform: Optional[str] = None,
    limit: int = 10,
    user_id: str = Depends(get_current_user),
):
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 50",
        )

    db = get_database_client()

    start_date, end_date = _get_date_range(days)

    query = (
        db.table("post_analytics")
        .select(
            "post_id,platform,platform_post_id,"
            "impressions,reach,likes,comments,shares,"
            "saves,clicks,followers_gained,"
            "metric_date"
        )
        .eq("user_id", user_id)
        .gte(
            "metric_date",
            start_date.isoformat(),
        )
        .lte(
            "metric_date",
            end_date.isoformat(),
        )
    )

    if platform:
        query = query.eq(
            "platform",
            platform.lower(),
        )

    response = query.execute()

    rows = response.data or []

    post_totals = {}

    for row in rows:
        post_id = row.get("post_id")

        if not post_id:
            continue

        if post_id not in post_totals:
            post_totals[post_id] = {
                "post_id": post_id,
                "platform": row.get("platform"),
                "platform_post_id": row.get(
                    "platform_post_id"
                ),
                "impressions": 0,
                "reach": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "saves": 0,
                "clicks": 0,
                "followers_gained": 0,
            }

        item = post_totals[post_id]

        for field in [
            "impressions",
            "reach",
            "likes",
            "comments",
            "shares",
            "saves",
            "clicks",
            "followers_gained",
        ]:
            item[field] += row.get(field) or 0

    posts = list(post_totals.values())

    for item in posts:
        item["engagements"] = (
            item["likes"]
            + item["comments"]
            + item["shares"]
            + item["saves"]
            + item["clicks"]
        )

    posts.sort(
        key=lambda item: item["engagements"],
        reverse=True,
    )

    return {
        "days": days,
        "platform": platform,
        "data": posts[:limit],
    }


@router.get("/posts/{post_id}")
def get_post_analytics(
    post_id: str,
    user_id: str = Depends(get_current_user),
):
    db = get_database_client()

    response = (
        db.table("post_analytics")
        .select("*")
        .eq("user_id", user_id)
        .eq("post_id", post_id)
        .order(
            "metric_date",
            desc=False,
        )
        .execute()
    )

    rows = response.data or []

    return {
        "post_id": post_id,
        "data": rows,
    }

@router.post("/collect")
def collect_analytics(
    user_id: str = Depends(get_current_user),
):
    try:
        return collect_all_platform_analytics(
            user_id=user_id
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )