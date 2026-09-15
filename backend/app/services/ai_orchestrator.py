# =========================================================
# AI ORCHESTRATOR
# =========================================================
#
# Main AI pipeline:
#
# User Input
#      ↓
# Content Planner
#      ↓
# Style Agent
#      ↓
# Research Agent
#      ↓
# Content Generator
#      ↓
# Duplicate Check
#      ↓
# Safety Check
#      ↓
# Fact Check
#      ↓
# Design Agent
#      ↓
# Quality Check
#      ↓
# Post Renderer
#      ↓
# Final Social Media Image(s)
#      ↓
# Supabase Storage
#
# The AI agents make the creative decisions.
# The renderer only implements those decisions.
# =========================================================


from app.agents.content_planner import plan_social_media_post
from app.agents.style_agent import choose_style
from app.agents.research_agent import research_topic
from app.agents.design_agent import create_design_plan
from app.agents.safety_agent import check_safety
from app.agents.fact_check_agent import fact_check_post
from app.agents.quality_agent import check_quality

from app.services.content_generator import generate_post
from app.services.post_renderer import render_social_post
from app.services.storage_service import upload_image_to_storage


# =========================================================
# HELPER — GET PREVIOUS CAPTIONS
# =========================================================

def _extract_previous_captions(previous_posts):

    if not previous_posts:
        return []

    return [
        post.get("caption")
        for post in previous_posts
        if post.get("caption")
    ]


# =========================================================
# MAIN PIPELINE
# =========================================================

