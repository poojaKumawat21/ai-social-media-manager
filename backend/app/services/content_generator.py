import os
import json
import re
import time

from groq import Groq
from google import genai
from dotenv import load_dotenv


load_dotenv(".env")


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")


client = Groq(
    api_key=GROQ_API_KEY
)

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# Helper: Groq Completion With Rate-Limit Handling
# =========================================================

# =========================================================
# Helper: Groq Completion With Gemini Fallback
# =========================================================

# =========================================================
# Helper: Groq Completion With Gemini Fallback
# =========================================================

def create_groq_completion(
    messages,
    temperature=0.65,
    max_retries=2,
):
    """
    Try Groq first.

    If Groq hits a temporary rate limit/server error,
    retry briefly and then fall back to Gemini.

    Gemini also gets its own retry handling for temporary
    503/429/500/502/504 errors.

    Existing callers continue receiving a response object
    with the same structure:

        response.choices[0].message.content
    """

    last_error = None

    # =====================================================
    # 1. TRY GROQ
    # =====================================================

    for attempt in range(max_retries + 1):

        try:

            return client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=temperature,
            )

        except Exception as exc:

            last_error = exc

            error_text = str(exc).lower()

            is_rate_limit = (
                "429" in error_text
                or "rate limit" in error_text
                or "too many requests" in error_text
            )

            is_temporary_server_error = any(
                code in error_text
                for code in [
                    "500",
                    "502",
                    "503",
                    "504",
                ]
            )

            # ---------------------------------------------
            # Do not fallback for unrelated errors.
            # ---------------------------------------------

            if not (
                is_rate_limit
                or is_temporary_server_error
            ):
                raise

            # ---------------------------------------------
            # Groq retries exhausted
            # ---------------------------------------------

            if attempt >= max_retries:
                break

            wait_seconds = 2 ** attempt

            print(
                f"⚠️ Groq temporary error. "
                f"Retrying in {wait_seconds}s "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            time.sleep(wait_seconds)

    # =====================================================
    # 2. GROQ FAILED → GEMINI FALLBACK
    # =====================================================

    print(
        "🔄 Groq unavailable. "
        "Switching to Gemini fallback..."
    )

    # -----------------------------------------------------
    # Build Gemini prompt
    # -----------------------------------------------------

    system_instruction = ""

    user_parts = []

    for message in messages:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        if role == "system":

            system_instruction += (
                str(content)
                + "\n"
            )

        elif role == "user":

            user_parts.append(
                str(content)
            )

    combined_prompt = "\n\n".join(
        user_parts
    )

    # =====================================================
    # 3. GEMINI RETRY
    # =====================================================

    gemini_max_retries = 3
    gemini_last_error = None

    for gemini_attempt in range(
        gemini_max_retries + 1
    ):

        try:

            print(
                f"🤖 Gemini attempt "
                f"{gemini_attempt + 1}/"
                f"{gemini_max_retries + 1}"
            )

            response = (
                gemini_client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=combined_prompt,
                    config={
                        "system_instruction": (
                            system_instruction.strip()
                        ),
                        "temperature": temperature,
                        "max_output_tokens": 3000,
                    },
                )
            )

            gemini_text = response.text

            if not gemini_text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            print(
                "✅ Gemini fallback completed successfully."
            )

            # =================================================
            # Create Groq-compatible response structure
            # =================================================

            class GeminiMessage:

                def __init__(self, content):
                    self.content = content

            class GeminiChoice:

                def __init__(self, message):
                    self.message = message

            class GeminiResponse:

                def __init__(self, content):

                    self.choices = [
                        GeminiChoice(
                            GeminiMessage(content)
                        )
                    ]

            return GeminiResponse(
                gemini_text
            )

        except Exception as gemini_error:

            gemini_last_error = gemini_error

            error_text = str(
                gemini_error
            ).lower()

            is_gemini_temporary_error = (
                "429" in error_text
                or "503" in error_text
                or "500" in error_text
                or "502" in error_text
                or "504" in error_text
                or "unavailable" in error_text
                or "high demand" in error_text
                or "resource exhausted" in error_text
                or "rate limit" in error_text
            )

            # ---------------------------------------------
            # Permanent Gemini error
            # ---------------------------------------------

            if not is_gemini_temporary_error:

                print(
                    "❌ Gemini fallback failed "
                    "with a non-retryable error."
                )

                print(
                    f"Gemini error: {gemini_error}"
                )

                raise

            # ---------------------------------------------
            # Gemini temporary error
            # ---------------------------------------------

            if (
                gemini_attempt
                >= gemini_max_retries
            ):

                break

            wait_seconds = min(
                2 ** gemini_attempt,
                8
            )

            print(
                f"⚠️ Gemini temporary error. "
                f"Retrying in {wait_seconds}s..."
            )

            print(
                f"Gemini error: {gemini_error}"
            )

            time.sleep(
                wait_seconds
            )

    # =====================================================
    # 4. BOTH PROVIDERS FAILED
    # =====================================================

    print(
        "❌ Gemini fallback failed "
        "after all retry attempts."
    )

    if gemini_last_error:

        print(
            f"Gemini final error: "
            f"{gemini_last_error}"
        )

    # Preserve existing error behavior.
    # This means callers still receive the original
    # Groq error if both providers are unavailable.

    if last_error:
        raise last_error

    if gemini_last_error:
        raise gemini_last_error

    raise RuntimeError(
        "Both Groq and Gemini failed."
    )
