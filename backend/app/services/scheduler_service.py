from apscheduler.schedulers.background import BackgroundScheduler

from app.agents.supervisor_agent import run_autonomous_agent
from app.services.automation_service import get_automation_setting


# Scheduler uses Indian Standard Time
scheduler = BackgroundScheduler(
    timezone="Asia/Kolkata"
)


def run_daily_post(
    niche,
    topic,
    language="English",
    tone="Professional",
    profile_id=None
):
    """
    Runs the autonomous AI post generation pipeline.
    """

    print("🤖 Starting daily autonomous post generation...")

    try:
        result = run_autonomous_agent(
            niche=niche,
            topic=topic,
            language=language,
            tone=tone,
            profile_id=profile_id
        )

        print("✅ Daily autonomous task completed.")
        print(result)

        return result

    except Exception as e:
        print(f"❌ Daily autonomous task failed: {e}")

        return {
            "status": "failed",
            "error": str(e)
        }


def start_scheduler():
    """
    Start background scheduler.
    """

    if not scheduler.running:
        scheduler.start()
        print("⏰ Scheduler started.")


def stop_scheduler():
    """
    Stop background scheduler.
    """

    if scheduler.running:
        scheduler.shutdown()
        print("⏹️ Scheduler stopped.")


def add_daily_job(
    niche,
    topic,
    hour,
    minute,
    language="English",
    tone="Professional",
    profile_id=None
):
    """
    Add a daily autonomous posting job.
    """

    job_id = f"daily_post_{profile_id or 'default'}"

    scheduler.add_job(
        run_daily_post,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[
            niche,
            topic,
            language,
            tone,
            profile_id
        ],
        id=job_id,
        replace_existing=True
    )

    print(
        f"📅 Daily job scheduled at "
        f"{hour:02d}:{minute:02d} IST"
    )

    return {
        "job_id": job_id,
        "schedule": f"{hour:02d}:{minute:02d}",
        "frequency": "daily",
        "timezone": "Asia/Kolkata"
    }


def schedule_from_database(setting_id):
    """
    Load automation settings from Supabase
    and create a scheduler job.
    """

    setting = get_automation_setting(setting_id)

    if not setting:
        return {
            "status": "error",
            "message": "Automation setting not found."
        }

    if not setting.get("is_enabled", False):
        return {
            "status": "disabled",
            "message": "Automation is disabled.",
            "setting_id": setting_id
        }

    if setting.get("is_paused", False):
        return {
            "status": "paused",
            "message": "Automation is currently paused.",
            "setting_id": setting_id
        }

    frequency = setting.get("frequency", "daily")

    if frequency != "daily":
        return {
            "status": "error",
            "message": "Currently only daily frequency is supported.",
            "frequency": frequency
        }

    posting_time = setting.get("posting_time")

    if not posting_time:
        return {
            "status": "error",
            "message": "Posting time is missing."
        }

    time_parts = str(posting_time).split(":")

    hour = int(time_parts[0])
    minute = int(time_parts[1])

    job = add_daily_job(
        niche=setting["niche"],
        topic=setting["topic"],
        hour=hour,
        minute=minute,
        language=setting.get("language", "English"),
        tone=setting.get("tone", "Professional"),
        profile_id=setting.get("profile_id")
    )

    return {
        "status": "success",
        "message": "Automation scheduled from database settings.",
        "setting_id": setting_id,
        "automation": setting,
        "job": job
    }


def remove_daily_job(profile_id=None):
    """
    Remove a user's daily posting job.
    """

    job_id = f"daily_post_{profile_id or 'default'}"

    try:
        scheduler.remove_job(job_id)

        return {
            "status": "success",
            "message": "Daily job removed.",
            "job_id": job_id
        }

    except Exception:
        return {
            "status": "not_found",
            "message": "No daily job found.",
            "job_id": job_id
        }


def get_scheduled_jobs():
    """
    Return all currently scheduled jobs.
    """

    jobs = scheduler.get_jobs()

    return [
        {
            "id": job.id,
            "next_run_time": (
                job.next_run_time.isoformat()
                if job.next_run_time
                else None
            )
        }
        for job in jobs
    ]


