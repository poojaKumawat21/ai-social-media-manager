import json
import re

from app.services.content_generator import client


# ---------------------------------------------------------
# JSON CLEANER
# ---------------------------------------------------------

def clean_json_response(text: str):
    """
    Cleans AI response and converts it into a Python dictionary.
    Handles markdown code blocks and minor formatting issues.
    """

    if not text:
        return {}

    text = text.strip()

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {}

    return {}


# ---------------------------------------------------------
# NORMALIZERS
# ---------------------------------------------------------

def normalize_hashtags(value):
    """
    Always return exactly 5 hashtags.
    """

    if not isinstance(value, list):
        value = []

    hashtags = []

    for tag in value:
        if not isinstance(tag, str):
            continue

        tag = tag.strip()

        if not tag:
            continue

        if not tag.startswith("#"):
            tag = "#" + tag

        hashtags.append(tag)

    unique = []

    for tag in hashtags:
        if tag.lower() not in [x.lower() for x in unique]:
            unique.append(tag)

    while len(unique) < 5:
        fallback = "#SocialMedia"

        if fallback.lower() not in [x.lower() for x in unique]:
            unique.append(fallback)
        else:
            unique.append(f"#Content{len(unique) + 1}")

    return unique[:5]


def normalize_sections(value):
    """
    Converts AI section output into a consistent structure.
    """

    if not isinstance(value, list):
        return []

    sections = []

    for index, item in enumerate(value, start=1):

        if isinstance(item, str):
            title = item.strip()
            description = ""

        elif isinstance(item, dict):
            title = str(
                item.get("title", "")
            ).strip()

            description = str(
                item.get("description", "")
            ).strip()

        else:
            continue

        if not title:
            continue

        sections.append(
            {
                "number": index,
                "title": title,
                "description": description
            }
        )

    return sections


# ---------------------------------------------------------
# FORMAT NORMALIZER
# ---------------------------------------------------------

def normalize_format(value):
    """
    Normalizes different AI responses into:
    - single_post
    - carousel
    """

    raw_format = str(
        value or "single_post"
    ).strip().lower()

    carousel_keywords = [
        "carousel",
        "multi-slide",
        "multi slide",
        "multiple slide",
        "multiple slides",
        "slide deck"
    ]

    if any(
        keyword in raw_format
        for keyword in carousel_keywords
    ):
        return "carousel"

    return "single_post"


# ---------------------------------------------------------
# MAIN CONTENT PLANNER
# ---------------------------------------------------------

def plan_social_media_post(
    topic: str,
    description: str = ""
):
    """
    Intelligent agentic social media content planner.

    USER PROVIDES ONLY:
    - topic
    - optional description/instructions

    AI DECIDES:
    - niche / field
    - audience
    - tone
    - style
    - post type
    - format
    - carousel vs single post
    - number of useful sections
    - headline
    - subheadline
    - introduction
    - content
    - CTA
    - hashtags
    - research requirement
    - source requirement
    - visual direction
    - design layout
    """

    topic = str(topic or "").strip()
    description = str(description or "").strip()

    if not topic:
        raise ValueError(
            "Topic is required."
        )

    # -----------------------------------------------------
    # AI PLANNING PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are the CONTENT PLANNING AGENT of an intelligent,
autonomous AI Social Media Manager.

Your job is to understand the user's intent and independently
decide the best social-media strategy for the topic.

The user should NOT have to decide technical content/design
parameters.

USER INPUT
----------

Topic:
{topic}

Optional description/instructions:
{description if description else "None provided."}


===========================================================
CORE AGENTIC RULE
===========================================================

The user gives an intent.

YOU make the decisions.

Do NOT expect the user to provide:

- niche
- industry
- audience
- tone
- style
- content type
- format
- number of slides
- design style
- layout
- colors
- visual type

Infer these intelligently from the topic and optional
description.

If the user explicitly gives an instruction, respect it.

Example:

"Make it funny"
→ choose an appropriate humorous tone.

"Professional LinkedIn post"
→ infer professional/business tone and suitable style.

"Explain this to beginners"
→ infer beginner audience and educational approach.

If the user gives no such instruction,
choose the best option yourself.


===========================================================
NO FIXED TEMPLATE
===========================================================

Do NOT force every topic into the same structure.

Do NOT automatically create a carousel.

Do NOT automatically create 8 slides.

Choose between:

- single post
- carousel

based on what communicates the topic best.

For a carousel, choose the amount of content needed.
There is NO fixed slide count.

The renderer may later create the required number of slides
based on the planned sections.


===========================================================
UNDERSTAND THE USER'S INTENT
===========================================================

Before planning the post, internally determine:

1. What is the topic?
2. What is the likely intent?
3. Who would benefit from this content?
4. Does this topic need explanation?
5. Is it emotional, educational, promotional,
   entertaining, informational, celebratory, etc.?