# =========================================================
# Helper: Clean AI JSON Response
# =========================================================

def clean_json_response(raw_text: str):

    raw_text = raw_text.strip()

    if raw_text.startswith("```"):

        raw_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw_text,
            flags=re.IGNORECASE
        )

        raw_text = re.sub(
            r"\s*```$",
            "",
            raw_text
        )

    raw_text = raw_text.strip()

    if not raw_text.startswith("{"):

        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}")

        if (
            json_start != -1
            and json_end != -1
            and json_end > json_start
        ):
            raw_text = raw_text[
                json_start:json_end + 1
            ]

    return json.loads(raw_text)


# =========================================================
# Helper: Normalize Platform
# =========================================================

def normalize_platform(platform="general"):
    """
    Safely normalize the requested platform.

    Existing callers that do not provide a platform
    continue using "general".
    """

    platform = (
        platform or "general"
    ).strip().lower()

    allowed_platforms = {
        "instagram",
        "linkedin",
        "facebook",
        "x",
        "general",
    }

    if platform not in allowed_platforms:
        return "general"

    return platform


# =========================================================
# Helper: Normalize Hashtags
# =========================================================

def normalize_hashtags(
    hashtags,
    platform="general"
):

    if not isinstance(hashtags, list):
        return []

    platform = normalize_platform(
        platform
    )

    cleaned = []

    for tag in hashtags:

        if not isinstance(tag, str):
            continue

        tag = tag.strip()

        if not tag:
            continue

        if not tag.startswith("#"):
            tag = "#" + tag

        if tag not in cleaned:
            cleaned.append(tag)

    limits = {
        "instagram": 5,
        "linkedin": 3,
        "facebook": 5,
        "x": 2,
        "general": 5,
    }

    return cleaned[
        :limits.get(platform, 5)
    ]


# =========================================================
# Helper: Safe Text
# =========================================================

def safe_text(
    value,
    default=""
):

    if value is None:
        return default

    if not isinstance(value, str):
        return str(value)

    return value.strip()


# =========================================================
# Helper: Platform Rules
# =========================================================

