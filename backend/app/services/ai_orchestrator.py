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
# Supabase Storage
#
# =========================================================

from app.agents.content_planner import plan_social_media_post
from app.agents.style_agent import choose_style
from app.agents.research_agent import research_topic
from app.agents.duplicate_agent import check_duplicate_content
from app.agents.design_agent import create_design_plan
from app.agents.safety_agent import check_safety
from app.agents.fact_check_agent import fact_check_post
from app.agents.quality_agent import check_quality

from app.services.content_generator import generate_post
from app.services.post_renderer import render_social_post
from app.services.storage_service import upload_image_to_storage


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

    Validation agents check:
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
        planner_data=planner,
        research_data=research
    )

    # =====================================================
    # STEP 5 — DUPLICATE CHECK
    # =====================================================

    print("\n♻️ STEP 5 — Duplicate Check")

    # The duplicate agent receives the complete current
    # content plus previous user posts.

    current_content = {
        "topic": topic,
        "caption": content.get("caption", ""),
        "post_idea": content.get("post_idea", ""),
        "hashtags": content.get("hashtags", []),
        "style": selected_style
    }

    duplicate_result = check_duplicate_content(
        current_content=current_content,
        previous_posts=previous_posts
    )

    print(
        f"Duplicate decision: "
        f"{duplicate_result.get('decision')}"
    )

    print(
        f"Similarity: "
        f"{duplicate_result.get('similarity', 0.0)}"
    )

    # =====================================================
    # STEP 6 — SAFETY CHECK
    # =====================================================

    print("\n🛡️ STEP 6 — Safety Check")

    new_caption = content.get(
        "caption",
        ""
    )

    news_title = research.get(
        "news_title"
    ) or research.get(
        "title"
    )

    news_source = research.get(
        "news_source"
    ) or research.get(
        "source"
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

    duplicate_decision = duplicate_result.get(
        "decision"
    )

    if duplicate_decision == "regenerate_required":

        quality_issues.append(
            "Generated content is too similar to previous content."
        )

    elif duplicate_decision == "review_required":

        quality_issues.append(
            "Generated content has noticeable similarity to previous content."
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
    # Approval Status
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
    # STEP 10 — FINAL QUALITY CHECK
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