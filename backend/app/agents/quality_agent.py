# =========================================================
# QUALITY AGENT
# =========================================================
#
# Purpose:
#
# Generated Post
#      ↓
# Quality Agent
#      ↓
# Check:
#   - Topic relevance
#   - Content completeness
#   - Readability
#   - Repetition
#   - Unsupported promises
#   - Invented offers / CTAs
#   - Hashtag quality
#   - Caption quality
#   - Content/design consistency
#      ↓
# QUALITY PASS / REVIEW REQUIRED
#
# Important:
# - Does NOT fact-check claims.
# - Does NOT replace Safety Agent.
# - Does NOT decide the post format.
# - Does NOT use a fixed topic/category list.
# - AI evaluates the actual generated content.
# =========================================================

import os
import re
import json

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

    # Find JSON object if extra text exists
    if not text.startswith("{"):

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            text = text[start:end + 1]

    try:
        return json.loads(text)

    except Exception:

        # Try removing trailing commas
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
# TEXT HELPERS
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text).strip().lower()
    )


def word_count(text):

    if not text:
        return 0

    return len(
        re.findall(
            r"\b[\w'-]+\b",
            text
        )
    )


def count_hashtags(hashtags):

    if not hashtags:
        return 0

    if isinstance(hashtags, list):

        return len(
            [
                item
                for item in hashtags
                if str(item).strip()
            ]
        )

    if isinstance(hashtags, str):

        return len(
            re.findall(
                r"#\w+",
                hashtags
            )
        )

    return 0


def extract_hashtags(text):

    if not text:
        return []

    return re.findall(
        r"#\w+",
        text
    )


# =========================================================
# BASIC LOCAL QUALITY CHECKS
# =========================================================

def basic_quality_checks(
    topic: str,
    content: dict
):
    """
    Lightweight deterministic checks.

    These run before Groq so obvious problems can be
    detected without spending AI tokens.
    """

    issues = []
    warnings = []

    caption = content.get(
        "caption",
        ""
    )

    hashtags = content.get(
        "hashtags",
        []
    )

    post_idea = content.get(
        "post_idea",
        ""
    )

    # -----------------------------------------------------
    # Caption exists
    # -----------------------------------------------------

    if not caption or not caption.strip():

        issues.append(
            "Caption is empty."
        )

    # -----------------------------------------------------
    # Topic exists
    # -----------------------------------------------------

    if not topic or not topic.strip():

        issues.append(
            "Topic is missing."
        )

    # -----------------------------------------------------
    # Very short caption
    # -----------------------------------------------------

    caption_words = word_count(
        caption
    )

    if caption_words > 0 and caption_words < 5:

        warnings.append(
            "Caption may be too short."
        )

    # -----------------------------------------------------
    # Extremely long caption
    # -----------------------------------------------------

    if caption_words > 500:

        warnings.append(
            "Caption may be unnecessarily long."
        )

    # -----------------------------------------------------
    # Hashtag checks
    # -----------------------------------------------------

    hashtag_count = count_hashtags(
        hashtags
    )

    if hashtag_count == 0:

        warnings.append(
            "No hashtags were generated."
        )

    if hashtag_count > 15:

        issues.append(
            "Too many hashtags were generated."
        )

    # -----------------------------------------------------
    # Post idea
    # -----------------------------------------------------

    if not post_idea:

        warnings.append(
            "Post idea is missing."
        )

    # -----------------------------------------------------
    # Repeated words / phrases
    # -----------------------------------------------------

    words = re.findall(
        r"\b[a-zA-Z]{4,}\b",
        caption.lower()
    )

    word_frequency = {}

    for word in words:

        word_frequency[word] = (
            word_frequency.get(
                word,
                0
            ) + 1
        )

    repeated_words = [
        word
        for word, count in word_frequency.items()
        if count >= 5
    ]

    if repeated_words:

        warnings.append(
            "Some words are repeated excessively."
        )

    # -----------------------------------------------------
    # Duplicate sentences
    # -----------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+",
        caption.strip()
    )

    normalized_sentences = [
        normalize_text(sentence)
        for sentence in sentences
        if sentence.strip()
    ]

    if (
        len(normalized_sentences)
        != len(set(normalized_sentences))
    ):

        issues.append(
            "Caption contains repeated sentences."
        )

    return {
        "issues": issues,
        "warnings": warnings,
        "caption_word_count": caption_words,
        "hashtag_count": hashtag_count,
        "repeated_words": repeated_words
    }


# =========================================================
# AI QUALITY EVALUATION
# =========================================================