6. Would a single visual communicate it better?
7. Would multiple slides genuinely improve it?
8. Does it require current/recent information?
9. What visual concept naturally matches the topic?


===========================================================
EXAMPLES
===========================================================

These are examples of reasoning only.

DO NOT hardcode these categories.

Example:

Topic: "Ganesh Chaturthi"

Likely result:
- celebration/greeting
- single visual post
- festive cultural imagery
- concise emotional message

Do NOT force an educational carousel.


Topic: "Happy Birthday"

Likely result:
- celebration
- single visual
- birthday-themed visual
- warm/elegant message

Do NOT create unnecessary informational sections.


Topic: "Digital Marketing"

Likely result:
- educational/informative
- useful beginner-friendly information
- single post OR carousel depending on the actual content


Topic: "7 Digital Marketing Strategies"

Likely result:
- educational
- carousel
- multiple useful sections

Each strategy must contain actual useful information.


Topic: "AI Agents"

Likely result:
- educational/explanatory
- explain the concept clearly
- provide useful examples
- choose single post or carousel intelligently.


Topic involving current news:

- research required
- current facts must NOT be invented
- research agent should verify information
- source attribution may be required.


===========================================================
CONTENT QUALITY
===========================================================

Every post must feel like real social-media content.

Prioritize:

- strong hook
- useful information
- concise writing
- natural language
- relevance
- readability
- engagement
- originality
- non-repetitive content

Do not write every post like a formal article.

Do not add filler simply to increase content length.


===========================================================
INFORMATIONAL CONTENT
===========================================================

If the chosen content strategy requires explanations,
every section must contain actual useful information.

BAD:

Title:
"Use First-Party Data"

Description:
""


GOOD:

Title:
"Use First-Party Data"

Description:
"Collect consent-based data directly from your website,
app or customers. This can help personalize campaigns
while reducing dependence on third-party tracking."

Do NOT create empty informational sections.


===========================================================
SIMPLE VISUAL CONTENT
===========================================================

If the topic is best communicated visually:

sections may be [].

The headline, message, CTA and visual should carry
the post.

Do not force educational sections.


===========================================================
CURRENT INFORMATION / RESEARCH
===========================================================

Set:

requires_research = true

when the topic or user instruction requires:

- current news
- today's events
- latest developments
- recent statistics
- current technology releases
- current companies/products
- political/current affairs
- time-sensitive information

Otherwise:

requires_research = false


===========================================================
SOURCE REQUIREMENT
===========================================================

Set:

source_required = true

when the post contains factual claims that should be
attributed to a source, especially current or researched
information.

Never invent a source.

Never fabricate statistics.


===========================================================
VISUAL INTELLIGENCE
===========================================================

Create a specific visual direction based on the actual topic.

Do NOT repeatedly use generic:

- laptop
- business people
- blue gradients
- office scenes
- generic technology backgrounds
- stock imagery

The visual concept must naturally match the topic.

For example, a food topic should visually feel like food.

A travel topic should visually feel like the relevant
destination/travel experience.

A festival should use culturally relevant elements.

A technology topic can use relevant technological concepts.

A birthday should look like a birthday.

Do NOT copy these examples mechanically.


===========================================================
DESIGN INTELLIGENCE
===========================================================

Choose a layout appropriate for the actual content.

Possible approaches include:

- centered
- editorial
- split
- asymmetric
- image-led
- text-led
- full-bleed
- large typography
- cards
- magazine
- cinematic
- poster
- infographic
- photo + text
- minimal
- diagonal

Do NOT always choose the same layout.

Do NOT always choose the same style.

The Design Agent will later turn this plan into the
actual visual design.


===========================================================
ORIGINALITY
===========================================================

Avoid generic repeated wording.

The same topic may be posted multiple times in the future,
so create a useful and natural angle for this particular post.

Do not assume today's post is identical to yesterday's post.


===========================================================
OUTPUT
===========================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "inferred_niche": "",
    "audience": "",
    "tone": "",
    "selected_style": "",

    "post_type": "",
    "format": "",

    "headline": "",
    "subheadline": "",
    "introduction": "",

    "sections": [],

    "key_takeaway": "",
    "cta": "",
    "hashtags": [],

    "requires_research": false,
    "source_required": false,
    "research_queries": [],

    "visual_direction": "",
    "design_layout": "",

    "reasoning": ""
}}


===========================================================
SECTION FORMAT
===========================================================

Each section must be:

{{
    "number": 1,
    "title": "",
    "description": ""
}}

For informational content:

description MUST contain useful information.

For simple visual posts:

sections can be [].


===========================================================
HASHTAGS
===========================================================

Return exactly 5 relevant hashtags.

They must match the actual topic.


===========================================================
FINAL PRINCIPLE
===========================================================

Think like a professional autonomous social-media strategist.

The user gives the topic.