def run_ai_pipeline(
    topic: str,
    description: str = "",
    previous_styles=None,
    previous_posts=None
):
    """
    Run the complete AI social media generation pipeline.

    User provides:
        - topic
        - optional description

    AI decides:
        - niche
        - audience
        - tone
        - style
        - format
        - post type
        - content structure
        - research requirement
        - visual direction
        - design
        - layout
        - colors
        - theme
        - visual direction

    Quality agents check:
        - duplicate content
        - safety
        - factual reliability
        - overall quality

    Renderer:
        - converts AI design decisions into final images
    """

    # =====================================================
    # INPUT VALIDATION
    # =====================================================

    if not topic or not topic.strip():
        raise ValueError("Topic is required.")

    topic = topic.strip()
    description = (description or "").strip()

    previous_styles = previous_styles or []
    previous_posts = previous_posts or []

    # =====================================================
    # STEP 1 — CONTENT PLANNER
    # =====================================================

    print("\n🧠 STEP 1 — Content Planner")

    planner = plan_social_media_post(
        topic=topic,
        description=description
    )

    # =====================================================
    # STEP 2 — STYLE AGENT
    # =====================================================

    print("\n🎨 STEP 2 — Style Agent")

    style_result = choose_style(
        topic=topic,
        description=description,
        planner_data=planner,
        previous_styles=previous_styles
    )

    selected_style = style_result.get(
        "style",
        planner.get(
            "selected_style",
            "Natural"
        )
    )

    planner["selected_style"] = selected_style

    # =====================================================
    # STEP 3 — RESEARCH AGENT
    # =====================================================

    print("\n🔎 STEP 3 — Research Agent")

    research = research_topic(
        topic=topic,
        planner_data=planner
    )

    # =====================================================
    # STEP 4 — CONTENT GENERATOR
    # =====================================================

    print("\n✍️ STEP 4 — Content Generator")

    niche = planner.get(
        "inferred_niche",
        "General"
    )

    language = planner.get(
        "language",
        "English"
    )

    tone = planner.get(
        "tone",
        "Natural"
    )

    content = generate_post(
        niche=niche,
        topic=topic,
        language=language,
        tone=tone,
        style=selected_style,
        planner_data=planner
    )

    # =====================================================
    # STEP 5 — DUPLICATE CHECK
    # =====================================================

    print("\n♻️ STEP 5 — Duplicate Check")

    new_caption = content.get(
        "caption",
        ""
    )

    previous_captions = _extract_previous_captions(
        previous_posts
    )

    duplicate_result = {
        "is_duplicate": False,
        "similarity": 0.0
    }

    if previous_captions:

        from app.agents.style_agent import check_duplicate

        duplicate_result = check_duplicate(
            new_caption=new_caption,
            previous_captions=previous_captions
        )

    # =====================================================
    # STEP 6 — SAFETY CHECK
    # =====================================================

    print("\n🛡️ STEP 6 — Safety Check")

    news_title = research.get(
        "news_title"
    )

    news_source = research.get(
        "news_source"
    )

    safety_result = check_safety(
        caption=new_caption,
        news_title=news_title,
        news_source=news_source
    )

    # =====================================================
    # STEP 7 — FACT CHECK
    # =====================================================

    print("\n🔎 STEP 7 — Fact Check")

    fact_check_result = fact_check_post(
        caption=new_caption,
        news_title=news_title,
        news_source=news_source
    )

    # =====================================================
    # STEP 8 — QUALITY GATE
    # =====================================================

    print("\n🚦 STEP 8 — Quality Gate")

    quality_issues = []

    # -----------------------------------------------------
    # Duplicate
    # -----------------------------------------------------

    if duplicate_result.get(
        "is_duplicate"
    ):

        quality_issues.append(
            "Generated caption is too similar to previous content."
        )

    # -----------------------------------------------------
    # Safety
    # -----------------------------------------------------

    if not safety_result.get(
        "safe",
        False
    ):

        quality_issues.extend(
            safety_result.get(
                "issues",
                []
            )
        )

    # -----------------------------------------------------
    # Fact Check
    # -----------------------------------------------------

    fact_decision = fact_check_result.get(
        "decision"
    )

    if fact_decision in [
        "review_required",
        "not_verified"
    ]:

        quality_issues.append(
            "Fact verification requires review."
        )

    # -----------------------------------------------------
    # Approval
    # -----------------------------------------------------

    if quality_issues:

        approval_status = "review_required"

    else:

        approval_status = "approved"

    # =====================================================
    # STEP 9 — DESIGN AGENT
    # =====================================================

    print("\n🎯 STEP 9 — Design Agent")

    design_input = {
        **planner,

        "topic": topic,

        "description": description,

        "style_decision": style_result,

        "research": research,

        "generated_content": content,

        "quality": {
            "duplicate": duplicate_result,
            "safety": safety_result,
            "fact_check": fact_check_result,
            "approval_status": approval_status
        }
    }

    design = create_design_plan(
        design_input
    )

    # =====================================================
    # STEP 10 — QUALITY CHECK
    # =====================================================

    print("\n⭐ STEP 10 — Final Quality Check")

    quality_result = check_quality(
        topic=topic,
        description=description,
        content=content,
        planner_data=planner,
        design_data=design
    )

    # =====================================================
    # STEP 11 — POST RENDERER
    # =====================================================

    print("\n🖼️ STEP 11 — Rendering Final Social Post")

    # Renderer receives the COMPLETE AI design plan.
    #
    # It does not decide:
    # - topic
    # - style
    # - theme
    # - colors
    # - layout
    # - number of slides
    #
    # It only implements the Design Agent's decisions.

    rendered_post = render_social_post(
        design_plan=design
    )

    # =====================================================
    # STEP 12 — UPLOAD FINAL RENDERED IMAGES
    # =====================================================

    print("\n☁️ STEP 12 — Uploading Final Images")

    uploaded_images = []

    for image_data in rendered_post.get(
        "images",
        []
    ):

        local_path = image_data.get(
            "path"
        )

        if not local_path:
            continue

        try:

            # Open final rendered image
            # and upload it to Supabase.

            from PIL import Image

            final_image = Image.open(
                local_path
            )

            storage_result = upload_image_to_storage(
                image=final_image,
                folder=f"posts/{rendered_post.get('post_id')}"
            )

            uploaded_images.append(
                {
                    "slide_number": image_data.get(
                        "slide_number"
                    ),
                    "filename": image_data.get(
                        "filename"
                    ),
                    "local_path": local_path,
                    "storage": storage_result
                }
            )

        except Exception as e:

            print(
                f"⚠️ Upload failed for "
                f"{local_path}: {e}"
            )

            uploaded_images.append(
                {
                    "slide_number": image_data.get(
                        "slide_number"
                    ),
                    "filename": image_data.get(
                        "filename"
                    ),
                    "local_path": local_path,
                    "storage": None,
                    "upload_error": str(e)
                }
            )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    print("\n✅ AI PIPELINE COMPLETED")

    return {
        "topic": topic,

        "description": description,

        # -----------------------------
        # AI DECISIONS
        # -----------------------------

        "planner": planner,

        "style": style_result,

        "research": research,

        "content": content,

        "design": design,

        # -----------------------------
        # QUALITY
        # -----------------------------

        "quality": quality_result,

        "quality_gate": {
            "duplicate": duplicate_result,
            "safety": safety_result,
            "fact_check": fact_check_result,
            "approval_status": approval_status,
            "issues": quality_issues
        },

        # -----------------------------
        # FINAL RENDERED POST
        # -----------------------------

        "rendered_post": rendered_post,

        # -----------------------------
        # SUPABASE STORAGE
        # -----------------------------

        "uploaded_images": uploaded_images
    }