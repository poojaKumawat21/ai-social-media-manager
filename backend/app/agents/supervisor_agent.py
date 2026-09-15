# =========================================================
# SUPERVISOR AGENT
# =========================================================
#
# Main responsibility:
#
# Research
#    ↓
# Generate Post
#    ↓
# Duplicate Check
#    ↓
# Safety Check
#    ↓
# Fact Check
#    ↓
# ┌──────────────────────────────┐
# │ All checks passed            │ → Save Post
# │ Any important check failed   │ → Human Review
# └──────────────────────────────┘
#
# This agent coordinates all other agents.
# =========================================================


# ---------------------------------------------------------
# IMPORT AGENTS
# ---------------------------------------------------------

# Research Agent
# Finds latest news related to the user's topic.
from app.agents.research_agent import research_tech_news


# Safety Agent
# Checks whether the generated content contains
# sensitive or unsafe topics.
from app.agents.safety_agent import check_safety


# Fact Check Agent
# Verifies factual claims using available evidence
# and source quality.
from app.agents.fact_check_agent import fact_check_post


# Style Agent
# Chooses different styles and checks duplicate content.
from app.agents.style_agent import (
    choose_style,
    check_post_against_history
)


# ---------------------------------------------------------
# CONTENT GENERATION SERVICES
# ---------------------------------------------------------

# Generates normal AI posts and news-based AI posts.
from app.services.content_generator import (
    generate_post,
    generate_post_from_news
)


# ---------------------------------------------------------
# DATABASE SERVICES
# ---------------------------------------------------------

# Get previous posts from Supabase
# and save newly generated posts.
from app.services.post_service import (
    get_previous_posts,
    save_post
)


# =========================================================
# AUTONOMOUS AGENT
# =========================================================