def ai_quality_evaluation(
    topic: str,
    description: str,
    planner_data: dict,
    content: dict,
    design_data: dict
):
    """
    AI evaluates the generated post according to
    its actual context.

    No fixed topic/category rules are used.
    """

    if client is None:

        return {
            "decision": "review_required",
            "quality_score": 0.0,
            "reason": (
                "Groq is unavailable. "
                "AI quality evaluation could not run."
            ),
            "issues": [],
            "warnings": [],
            "strengths": [],
            "improvements": [],
            "ai_generated": False,
            "error": "GROQ_API_KEY is missing."
        }

    planner_summary = {
        "inferred_niche":
            planner_data.get(
                "inferred_niche"
            ),

        "audience":
            planner_data.get(
                "audience"
            ),

        "tone":
            planner_data.get(
                "tone"
            ),

        "post_type":
            planner_data.get(
                "post_type"
            ),

        "format":
            planner_data.get(
                "format"
            ),

        "headline":
            planner_data.get(
                "headline"
            ),

        "visual_direction":
            planner_data.get(
                "visual_direction"
            )
    }

    design_summary = {}

    if design_data:

        design_summary = {
            "canvas":
                design_data.get(
                    "canvas"
                ),

            "theme":
                design_data.get(
                    "theme"
                ),

            "global_layout":
                design_data.get(
                    "global_layout"
                ),

            "slides":
                design_data.get(
                    "slides",
                    []
                )
        }

    prompt = f"""
You are the Quality Assurance Agent for an autonomous
AI social media manager.

Your job is to evaluate the generated social media post.

IMPORTANT:
The user gives the intent.
AI decides the content and design.

Do NOT use a fixed list of topics, industries, formats,
styles, or content categories.

Evaluate the actual context of this post.

USER TOPIC:
{topic}

USER DESCRIPTION:
{description}

PLANNER:
{json.dumps(planner_summary, indent=2)}

GENERATED CONTENT:
{json.dumps(content, indent=2)}

DESIGN:
{json.dumps(design_summary, indent=2)}

Evaluate the post on these dimensions:

1. Topic relevance
   - Does the content actually match the user's topic?

2. Audience relevance
   - Is the content appropriate for the intended audience?

3. Content quality
   - Is it useful, meaningful, clear and coherent?
   - Consider the user's actual intent before judging depth.
   - Do not automatically classify a concise caption as an issue
     merely because it does not contain multiple tips or details.
   - For educational or informational topics, concrete information
     is preferred when appropriate, but lack of extra detail should
     normally be an improvement or warning, not an issue.
   - A concise, celebratory, motivational, promotional, awareness,
     announcement, or greeting post can be high quality without
     detailed explanations.

4. Readability
   - Is the language understandable?
   - Avoid unnecessary complexity.

5. Repetition
   - Detect repetitive wording, ideas or sections.

6. Unsupported promises
   - Flag claims such as guaranteed results,
     guaranteed growth, guaranteed income, etc.
   - Do not invent facts.

7. Invented offers
   - Flag fake guides, downloads, discounts,
     products, links, services, consultations,
     resources or offers that the user never supplied.

8. CTA quality
   - A CTA is optional, not mandatory.
   - Do NOT penalize the post merely because it has no CTA.
   - If a CTA exists, check whether it is natural and relevant.
   - Do not invent an actual product/resource/offer.

9. Hashtag quality
   - Relevant to the topic.
   - Not random.
   - Avoid excessive repetition.

10. Content/design consistency
    - Evaluate design consistency ONLY when design
      information is actually provided.
    - If the DESIGN section is empty or unavailable,
      do NOT create an issue because design data is missing.
    - When design information exists, check whether
      the design matches the actual content and topic.
    - Visual direction should make sense for the topic.

11. Overall social-media quality
    - Should feel intentional rather than generic.
    - Avoid meaningless filler.

IMPORTANT CTA RULE:

Absence of a CTA alone must NEVER be classified as an issue.

A post can pass quality evaluation without a CTA.

IMPORTANT DESIGN RULE:

If no design information is provided, do NOT mark
missing design information as an issue.

IMPORTANT SAFETY RULE:

Do NOT mark a sentence as a problem merely because
it is motivational, promotional, celebratory or a CTA.

Examples that are normally acceptable:

"Take control of your digital footprint."

"Ready to improve your online habits?"

"Celebrate the moment."

"Follow for more tips."

However, flag invented factual promises such as:

"Use our free guide to guarantee better results."

"Download our exclusive product."

if such a resource was never provided by the user.

Also:

- Do not fact-check the post here.
- Do not invent corrections.
- Do not create new facts.
- Do not require a specific format.
- Do not require a specific number of slides.
- Judge the generated format based on the user's intent.

SCORING:

Give a quality score from 0 to 1.

Suggested interpretation:

0.90 - 1.00 = excellent
0.80 - 0.89 = good
0.70 - 0.79 = acceptable but can improve
0.50 - 0.69 = review required
below 0.50 = poor

DECISION:

"pass"
if the post is good enough to continue.

"review_required"
if meaningful problems need human/AI correction.

"fail"
only if the post is clearly unusable.

Return ONLY valid JSON.

Schema:

{{
    "decision": "pass",
    "quality_score": 0.90,
    "topic_relevance": 0.95,
    "audience_relevance": 0.90,
    "content_quality": 0.90,
    "readability": 0.90,
    "originality": 0.90,
    "cta_quality": 0.90,
    "hashtag_quality": 0.90,
    "design_consistency": 0.90,
    "issues": [],
    "warnings": [],
    "strengths": [],
    "improvements": [],
    "reason": "Short explanation."
}}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict but practical "
                        "social media quality assurance agent. "
                        "Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=2500
        )

        raw = response.choices[0].message.content

        result = clean_json_response(
            raw
        )

        if not result:

            return {
                "decision": "review_required",
                "quality_score": 0.0,
                "reason": (
                    "AI returned invalid quality evaluation."
                ),
                "issues": [],
                "warnings": [],
                "strengths": [],
                "improvements": [],
                "ai_generated": False,
                "error": "Invalid JSON response."
            }

        # -------------------------------------------------
        # Normalize decision
        # -------------------------------------------------

        decision = str(
            result.get(
                "decision",
                "review_required"
            )
        ).lower().strip()

        if decision not in {
            "pass",
            "review_required",
            "fail"
        }:

            decision = "review_required"

        # -------------------------------------------------
        # Normalize score
        # -------------------------------------------------

        try:

            quality_score = float(
                result.get(
                    "quality_score",
                    0.0
                )
            )

        except Exception:

            quality_score = 0.0

        quality_score = max(
            0.0,
            min(
                1.0,
                quality_score
            )
        )

        # -------------------------------------------------
        # Normalize list fields
        # -------------------------------------------------

        list_fields = [
            "issues",
            "warnings",
            "strengths",
            "improvements"
        ]

        for field in list_fields:

            if not isinstance(
                result.get(field),
                list
            ):

                result[field] = []

        result["decision"] = decision

        result["quality_score"] = round(
            quality_score,
            2
        )

        result["ai_generated"] = True

        return result

    except Exception as error:

        return {
            "decision": "review_required",
            "quality_score": 0.0,
            "reason": (
                "AI quality evaluation failed. "
                "Human review is required."
            ),
            "issues": [],
            "warnings": [],
            "strengths": [],
            "improvements": [],
            "ai_generated": False,
            "error": str(error)
        }


# =========================================================
# MAIN QUALITY CHECK
# =========================================================

def check_quality(
    topic: str,
    content: dict,
    description: str = "",
    planner_data: dict = None,
    design_data: dict = None
):
    """
    Main Quality Agent entry point.

    Compatible with the current AI pipeline.

    Returns:
        {
            decision,
            quality_score,
            basic_checks,
            ai_evaluation,
            issues,
            warnings,
            strengths,
            improvements
        }
    """

    planner_data = (
        planner_data or {}
    )

    design_data = (
        design_data or {}
    )

    content = (
        content or {}
    )

    # -----------------------------------------------------
    # Basic deterministic checks
    # -----------------------------------------------------

    basic_result = basic_quality_checks(
        topic=topic,
        content=content
    )

    # -----------------------------------------------------
    # AI quality evaluation
    # -----------------------------------------------------

    ai_result = ai_quality_evaluation(
        topic=topic,
        description=description,
        planner_data=planner_data,
        content=content,
        design_data=design_data
    )

    # -----------------------------------------------------
    # Combine issues
    # -----------------------------------------------------

    issues = []

    issues.extend(
        basic_result.get(
            "issues",
            []
        )
    )

    issues.extend(
        ai_result.get(
            "issues",
            []
        )
    )

    warnings = []

    warnings.extend(
        basic_result.get(
            "warnings",
            []
        )
    )

    warnings.extend(
        ai_result.get(
            "warnings",
            []
        )
    )

    # -----------------------------------------------------
    # Final decision
    # -----------------------------------------------------

    quality_score = ai_result.get(
        "quality_score",
        0.0
    )

    ai_decision = ai_result.get(
        "decision",
        "review_required"
    )

    if issues:

        final_decision = "review_required"

    elif ai_decision == "fail":

        final_decision = "review_required"

    elif quality_score < 0.70:

        final_decision = "review_required"

    else:

        final_decision = "pass"

    return {

        "decision":
            final_decision,

        "quality_score":
            round(
                quality_score,
                2
            ),

        "basic_checks":
            basic_result,

        "ai_evaluation":
            ai_result,

        "issues":
            issues,

        "warnings":
            warnings,

        "strengths":
            ai_result.get(
                "strengths",
                []
            ),

        "improvements":
            ai_result.get(
                "improvements",
                []
            ),

        "reason":
            ai_result.get(
                "reason",
                "Quality evaluation completed."
            ),

        "ai_generated":
            ai_result.get(
                "ai_generated",
                False
            )
    }


# =========================================================
# SIMPLE ALIAS
# =========================================================

def evaluate_post_quality(
    topic: str,
    content: dict,
    description: str = "",
    planner_data: dict = None,
    design_data: dict = None
):
    """
    Alias for easier use from other modules.
    """

    return check_quality(
        topic=topic,
        content=content,
        description=description,
        planner_data=planner_data,
        design_data=design_data
    )