# =========================================================
# STYLE + DUPLICATE AGENT
# =========================================================
#
# Responsibilities:
#
# Planner output
#      ↓
# AI decides suitable style
#      ↓
# Check previous styles
#      ↓
# Avoid unnecessary repetition
#      ↓
# Return final style decision
#
# Also provides caption duplicate detection.
#
# Important:
# - No fixed topic/category list.
# - AI decides the style from the actual content.
# - User does not need to select a style.
# - Previous history is used to improve variation.
# =========================================================

import os
import json
import re

from difflib import SequenceMatcher
from dotenv import load_dotenv
from groq import Groq


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None

if GROQ_API_KEY:
    client = Groq(
        api_key=GROQ_API_KEY
    )


# =========================================================
# JSON CLEANER
# =========================================================

def clean_json_response(raw_text: str):

    if not raw_text:
        return {}

    text = raw_text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # Extract JSON object if extra text exists
    if not text.startswith("{"):

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            text = text[start:end + 1]

    # Remove trailing commas
    text = re.sub(
        r",\s*([}\]])",
        r"\1",
        text
    )

    try:
        return json.loads(text)

    except Exception:
        return {}


# =========================================================
# AI STYLE DECISION
# =========================================================

def choose_style(
    topic: str = "",
    description: str = "",
    planner_data: dict = None,
    previous_styles=None
):
    """
    Let AI decide the most suitable style.

    The AI considers:
        - topic
        - user description
        - niche
        - audience
        - tone
        - post type
        - format
        - visual direction
        - previously used styles

    No fixed style list is used.
    """

    planner_data = planner_data or {}
    previous_styles = previous_styles or []

    previous_styles = [
        style
        for style in previous_styles
        if style
    ]

    # -----------------------------------------------------
    # Build planner context
    # -----------------------------------------------------

    planner_context = {
        "topic": topic,
        "description": description,

        "niche": planner_data.get(
            "inferred_niche"
        ),

        "audience": planner_data.get(
            "audience"
        ),

        "tone": planner_data.get(
            "tone"
        ),

        "selected_style": planner_data.get(
            "selected_style"
        ),

        "post_type": planner_data.get(
            "post_type"
        ),

        "format": planner_data.get(
            "format"
        ),

        "headline": planner_data.get(
            "headline"
        ),

        "visual_direction": planner_data.get(
            "visual_direction"
        ),

        "design_layout": planner_data.get(
            "design_layout"
        )
    }

    # -----------------------------------------------------
    # If AI is unavailable, use planner's decision.
    # -----------------------------------------------------

    if client is None:

        planner_style = planner_data.get(
            "selected_style"
        )

        if planner_style:
            return {
                "style": planner_style,
                "reason": (
                    "Used the style selected by "
                    "the content planner because "
                    "the AI style service is unavailable."
                ),
                "ai_generated": False
            }

        return {
            "style": "Natural",
            "reason": (
                "No AI style decision was available."
            ),
            "ai_generated": False
        }

    # -----------------------------------------------------
    # AI PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are the Style Decision Agent for an autonomous
AI social media manager.

The user should NOT have to manually select a style.

Your job is to understand the actual content and decide
what visual/content style will communicate it best.

USER INPUT:
{json.dumps({
    "topic": topic,
    "description": description
}, indent=2)}

CONTENT PLANNER:
{json.dumps(
    planner_context,
    indent=2
)}

RECENTLY USED STYLES:
{json.dumps(previous_styles, indent=2)}

IMPORTANT RULES:

1. Decide the style from the meaning and purpose
   of the content.

2. Do NOT use a fixed predefined style list.

3. You may create a new descriptive style when
   appropriate.

4. The style should make sense for the topic,
   audience, tone and format.

5. Avoid repeating a recently used style when another
   suitable direction would improve variation.

6. Do not change the actual topic or meaning.

7. Do not invent factual claims.

8. Do not select a style merely because it is popular.

9. A simple greeting, celebration or visual message
   may use a simple visual style.

10. Educational information may use an explanatory,
    editorial, infographic, storytelling or another
    appropriate visual direction.

11. A humorous topic may use a playful/comedic style.

12. A professional announcement may use a refined,
    editorial or corporate visual direction.

These are examples only.
They are NOT a fixed list.

Think about:
- communication goal
- audience expectations
- emotional impact
- readability
- visual storytelling
- topic context
- platform suitability
- variation from recent posts

Return ONLY valid JSON.

Required format:

{{
    "style": "short descriptive style name",
    "reason": "Why this style is appropriate.",
    "variation_note": "How this differs from recent styles."
}}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a creative but disciplined "
                        "social media style decision agent."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.65,
            max_tokens=1000
        )

        raw_text = response.choices[0].message.content

        result = clean_json_response(
            raw_text
        )

        style = result.get(
            "style"
        )

        if not style:
            style = planner_data.get(
                "selected_style",
                "Natural"
            )

        return {
            "style": style,
            "reason": result.get(
                "reason",
                "AI selected the style based on the content."
            ),
            "variation_note": result.get(
                "variation_note",
                ""
            ),
            "ai_generated": True
        }

    except Exception as error:

        # Safe fallback to planner
        planner_style = planner_data.get(
            "selected_style"
        )

        return {
            "style": (
                planner_style
                if planner_style
                else "Natural"
            ),
            "reason": (
                "Style AI was unavailable, so the "
                "planner decision was used."
            ),
            "variation_note": "",
            "ai_generated": False,
            "error": str(error)
        }


# =========================================================
# CAPTION DUPLICATE CHECK
# =========================================================

def check_duplicate(
    new_caption,
    previous_captions=None,
    threshold=0.80
):
    """
    Check whether a new caption is too similar
    to previous captions.
    """

    if not new_caption:
        return {
            "is_duplicate": False,
            "similarity": 0.0
        }

    if not previous_captions:
        return {
            "is_duplicate": False,
            "similarity": 0.0
        }

    new_caption = (
        new_caption
        .lower()
        .strip()
    )

    highest_similarity = 0.0

    for old_caption in previous_captions:

        if not old_caption:
            continue

        old_caption = (
            old_caption
            .lower()
            .strip()
        )

        similarity = SequenceMatcher(
            None,
            new_caption,
            old_caption
        ).ratio()

        highest_similarity = max(
            highest_similarity,
            similarity
        )

    return {
        "is_duplicate": (
            highest_similarity >= threshold
        ),
        "similarity": round(
            highest_similarity,
            2
        )
    }


# =========================================================
# CHECK POST AGAINST HISTORY
# =========================================================

def check_post_against_history(
    new_caption,
    previous_posts
):
    """
    Check a new caption against posts
    stored in Supabase.
    """

    previous_captions = [
        post.get("caption")
        for post in previous_posts
        if post.get("caption")
    ]

    return check_duplicate(
        new_caption=new_caption,
        previous_captions=previous_captions
    )