# =========================================================
# ONE-TIME SCHEDULED POST
# =========================================================

from app.database.supabase import get_database_client

from app.services.linkedin_publish_service import (
    publish_linkedin_text_post,
    publish_linkedin_multi_image_post,
)

from app.services.instagram_publish_service import (
    publish_instagram_image_post,
)

from app.services.x_publish_service import (
    publish_x_text_post,
    publish_x_image_post,
)


def run_scheduled_post(scheduled_post_id):
    """
    Publish a one-time scheduled post.

    Supported platforms:
    - LinkedIn
    - Instagram
    - X

    The post is NOT generated again.
    The already-generated post is published.
    """

    print(
        f"⏰ Running scheduled post: {scheduled_post_id}"
    )

    db = get_database_client()

    try:
        # -------------------------------------------------
        # Get scheduled post
        # -------------------------------------------------

        scheduled_response = (
            db
            .table("scheduled_posts")
            .select("*")
            .eq("id", scheduled_post_id)
            .limit(1)
            .execute()
        )

        if not scheduled_response.data:
            print("❌ Scheduled post not found.")
            return

        scheduled_post = scheduled_response.data[0]

        # -------------------------------------------------
        # Prevent duplicate publishing
        # -------------------------------------------------

        if scheduled_post.get("status") != "scheduled":
            print(
                "⚠️ Scheduled post is already processed."
            )
            return

        post_id = scheduled_post.get("post_id")

        platform = (
            scheduled_post.get("platform")
            or "linkedin"
        ).strip().lower()

        user_id = scheduled_post.get("user_id")

        if not post_id:
            raise RuntimeError(
                "Scheduled post does not contain a post_id."
            )

        if not user_id:
            raise RuntimeError(
                "Scheduled post does not contain a user_id."
            )

        # -------------------------------------------------
        # Validate supported platform
        # -------------------------------------------------

        supported_platforms = {
            "linkedin",
            "instagram",
            "x",
        }

        if platform not in supported_platforms:
            raise RuntimeError(
                f"Platform '{platform}' is not supported yet."
            )

        # -------------------------------------------------
        # Get original post
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
            raise RuntimeError(
                "Original post not found."
            )

        post = post_response.data[0]

        # -------------------------------------------------
        # Prepare post content
        # -------------------------------------------------

        caption = post.get("caption")

        if not caption:
            raise RuntimeError(
                "Post caption is empty."
            )

        caption = str(caption).strip()

        # -------------------------------------------------
        # Prepare hashtags
        # -------------------------------------------------

        hashtags = post.get("hashtags") or []

        if hashtags:
            hashtag_text = " ".join(
                hashtag
                if str(hashtag).startswith("#")
                else f"#{hashtag}"
                for hashtag in hashtags
            )

            caption = (
                f"{caption}\n\n"
                f"{hashtag_text}"
            )

        # -------------------------------------------------
        # Prepare media
        # -------------------------------------------------

        media_urls = post.get("media_urls") or []

        if not isinstance(media_urls, list):
            media_urls = [media_urls]

        # =================================================
        # LINKEDIN
        # =================================================

        if platform == "linkedin":

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
                raise RuntimeError(
                    "LinkedIn account is not connected."
                )

            linkedin_account = account_response.data[0]

            access_token = linkedin_account.get(
                "access_token"
            )

            author_id = linkedin_account.get(
                "platform_user_id"
            )

            if not access_token:
                raise RuntimeError(
                    "LinkedIn access token is missing."
                )

            if not author_id:
                raise RuntimeError(
                    "LinkedIn profile ID is missing."
                )

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

        # =================================================
        # X
        # =================================================

        elif platform == "x":

            account_response = (
                db
                .table("social_accounts")
                .select("*")
                .eq("user_id", user_id)
                .eq("platform", "x")
                .eq("status", "connected")
                .limit(1)
                .execute()
            )

            if not account_response.data:
                raise RuntimeError(
                    "X account is not connected."
                )

            x_account = account_response.data[0]

            access_token = x_account.get(
                "access_token"
            )

            if not access_token:
                raise RuntimeError(
                    "X access token is missing."
                )

            # X has a 280-character limit.
            if len(caption) > 280:
                raise RuntimeError(
                    f"X post exceeds 280 characters "
                    f"({len(caption)})."
                )

            # Preserve existing scheduling behavior:
            # use image when generated media exists,
            # otherwise publish text only.
            if media_urls:

                result = publish_x_image_post(
                    access_token=access_token,
                    text=caption,
                    image_url=media_urls[0],
                )

            else:

                result = publish_x_text_post(
                    access_token=access_token,
                    text=caption,
                )

        # =================================================
        # INSTAGRAM
        # =================================================

        elif platform == "instagram":

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
                raise RuntimeError(
                    "Instagram account is not connected."
                )

            instagram_account = account_response.data[0]

            access_token = instagram_account.get(
                "access_token"
            )

            instagram_user_id = instagram_account.get(
                "platform_user_id"
            )

            if not access_token:
                raise RuntimeError(
                    "Instagram access token is missing."
                )

            if not instagram_user_id:
                raise RuntimeError(
                    "Instagram user ID is missing."
                )

            if not media_urls:
                raise RuntimeError(
                    "Instagram scheduling requires an image."
                )

            result = publish_instagram_image_post(
                access_token=access_token,
                instagram_user_id=instagram_user_id,
                image_url=media_urls[0],
                caption=caption,
            )

        else:

            raise RuntimeError(
                f"Platform '{platform}' is not supported yet."
            )

        # =================================================
        # UPDATE SCHEDULED POST
        # =================================================

        from datetime import datetime, timezone

        db.table("scheduled_posts").update(
            {
                "status": "published",
                "published_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        ).eq(
            "id",
            scheduled_post_id
        ).execute()

        # =================================================
        # UPDATE ORIGINAL POST
        # =================================================

        db.table("posts").update(
            {
                "status": "published",
            }
        ).eq(
            "id",
            post_id
        ).eq(
            "user_id",
            user_id
        ).execute()

        print(
            "✅ Scheduled post published successfully."
        )

        return {
            "status": "published",
            "scheduled_post_id": scheduled_post_id,
            "post_id": post_id,
            "platform": platform,
            "publish_result": result,
        }

    except Exception as e:

        print(
            f"❌ Scheduled post failed: {e}"
        )

        # Mark only this scheduled platform as failed.
        db.table("scheduled_posts").update(
            {
                "status": "failed",
            }
        ).eq(
            "id",
            scheduled_post_id
        ).execute()

        return {
            "status": "failed",
            "scheduled_post_id": scheduled_post_id,
            "error": str(e),
        }


def add_one_time_job(
    scheduled_post_id,
    scheduled_at,
):
    """
    Add a one-time APScheduler job.
    """

    job_id = (
        f"scheduled_post_{scheduled_post_id}"
    )

    scheduler.add_job(
        run_scheduled_post,
        trigger="date",
        run_date=scheduled_at,
        args=[scheduled_post_id],
        id=job_id,
        replace_existing=True,
    )

    print(
        f"📅 One-time post scheduled for "
        f"{scheduled_at}"
    )

    return {
        "job_id": job_id,
        "scheduled_post_id": scheduled_post_id,
        "scheduled_at": scheduled_at.isoformat(),
        "frequency": "once",
        "timezone": "Asia/Kolkata",
    }


def remove_one_time_job(
    scheduled_post_id,
):
    """
    Remove a one-time scheduled post job.
    """

    job_id = (
        f"scheduled_post_{scheduled_post_id}"
    )

    try:

        scheduler.remove_job(job_id)

        return {
            "status": "success",
            "message": "Scheduled post job removed.",
            "job_id": job_id,
        }

    except Exception:

        return {
            "status": "not_found",
            "message": "Scheduled post job not found.",
            "job_id": job_id,
        }