YOU decide what the best social-media post should be.

Never force the topic into a predetermined template.
"""


    # -----------------------------------------------------
    # GROQ CALL
    # -----------------------------------------------------

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert autonomous social media "
                    "content planner. Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=3000
    )

    raw_text = response.choices[0].message.content

    planner_data = clean_json_response(raw_text)

    if not planner_data:
        raise ValueError(
            "Content Planner returned invalid JSON."
        )


    # -----------------------------------------------------
    # NORMALIZE BASIC FIELDS
    # -----------------------------------------------------

    planner_data["inferred_niche"] = str(
        planner_data.get("inferred_niche", "")
    ).strip()

    planner_data["audience"] = str(
        planner_data.get("audience", "")
    ).strip()

    planner_data["tone"] = str(
        planner_data.get("tone", "")
    ).strip()

    planner_data["selected_style"] = str(
        planner_data.get("selected_style", "")
    ).strip()

    planner_data["post_type"] = str(
        planner_data.get(
            "post_type",
            "social media post"
        )
    ).strip()

    planner_data["format"] = normalize_format(
        planner_data.get("format")
    )

    planner_data["headline"] = str(
        planner_data.get("headline", "")
    ).strip()

    planner_data["subheadline"] = str(
        planner_data.get("subheadline", "")
    ).strip()

    planner_data["introduction"] = str(
        planner_data.get("introduction", "")
    ).strip()

    planner_data["key_takeaway"] = str(
        planner_data.get("key_takeaway", "")
    ).strip()

    planner_data["cta"] = str(
        planner_data.get("cta", "")
    ).strip()

    planner_data["visual_direction"] = str(
        planner_data.get("visual_direction", "")
    ).strip()

    planner_data["design_layout"] = str(
        planner_data.get("design_layout", "")
    ).strip()

    planner_data["reasoning"] = str(
        planner_data.get("reasoning", "")
    ).strip()


    # -----------------------------------------------------
    # NORMALIZE SECTIONS
    # -----------------------------------------------------

    sections = normalize_sections(
        planner_data.get("sections", [])
    )

    planner_data["sections"] = sections


    # -----------------------------------------------------
    # INFORMATIONAL CONTENT VALIDATION
    # -----------------------------------------------------

    valid_sections = []

    for section in planner_data["sections"]:

        title = section["title"].strip()
        description_text = section["description"].strip()

        if not title:
            continue

        # If AI created a section, informational content
        # should have meaningful text.
        if description_text and len(description_text) >= 20:

            valid_sections.append(
                {
                    "number": len(valid_sections) + 1,
                    "title": title,
                    "description": description_text
                }
            )

    planner_data["sections"] = valid_sections


    # -----------------------------------------------------
    # FORMAT-BASED SECTION LIMIT
    # -----------------------------------------------------

    if planner_data["format"] == "single_post":

        # A single post should remain concise.
        planner_data["sections"] = (
            planner_data["sections"][:4]
        )

    elif planner_data["format"] == "carousel":

        # Flexible carousel.
        # No fixed 8-slide rule.
        planner_data["sections"] = (
            planner_data["sections"][:7]
        )


    # -----------------------------------------------------
    # NORMALIZE RESEARCH
    # -----------------------------------------------------

    planner_data["requires_research"] = bool(
        planner_data.get(
            "requires_research",
            False
        )
    )

    planner_data["source_required"] = bool(
        planner_data.get(
            "source_required",
            False
        )
    )

    research_queries = planner_data.get(
        "research_queries",
        []
    )

    if not isinstance(
        research_queries,
        list
    ):
        research_queries = []

    planner_data["research_queries"] = [
        str(query).strip()
        for query in research_queries
        if str(query).strip()
    ]


    # -----------------------------------------------------
    # NORMALIZE HASHTAGS
    # -----------------------------------------------------

    planner_data["hashtags"] = normalize_hashtags(
        planner_data.get("hashtags", [])
    )


    # -----------------------------------------------------
    # SAFETY DEFAULTS
    # -----------------------------------------------------

    if not planner_data["headline"]:
        planner_data["headline"] = topic

    if not planner_data["inferred_niche"]:
        planner_data["inferred_niche"] = "General"

    if not planner_data["audience"]:
        planner_data["audience"] = (
            "Social media audience interested in the topic."
        )

    if not planner_data["tone"]:
        planner_data["tone"] = "Natural and engaging"

    if not planner_data["selected_style"]:
        planner_data["selected_style"] = "Modern"

    if not planner_data["visual_direction"]:
        planner_data["visual_direction"] = (
            f"Create a topic-specific visual centered around "
            f"{topic}. Avoid generic stock imagery."
        )

    if not planner_data["design_layout"]:
        planner_data["design_layout"] = (
            "Choose a visually appropriate layout based "
            "on the topic and content."
        )


    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return planner_data