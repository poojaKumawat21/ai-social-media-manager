from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.social_accounts import router as social_accounts_router
from app.api.ai import router as ai_router


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Social Media Manager API",
    description="Backend API for AI-powered autonomous social media management.",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# AUTH / ROUTERS
# =========================================================

from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.posts import router as posts_router
from app.api.scheduled_posts import router as scheduled_posts_router
from app.api.analytics import router as analytics_router


# =========================================================
# DATABASE
# =========================================================

from app.database.supabase import supabase


# =========================================================
# MODELS
# =========================================================

from app.models.profile import ProfileCreate
from app.models.post import PostCreate
from app.models.automation import (
    AutomationCreate,
    AutomationUpdate,
)


# =========================================================
# AI AGENTS
# =========================================================

from app.agents.research_agent import research_tech_news
from app.agents.safety_agent import check_safety
from app.agents.fact_check_agent import fact_check_post

from app.agents.content_planner import (
    plan_social_media_post,
)

from app.agents.supervisor_agent import (
    run_supervisor,
    run_autonomous_agent,
)

from app.agents.style_agent import (
    choose_style,
    check_duplicate,
    check_post_against_history,
)


# =========================================================
# AI SERVICES
# =========================================================

from app.services.image_generator import generate_post_image

from app.services.content_generator import (
    generate_post,
    generate_post_from_news,
)

from app.services.post_service import (
    save_post,
    get_previous_posts,
)

from app.services.ai_orchestrator import (
    run_ai_pipeline,
)


# =========================================================
# AUTOMATION
# =========================================================

from app.services.automation_service import (
    create_automation_settings,
    get_automation_settings,
    get_automation_setting,
    update_automation_settings,
    enable_automation,
    disable_automation,
    pause_automation,
    resume_automation,
    delete_automation_settings,
)


# =========================================================
# SCHEDULER
# =========================================================

from app.services.scheduler_service import (
    start_scheduler,
    stop_scheduler,
    schedule_from_database,
    remove_daily_job,
    get_scheduled_jobs,
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Social Media Manager API",
    description="Backend API for AI-powered autonomous social media management.",
    version="1.0.0",
)
@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# AUTHENTICATED API ROUTERS
# =========================================================
#
# IMPORTANT:
# Authentication for /profile and /posts is handled inside
# their respective router files using get_current_user().
#
# DO NOT create duplicate /posts or /profile routes here.
#

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(posts_router)
app.include_router(social_accounts_router)
app.include_router(scheduled_posts_router)
app.include_router(ai_router)
app.include_router(analytics_router)

# =========================================================
# STATIC FILES
# =========================================================

GENERATED_IMAGES_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    ),
    "generated_images",
)

os.makedirs(
    GENERATED_IMAGES_DIR,
    exist_ok=True,
)

app.mount(
    "/generated-images",
    StaticFiles(directory=GENERATED_IMAGES_DIR),
    name="generated-images",
)


# =========================================================
# BASIC
# =========================================================

@app.get("/")
def root():
    return {
        "message": "AI Social Media Manager API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# SUPABASE TEST
# =========================================================

@app.get("/supabase-test")
def supabase_test():

    response = (
        supabase
        .table("profiles")
        .select("id")
        .limit(1)
        .execute()
    )

    return {
        "status": "connected",
        "message": "Supabase connection successful",
        "data": response.data,
    }


# =========================================================
# LEGACY PROFILE ENDPOINTS
# =========================================================
#
# NOTE:
# The authenticated /profile endpoints are handled by
# app/api/profile.py.
#
# These old /profiles endpoints are kept temporarily so
# existing frontend/testing code does not immediately break.
#
# New frontend should use /profile.
# =========================================================

@app.post("/profiles")
def create_profile_legacy(profile: ProfileCreate):

    response = (
        supabase
        .table("profiles")
        .insert({
            "name": profile.name,
            "niche": profile.niche,
            "language": profile.language,
            "tone": profile.tone,
        })
        .execute()
    )

    return {
        "status": "success",
        "message": "Profile created successfully",
        "data": response.data,
    }


@app.get("/profiles")
def get_profiles_legacy():

    response = (
        supabase
        .table("profiles")
        .select("*")
        .execute()
    )

    return {
        "status": "success",
        "data": response.data,
    }


@app.put("/profiles/{profile_id}")
def update_profile_legacy(
    profile_id: str,
    profile: ProfileCreate,
):

    response = (
        supabase
        .table("profiles")
        .update({
            "name": profile.name,
            "niche": profile.niche,
            "language": profile.language,
            "tone": profile.tone,
        })
        .eq("id", profile_id)
        .execute()
    )

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "data": response.data,
    }


@app.delete("/profiles/{profile_id}")
def delete_profile_legacy(profile_id: str):

    response = (
        supabase
        .table("profiles")
        .delete()
        .eq("id", profile_id)
        .execute()
    )

    return {
        "status": "success",
        "message": "Profile deleted successfully",
        "data": response.data,
    }


