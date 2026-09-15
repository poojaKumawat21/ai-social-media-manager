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

    # Get automation setting from database
    setting = get_automation_setting(setting_id)

    if not setting:
        return {
            "status": "error",
            "message": "Automation setting not found."
        }

    # Check whether automation is enabled
    if not setting.get("is_enabled", False):

        return {
            "status": "disabled",
            "message": "Automation is disabled.",
            "setting_id": setting_id
        }

    # Check whether automation is paused
    if setting.get("is_paused", False):

        return {
            "status": "paused",
            "message": "Automation is currently paused.",
            "setting_id": setting_id
        }

    # Currently supporting daily frequency
    frequency = setting.get("frequency", "daily")

    if frequency != "daily":

        return {
            "status": "error",
            "message": "Currently only daily frequency is supported.",
            "frequency": frequency
        }

    # Get posting time from database
    posting_time = setting.get("posting_time")

    if not posting_time:

        return {
            "status": "error",
            "message": "Posting time is missing."
        }

    # Convert database time into hour and minute
    time_parts = str(posting_time).split(":")

    hour = int(time_parts[0])
    minute = int(time_parts[1])

    # Add daily scheduler job
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