def run_autonomous_agent(
    niche: str,
    topic: str,
    language: str = "English",
    tone: str = "Professional",
    previous_styles=None,
    profile_id=None
):

    # -----------------------------------------------------
    # 1. GET PREVIOUS POSTS
    # -----------------------------------------------------
    #
    # We first get previous posts from the database.
    #
    # Why?
    #
    # To make sure the AI does not repeatedly generate
    # the same content or same style.
    # -----------------------------------------------------

    previous_posts = get_previous_posts(
        profile_id=profile_id,
        limit=20
    )


    # -----------------------------------------------------
    # 2. FIND PREVIOUSLY USED STYLES
    # -----------------------------------------------------
    #
    # Example:
    #
    # Previous posts:
    # Educational
    # Funny
    # Tips
    #
    # The Style Agent can choose another style.
    # -----------------------------------------------------

    used_styles = [
        post.get("style")
        for post in previous_posts
        if post.get("style")
    ]


    # -----------------------------------------------------
    # 3. CHOOSE NEW STYLE
    # -----------------------------------------------------
    #
    # Style Agent decides which style should be used.
    #
    # Example styles:
    #
    # Educational
    # Funny
    # Tips
    # Storytelling
    # Professional
    # Question
    # Trending
    # -----------------------------------------------------

    style = choose_style(
        previous_styles=used_styles
    )


    # -----------------------------------------------------
    # 4. RESEARCH LATEST NEWS
    # -----------------------------------------------------
    #
    # Research Agent searches for latest news related
    # to the user's topic.
    #
    # Example:
    #
    # niche = Artificial Intelligence
    # topic = AI Agents
    #
    # The agent searches for relevant latest news.
    # -----------------------------------------------------

    news = research_tech_news(topic)


    # =====================================================
    # 5. GENERATE + CHECK POST
    # =====================================================
    #
    # We allow maximum 3 attempts.
    #
    # Why?
    #
    # If the first generated post is duplicate,
    # AI gets another chance to create a different post.
    # =====================================================

    for attempt in range(3):


        # -------------------------------------------------
        # 5A. GENERATE NEWS-BASED POST
        # -------------------------------------------------
        #
        # If relevant news was found, generate a post
        # based on the latest news.
        # -------------------------------------------------

        if news:

            latest_news = news[0]


            post = generate_post_from_news(
                news_title=latest_news["title"],
                news_source=latest_news["source"],
                niche=niche,
                language=language,
                tone=tone,
                style=style
            )


            # Store news information inside the post.
            post["news_title"] = latest_news["title"]

            post["news_source"] = latest_news["source"]


        # -------------------------------------------------
        # 5B. GENERATE NORMAL POST
        # -------------------------------------------------
        #
        # If no relevant news is found,
        # generate a normal AI post.
        # -------------------------------------------------

        else:

            post = generate_post(
                niche=niche,
                topic=topic,
                language=language,
                tone=tone,
                style=style
            )


            # No news was used for this post.
            post["news_title"] = None

            post["news_source"] = None


        # =================================================
        # 6. DUPLICATE CHECK
        # =================================================
        #
        # Compare the newly generated caption against
        # previous posts stored in the database.
        #
        # Example:
        #
        # New caption
        #       ↓
        # Compare with previous 20 posts
        #       ↓
        # Similarity >= threshold?
        #
        # Yes → Duplicate
        # No  → Unique
        # =================================================

        duplicate_result = check_post_against_history(
            new_caption=post["caption"],
            previous_posts=previous_posts
        )


        # =================================================
        # 7. SAFETY CHECK
        # =================================================
        #
        # Safety Agent checks:
        #
        # - Empty caption
        # - Missing news source
        # - Sensitive topics
        # - Other configured safety rules
        # =================================================

        safety_result = check_safety(
            caption=post["caption"],
            news_title=post.get("news_title"),
            news_source=post.get("news_source")
        )


        # =================================================
        # 8. FACT CHECK
        # =================================================
        #
        # Fact Check Agent verifies factual claims.
        #
        # It can return:
        #
        # verified
        # review_required
        # not_verified
        #
        # For autonomous publishing, we only allow
        # verified content to continue automatically.
        # =================================================

        fact_check_result = fact_check_post(
            caption=post["caption"],
            news_title=post.get("news_title"),
            news_source=post.get("news_source")
        )


        # =================================================
        # 9. FINAL AUTOMATIC DECISION
        # =================================================
        #
        # Post will be saved automatically ONLY when:
        #
        # 1. It is NOT a duplicate
        # 2. Safety check passed
        # 3. Fact check is verified
        #
        # Otherwise it goes to human review.
        # =================================================

        if (
            not duplicate_result["is_duplicate"]
            and safety_result["safe"]
            and fact_check_result["verified"]
        ):


            # -------------------------------------------------
            # 10. PREPARE DATABASE RECORD
            # -------------------------------------------------

            post_data = {
                "profile_id": profile_id,

                "niche": niche,

                "topic": topic,

                "caption": post["caption"],

                "hashtags": post["hashtags"],

                "post_idea": post["post_idea"],

                "style": style,

                "language": language,

                "tone": tone,

                "news_title": post["news_title"],

                "news_source": post["news_source"],

                # Current status.
                # Later this can become:
                #
                # draft
                # review_required
                # approved
                # scheduled
                # published
                #
                "status": "generated"
            }


            # -------------------------------------------------
            # 11. SAVE VERIFIED POST
            # -------------------------------------------------

            saved_post = save_post(
                post_data
            )


            # -------------------------------------------------
            # 12. RETURN SUCCESS
            # -------------------------------------------------
            #
            # We return all check results so the frontend
            # can display them later.
            # -------------------------------------------------

            return {

                "status": "success",

                "decision": "unique_safe_verified_post",

                "attempt": attempt + 1,

                "duplicate_check": duplicate_result,

                "safety_check": safety_result,

                "fact_check": fact_check_result,

                "post": post,

                "saved_post": saved_post
            }


        # =================================================
        # 13. HUMAN REVIEW
        # =================================================
        #
        # If ANY important check fails, do NOT automatically
        # publish/save it as an approved autonomous post.
        #
        # It goes for human review.
        # =================================================

        if (
            duplicate_result["is_duplicate"]
            or not safety_result["safe"]
            or not fact_check_result["verified"]
        ):


            return {

                "status": "review_required",

                "decision": "human_review",

                "attempt": attempt + 1,

                "duplicate_check": duplicate_result,

                "safety_check": safety_result,

                "fact_check": fact_check_result,

                "post": post
            }


    # =====================================================
    # 14. ALL ATTEMPTS FAILED
    # =====================================================
    #
    # If all 3 attempts fail because of duplicate content,
    # return a failed result.
    # =====================================================

    return {

        "status": "failed",

        "decision": "duplicate_detected",

        "message": (
            "Could not generate a sufficiently unique "
            "post after 3 attempts."
        )
    }


# =========================================================
# BASIC SUPERVISOR AGENT
# =========================================================
#
# This function is kept because your existing backend
# may already be using /supervisor endpoint.
#
# It performs:
#
# Research → News Post OR Normal Post
#
# The full autonomous workflow above is handled by
# run_autonomous_agent().
# =========================================================

def run_supervisor(
    niche: str,
    topic: str,
    language: str = "English",
    tone: str = "Professional",
    style: str = "Educational"
):

    # -----------------------------------------------------
    # 1. RESEARCH LATEST NEWS
    # -----------------------------------------------------

    news = research_tech_news(
        topic
    )


    # -----------------------------------------------------
    # 2. IF NEWS EXISTS → NEWS-BASED POST
    # -----------------------------------------------------

    if news:

        latest_news = news[0]


        post = generate_post_from_news(
            news_title=latest_news["title"],
            news_source=latest_news["source"],
            niche=niche,
            language=language,
            tone=tone,
            style=style
        )


        return {

            "decision": "news_based_post",

            "reason": (
                "Relevant latest news was found."
            ),

            "news": latest_news,

            "post": post
        }


    # -----------------------------------------------------
    # 3. IF NO NEWS → NORMAL AI POST
    # -----------------------------------------------------

    post = generate_post(
        niche=niche,
        topic=topic,
        language=language,
        tone=tone,
        style=style
    )


    return {

        "decision": "normal_post",

        "reason": (
            "No relevant news was found."
        ),

        "news": None,

        "post": post
    }