def get_platform_content_rules(
    platform="general"
):

    platform = normalize_platform(
        platform
    )

    rules = {

        "instagram": """
- Write for Instagram users.
- Make the caption visually engaging and mobile-friendly.
- Use a conversational social-media style.
- The opening should be attention-grabbing.
- Keep paragraphs short and easy to scan.
- Hashtags should be highly relevant to the topic.
- Do not write like a LinkedIn article.
- Do not use excessive professional/business language.
- The caption should complement the visual rather than repeat every visual detail.
""",

        "linkedin": """
- Write for LinkedIn users.
- Use professional, insightful and value-oriented language.
- Prioritize useful context and professional readability.
- Use short paragraphs for easy feed reading.
- Focus on the insight, lesson, implication or professional relevance.
- Avoid excessive promotional language.
- Avoid Instagram-style phrasing.
- Avoid emoji-heavy writing.
- Do not make unsupported professional claims.
""",

        "facebook": """
- Write for Facebook users.
- Keep the language conversational and approachable.
- Make the content easy to read on mobile.
- Encourage natural discussion when appropriate.
- Keep the message understandable without requiring the visual.
- Avoid sounding like a formal LinkedIn article.
""",

        "x": """
- Write for X users.
- Keep the message concise.
- Make the opening immediately meaningful.
- Avoid unnecessary long-form explanation.
- Focus on one clear idea.
- Use only highly relevant hashtags.
- Do not add filler just to increase length.
""",

        "general": """
- Create natural social-media content.
- Keep the content concise, clear and engaging.
- Match the requested tone, language and style.
"""
    }

    return rules.get(
        platform,
        rules["general"]
    )


# =========================================================
# Helper: Platform Hashtag Fallback
# =========================================================

def get_hashtag_fallbacks(
    topic,
    platform="general"
):

    platform = normalize_platform(
        platform
    )

    topic_clean = re.sub(
        r"[^a-zA-Z0-9]",
        "",
        str(topic)
    )

    if platform == "instagram":

        return [
            f"#{topic_clean}",
            "#Instagram",
            "#ContentCreation",
            "#DigitalContent",
            "#AI"
        ]

    if platform == "linkedin":

        return [
            f"#{topic_clean}",
            "#LinkedIn",
            "#Technology",
            "#Innovation",
            "#AI"
        ]

    if platform == "facebook":

        return [
            f"#{topic_clean}",
            "#Facebook",
            "#ContentCreation",
            "#Technology",
            "#AI"
        ]

    if platform == "x":

        return [
            f"#{topic_clean}",
            "#AI"
        ]

    return [
        f"#{topic_clean}",
        "#SocialMedia",
        "#ContentCreation",
        "#DigitalContent",
        "#AI"
    ]


# =========================================================
# Generate Normal Social Media Post
# =========================================================