# =========================================================
# AI CONTENT GENERATION
# =========================================================

@app.post("/generate-content")
def generate_content(
    niche: str,
    topic: str,
    language: str = "English",
    tone: str = "Professional",
    style: str = "Educational",
):

    post = generate_post(
        niche=niche,
        topic=topic,
        language=language,
        tone=tone,
        style=style,
    )

    return {
        "status": "success",
        "data": post,
    }


# =========================================================
# NEWS RESEARCH
# =========================================================

@app.get("/research-news")
def research_news(
    topic: str = "Artificial Intelligence",
    category: str = "ai",
):

    news = research_tech_news(
        topic=topic,
        category=category,
    )

    return {
        "status": "success",
        "count": len(news),
        "data": news,
    }

# =========================================================
# NEWS → POST
# =========================================================

@app.post("/news-to-post")
def news_to_post(
    news_title: str,
    news_source: str,
    niche: str = "Technology",
    language: str = "English",
    tone: str = "Professional",
    style: str = "Educational",
):

    post = generate_post_from_news(
        news_title=news_title,
        news_source=news_source,
        niche=niche,
        language=language,
        tone=tone,
        style=style,
    )

    return {
        "status": "success",
        "data": post,
    }


# =========================================================
# AGENT
# =========================================================

@app.post("/run-agent")
def run_agent(
    niche: str,
    topic: str,
    language: str = "English",
    tone: str = "Professional",
    style: str = "Educational",
):

    result = run_supervisor(
        niche=niche,
        topic=topic,
        language=language,
        tone=tone,
        style=style,
    )

    return {
        "status": "success",
        "data": result,
    }


# =========================================================
# AUTONOMOUS POST
# =========================================================

@app.post("/autonomous-post")
def autonomous_post(
    niche: str,
    topic: str,
    language: str = "English",
    tone: str = "Professional",
    profile_id: str = None,
):

    result = run_autonomous_agent(
        niche=niche,
        topic=topic,
        language=language,
        tone=tone,
        profile_id=profile_id,
    )

    return result


# =========================================================
# STYLE
# =========================================================

@app.post("/check-style")
def check_style(
    previous_styles: str = "",
):

    styles = [
        style.strip()
        for style in previous_styles.split(",")
        if style.strip()
    ]

    selected_style = choose_style(styles)

    return {
        "status": "success",
        "selected_style": selected_style,
        "available_styles": [
            "Educational",
            "Funny",
            "Tips",
            "Storytelling",
            "Professional",
            "Question",
            "Trending",
        ],
    }


# =========================================================
# DUPLICATE CHECK
# =========================================================

@app.post("/check-duplicate")
def check_duplicate_post(
    new_caption: str,
    previous_captions: str = "",
):

    captions = [
        caption.strip()
        for caption in previous_captions.split("|")
        if caption.strip()
    ]

    result = check_duplicate(
        new_caption=new_caption,
        previous_captions=captions,
    )

    return {
        "status": "success",
        "data": result,
    }


# =========================================================
# DATABASE DUPLICATE CHECK
# =========================================================

@app.post("/check-database-duplicate")
def check_database_duplicate(
    new_caption: str,
):

    previous_posts = get_previous_posts(
        limit=20
    )

    result = check_post_against_history(
        new_caption=new_caption,
        previous_posts=previous_posts,
    )

    return {
        "status": "success",
        "posts_checked": len(previous_posts),
        "data": result,
    }


# =========================================================
# LEGACY CREATE POST
# =========================================================
#
# IMPORTANT:
# GET /posts is intentionally NOT defined here.
#
# The authenticated GET /posts and POST /posts/generate
# are handled by app/api/posts.py.
# =========================================================

@app.post("/posts")
def create_post_legacy(
    post: PostCreate,
):

    saved_post = save_post(
        post.model_dump()
    )

    return {
        "status": "success",
        "data": saved_post,
    }


# =========================================================
# SAFETY
# =========================================================

@app.post("/check-safety")
def check_safety_endpoint(
    caption: str,
    news_title: str = None,
    news_source: str = None,
):

    result = check_safety(
        caption=caption,
        news_title=news_title,
        news_source=news_source,
    )

    return {
        "status": "success",
        "data": result,
    }


# =========================================================
# AUTOMATION SETTINGS
# =========================================================

@app.post("/automation")
def create_automation(
    data: AutomationCreate,
):

    result = create_automation_settings(
        data.model_dump()
    )

    return {
        "status": "success",
        "message": "Automation settings created.",
        "data": result,
    }


@app.get("/automation")
def get_automation(
    profile_id: str = None,
):

    result = get_automation_settings(
        profile_id=profile_id
    )

    return {
        "status": "success",
        "data": result,
    }


@app.get("/automation/{setting_id}")
def get_single_automation(
    setting_id: str,
):

    result = get_automation_setting(
        setting_id
    )

    return {
        "status": "success",
        "data": result,
    }