def generate_post(
    niche,
    topic,
    language,
    tone,
    style,
    planner_data=None,
    research_data=None,
    platform="general"
):

    planner_data = planner_data or {}
    research_data = research_data or {}

    # -----------------------------------------------------
    # Normalize platform safely
    # -----------------------------------------------------

    platform = normalize_platform(
        platform or planner_data.get("platform")
    )

    platform_rules = get_platform_content_rules(
        platform
    )

    # -----------------------------------------------------
    # Read AI planner decisions
    # -----------------------------------------------------

    post_type = planner_data.get(
        "post_type",
        planner_data.get(
            "format",
            "single_post"
        )
    )

    post_format = planner_data.get(
        "format",
        "single_post"
    )

    headline = planner_data.get(
        "headline",
        ""
    )

    subheadline = planner_data.get(
        "subheadline",
        ""
    )

    introduction = planner_data.get(
        "introduction",
        ""
    )

    sections = planner_data.get(
        "sections",
        []
    )

    key_takeaway = planner_data.get(
        "key_takeaway",
        ""
    )

    cta = planner_data.get(
        "CTA",
        planner_data.get(
            "cta",
            ""
        )
    )

    requires_research = planner_data.get(
        "requires_research",
        False
    )

    source_required = planner_data.get(
        "source_required",
        False
    )

    # -----------------------------------------------------
    # Build structure context
    # -----------------------------------------------------

    structure_context = {

        "post_type": post_type,

        "format": post_format,

        "headline": headline,

        "subheadline": subheadline,

        "introduction": introduction,

        "sections": sections,

        "section_count": len(sections),

        "key_takeaway": key_takeaway,

        "cta": cta,

        "requires_research": requires_research,

        "source_required": source_required,

        "platform": platform
    }

    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    prompt = f"""
You are the CONTENT AGENT inside an autonomous
AI social media manager.

Your job is to create the actual social media content
from the decisions already made by the AI Content Planner.

IMPORTANT PRINCIPLE:

The planner has already decided the intended structure.
You MUST follow that structure consistently.

The caption, post_idea and content description MUST
describe the SAME content structure.

Do NOT independently change the number of steps,
tips, sections, items, slides or points.

---------------------------------------------------------
USER INPUT
---------------------------------------------------------

Niche:
{niche}

Topic:
{topic}

Language:
{language}

Tone:
{tone}

Style:
{style}

Platform:
{platform}

---------------------------------------------------------
AI PLANNER DECISION
---------------------------------------------------------

{json.dumps(
    structure_context,
    ensure_ascii=False,
    indent=2
)}

---------------------------------------------------------
PLATFORM-SPECIFIC REQUIREMENTS
---------------------------------------------------------

The same topic may be published on different platforms.

You MUST create content specifically for the requested
platform while preserving the planner's structure.

Platform:
{platform}

{platform_rules}

IMPORTANT:

Platform-specific adaptation means changing the way the
content is communicated for that platform.

It does NOT mean changing:
- the planner's sections
- the factual meaning
- the number of items
- the selected post format
- the intended topic
- the planner's CTA decision

---------------------------------------------------------
CONTENT RULES
---------------------------------------------------------

1. Respect the planner's actual intent.

2. If the planner selected SINGLE POST:
   - Create one concise social media message.
   - Do NOT force a list.
   - Do NOT invent numbered steps.
   - Do NOT mention a number of tips/items unless
     the planner explicitly contains that number.

3. If the planner selected CAROUSEL:
   - Follow the planner's sections.
   - Treat the number of planner sections as the intended
     content structure.
   - If there are N sections, any caption referring to
     the number of steps/tips/ideas MUST say N.
   - Do not change N.
   - Do not invent extra sections.
   - Do not remove sections unless absolutely necessary
     for coherence.

4. NUMERIC CONSISTENCY IS MANDATORY.

5. The post_idea MUST describe the SAME content
   that the caption and planner describe.

6. Do NOT invent:
   - products
   - guides
   - downloadable resources
   - discounts
   - offers
   - links
   - statistics
   - achievements
   - studies
   - factual claims
   - events
   - organizations

   unless they are provided by the planner/research
   context.

7. CTA is optional.

   If the planner has no CTA:
   - do not invent one
   - a natural caption can end without a CTA.

8. Keep the caption engaging but natural.

9. Avoid generic filler.

10. Match the requested language, tone and style.

11. Do not use markdown.

12. Do not add emojis unless they naturally fit.

13. Generate relevant hashtags appropriate for the
    selected platform.

14. Hashtags must match the actual topic.

15. Do not create platform-specific hashtags that are
    unrelated to the actual topic.

---------------------------------------------------------
HASHTAG REQUIREMENT
---------------------------------------------------------

Instagram:
5 hashtags

LinkedIn:
3 hashtags

Facebook:
5 hashtags

X:
2 hashtags

General:
5 hashtags

Return the appropriate number for the selected platform.

---------------------------------------------------------
OUTPUT
---------------------------------------------------------

Return ONLY valid JSON.

Use exactly this structure:

{{
    "caption": "final social media caption",
    "hashtags": [
        "#hashtag1",
        "#hashtag2",
        "#hashtag3"
    ],
    "post_idea": "short description that accurately matches the planner and caption"
}}

Do not include anything outside the JSON.
"""

    # -----------------------------------------------------
    # Groq Content Generation
    # -----------------------------------------------------

    response = create_groq_completion(

        messages=[

            {
                "role": "system",
                "content": (
                    "You are the Content Agent of an autonomous "
                    "social media manager. Follow planner decisions "
                    "exactly and maintain strict consistency between "
                    "caption, post idea and content structure. "
                    "Adapt the communication style to the requested "
                    "platform without changing the planner's intent."
                )
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.65,
    )

    raw_content = response.choices[0].message.content

    result = clean_json_response(
        raw_content
    )

    # -----------------------------------------------------
    # Platform-specific hashtag normalization
    # -----------------------------------------------------

    hashtags = normalize_hashtags(
        result.get("hashtags", []),
        platform=platform
    )

    hashtag_limit = {
        "instagram": 5,
        "linkedin": 3,
        "facebook": 5,
        "x": 2,
        "general": 5,
    }.get(
        platform,
        5
    )

    # -----------------------------------------------------
    # Hashtag fallback
    # -----------------------------------------------------

    if len(hashtags) < hashtag_limit:

        generated = get_hashtag_fallbacks(
            topic=topic,
            platform=platform
        )

        for tag in generated:

            if tag not in hashtags:
                hashtags.append(tag)

            if len(hashtags) == hashtag_limit:
                break

    # -----------------------------------------------------
    # FINAL CONTENT RESULT
    # -----------------------------------------------------

    return {

        "caption": safe_text(
            result.get(
                "caption",
                ""
            )
        ),

        "hashtags": hashtags[:hashtag_limit],

        "post_idea": safe_text(
            result.get(
                "post_idea",
                ""
            )
        ),

        "style": style,

        "language": language,

        "tone": tone,

        "niche": niche,

        "topic": topic,

        # IMPORTANT:
        # Always return the actual selected platform.
        "platform": platform,

        "content_structure": {

            "post_type": post_type,

            "format": post_format,

            "section_count": len(sections)
        }
    }


# =========================================================
# Generate Post From News
# =========================================================

def generate_post_from_news(
    news_title,
    news_source,
    niche="Technology",
    language="English",
    tone="Professional",
    style="Educational",
    planner_data=None,
    research_data=None,
    platform="general"
):

    planner_data = planner_data or {}
    research_data = research_data or {}

    # -----------------------------------------------------
    # Normalize platform safely
    # -----------------------------------------------------

    platform = normalize_platform(
        platform or planner_data.get("platform")
    )

    platform_rules = get_platform_content_rules(
        platform
    )

    # -----------------------------------------------------
    # Research context
    # -----------------------------------------------------

    research_summary = research_data.get(
        "summary",
        research_data.get(
            "news_summary",
            ""
        )
    )

    facts = research_data.get(
        "facts",
        []
    )

    sources = research_data.get(
        "sources",
        []
    )

    # -----------------------------------------------------
    # Planner structure
    # -----------------------------------------------------

    post_type = planner_data.get(
        "post_type",
        planner_data.get(
            "format",
            "single_post"
        )
    )

    post_format = planner_data.get(
        "format",
        "single_post"
    )

    sections = planner_data.get(
        "sections",
        []
    )

    structure_context = {

        "post_type": post_type,

        "format": post_format,

        "headline": planner_data.get(
            "headline",
            ""
        ),

        "subheadline": planner_data.get(
            "subheadline",
            ""
        ),

        "introduction": planner_data.get(
            "introduction",
            ""
        ),

        "sections": sections,

        "section_count": len(sections),

        "key_takeaway": planner_data.get(
            "key_takeaway",
            ""
        ),

        "cta": planner_data.get(
            "CTA",
            planner_data.get(
                "cta",
                ""
            )
        ),

        "platform": platform
    }

    # -----------------------------------------------------
    # News prompt
    # -----------------------------------------------------

    prompt = f"""
You are the CONTENT AGENT of an autonomous social
media manager specializing in responsible news content.

Create a social media post based ONLY on the supplied
news and research evidence.

---------------------------------------------------------
NEWS
---------------------------------------------------------

News Title:
{news_title}

News Source:
{news_source}

Research Summary:
{research_summary}

Research Facts:
{json.dumps(
    facts,
    ensure_ascii=False,
    indent=2
)}

Research Sources:
{json.dumps(
    sources,
    ensure_ascii=False,
    indent=2
)}

---------------------------------------------------------
USER / AI CONTEXT
---------------------------------------------------------

Niche:
{niche}

Language:
{language}

Tone:
{tone}

Style:
{style}

Platform:
{platform}

Platform-Specific Requirements:
{platform_rules}

Planner Structure:
{json.dumps(
    structure_context,
    ensure_ascii=False,
    indent=2
)}

---------------------------------------------------------
STRICT RULES
---------------------------------------------------------

1. NEVER invent news facts.

2. Only use facts supported by the supplied research.

3. Do not invent:
   - numbers
   - dates
   - companies
   - people
   - product names
   - technical specifications
   - statistics
   - quotes
   - announcements
   - links

4. Maintain consistency with the planner.

5. If the planner contains N sections, do not describe
   the content as a different number of steps/items.

6. post_idea must match the actual caption and planner.

7. If there is no meaningful CTA in the planner,
   do not invent one.

8. Keep the news summary factual and concise.

9. Generate relevant hashtags appropriate for the
   selected platform.

10. Match language, tone and style.

11. Do not use markdown.

12. Adapt the communication style to the selected
    platform without changing the factual meaning
    or planner structure.

13. Return ONLY valid JSON.

---------------------------------------------------------
HASHTAG REQUIREMENT
---------------------------------------------------------

Instagram:
5 hashtags

LinkedIn:
3 hashtags

Facebook:
5 hashtags

X:
2 hashtags

General:
5 hashtags

---------------------------------------------------------
OUTPUT
---------------------------------------------------------

{{
    "caption": "news-based social media caption",
    "hashtags": [
        "#hashtag1",
        "#hashtag2",
        "#hashtag3"
    ],
    "post_idea": "accurate visual/post idea",
    "news_summary": "short factual summary supported by research"
}}
"""

    # -----------------------------------------------------
    # Groq News Content Generation
    # -----------------------------------------------------

    response = create_groq_completion(

        messages=[

            {
                "role": "system",
                "content": (
                    "You are a responsible news-content agent. "
                    "Never invent facts and never create unsupported "
                    "claims. Adapt the writing style to the requested "
                    "platform without changing the supplied facts "
                    "or planner structure."
                )
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.35,
    )

    raw_content = response.choices[0].message.content

    result = clean_json_response(
        raw_content
    )

    # -----------------------------------------------------
    # Platform-specific hashtag normalization
    # -----------------------------------------------------

    hashtags = normalize_hashtags(
        result.get("hashtags", []),
        platform=platform
    )

    hashtag_limit = {
        "instagram": 5,
        "linkedin": 3,
        "facebook": 5,
        "x": 2,
        "general": 5,
    }.get(
        platform,
        5
    )

    # -----------------------------------------------------
    # Hashtag fallback
    # -----------------------------------------------------

    if len(hashtags) < hashtag_limit:

        generated = get_hashtag_fallbacks(
            topic=news_title,
            platform=platform
        )

        for tag in generated:

            if tag not in hashtags:
                hashtags.append(tag)

            if len(hashtags) == hashtag_limit:
                break

    # -----------------------------------------------------
    # FINAL NEWS CONTENT RESULT
    # -----------------------------------------------------

    return {

        "caption": safe_text(
            result.get(
                "caption",
                ""
            )
        ),

        "hashtags": hashtags[:hashtag_limit],

        "post_idea": safe_text(
            result.get(
                "post_idea",
                ""
            )
        ),

        "news_summary": safe_text(
            result.get(
                "news_summary",
                ""
            )
        ),

        "style": style,

        "language": language,

        "tone": tone,

        "niche": niche,

        "topic": news_title,

        # IMPORTANT:
        # Always return the actual selected platform.
        "platform": platform,

        "content_structure": {

            "post_type": post_type,

            "format": post_format,

            "section_count": len(sections)
        }
    }