@app.put("/automation/{setting_id}")
def update_automation(
    setting_id: str,
    data: AutomationUpdate,
):

    updates = {
        key: value
        for key, value in data.model_dump().items()
        if value is not None
    }

    result = update_automation_settings(
        setting_id,
        updates,
    )

    return {
        "status": "success",
        "message": "Automation settings updated.",
        "data": result,
    }


# =========================================================
# ENABLE AUTOMATION
# =========================================================

@app.post("/automation/{setting_id}/enable")
def enable_automation_endpoint(
    setting_id: str,
):

    result = enable_automation(
        setting_id
    )

    scheduler_result = schedule_from_database(
        setting_id
    )

    return {
        "status": "success",
        "message": "Automation enabled and scheduled.",
        "automation": result,
        "scheduler": scheduler_result,
    }


# =========================================================
# DISABLE AUTOMATION
# =========================================================

@app.post("/automation/{setting_id}/disable")
def disable_automation_endpoint(
    setting_id: str,
):

    setting = get_automation_setting(
        setting_id
    )

    result = disable_automation(
        setting_id
    )

    profile_id = (
        setting.get("profile_id")
        if setting
        else None
    )

    scheduler_result = remove_daily_job(
        profile_id=profile_id
    )

    return {
        "status": "success",
        "message": "Automation disabled and scheduler job removed.",
        "automation": result,
        "scheduler": scheduler_result,
    }


# =========================================================
# PAUSE AUTOMATION
# =========================================================

@app.post("/automation/{setting_id}/pause")
def pause_automation_endpoint(
    setting_id: str,
):

    setting = get_automation_setting(
        setting_id
    )

    result = pause_automation(
        setting_id
    )

    profile_id = (
        setting.get("profile_id")
        if setting
        else None
    )

    scheduler_result = remove_daily_job(
        profile_id=profile_id
    )

    return {
        "status": "success",
        "message": "Automation paused and scheduler job removed.",
        "automation": result,
        "scheduler": scheduler_result,
    }


# =========================================================
# RESUME AUTOMATION
# =========================================================

@app.post("/automation/{setting_id}/resume")
def resume_automation_endpoint(
    setting_id: str,
):

    result = resume_automation(
        setting_id
    )

    scheduler_result = schedule_from_database(
        setting_id
    )

    return {
        "status": "success",
        "message": "Automation resumed and scheduled.",
        "automation": result,
        "scheduler": scheduler_result,
    }


# =========================================================
# DELETE AUTOMATION
# =========================================================

@app.delete("/automation/{setting_id}")
def delete_automation(
    setting_id: str,
):

    result = delete_automation_settings(
        setting_id
    )

    return {
        "status": "success",
        "message": "Automation settings deleted.",
        "data": result,
    }


# =========================================================
# SCHEDULER
# =========================================================

@app.post("/scheduler/start")
def start_scheduler_endpoint():

    start_scheduler()

    return {
        "status": "success",
        "message": "Scheduler started.",
    }


@app.post("/scheduler/stop")
def stop_scheduler_endpoint():

    stop_scheduler()

    return {
        "status": "success",
        "message": "Scheduler stopped.",
    }


@app.get("/scheduler/jobs")
def scheduler_jobs_endpoint():

    return {
        "status": "success",
        "jobs": get_scheduled_jobs(),
    }


@app.post("/scheduler/schedule-from-database/{setting_id}")
def schedule_from_database_endpoint(
    setting_id: str,
):

    result = schedule_from_database(
        setting_id
    )

    return result


# =========================================================
# IMAGE GENERATION
# =========================================================

@app.post("/generate-image")
def generate_image_endpoint(
    niche: str,
    topic: str,
    style: str = "Professional",
    language: str = "English",
):

    result = generate_post_image(
        niche=niche,
        topic=topic,
        style=style,
        language=language,
    )

    return result


# =========================================================
# FACT CHECK
# =========================================================

@app.post("/fact-check")
def fact_check_endpoint(
    caption: str,
    news_title: str = None,
    news_source: str = None,
):

    result = fact_check_post(
        caption=caption,
        news_title=news_title,
        news_source=news_source,
    )

    return result


# =========================================================
# CONTENT PLANNER
# =========================================================

@app.post("/plan-post")
def plan_post_endpoint(
    topic: str,
    niche: str = "General",
    language: str = "English",
    tone: str = "Professional",
    style: str = "Auto",
):

    result = plan_social_media_post(
        topic=topic,
        niche=niche,
        language=language,
        tone=tone,
        style=style,
    )

    return {
        "status": "success",
        "data": result,
    }


# =========================================================
# FULL AI SOCIAL MEDIA POST PIPELINE
# =========================================================

@app.post("/ai-generate-post")
def ai_generate_post(
    topic: str,
    description: str = "",
):

    result = run_ai_pipeline(
        topic=topic,
        description=description,
    )

    return {
        "status": "success",
        "data": result,
    }