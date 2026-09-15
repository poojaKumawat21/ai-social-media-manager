import json
import re

from app.services.content_generator import client


# =========================================================
# JSON CLEANER
# =========================================================

def clean_design_json(raw_text: str):
    if not raw_text:
        raise ValueError("Design Agent returned empty response.")

    raw_text = raw_text.strip()

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

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")

    if start != -1 and end != -1:
        json_text = raw_text[start:end + 1]

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass

    raise ValueError("Design Agent returned invalid JSON.")


# =========================================================
# FORMAT NORMALIZER
# =========================================================

def normalize_format(value):
    if not value:
        return "single_post"

    value = str(value).strip().lower()

    if any(
        keyword in value
        for keyword in [
            "carousel",
            "multi-slide",
            "multi slide",
            "multiple slide"
        ]
    ):
        return "carousel"

    return "single_post"


# =========================================================
# TEXT HELPERS
# =========================================================

def _normalize_text(value):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower()
    )


def _section_title(section):
    if not isinstance(section, dict):
        return ""

    return (
        section.get("title")
        or section.get("heading")
        or section.get("name")
        or ""
    ).strip()


def _section_description(section):
    if not isinstance(section, dict):
        return ""

    return (
        section.get("description")
        or section.get("content")
        or section.get("body")
        or ""
    ).strip()


def _slide_search_text(slide):
    if not isinstance(slide, dict):
        return ""

    values = [
        slide.get("purpose", ""),
        slide.get("title", ""),
        slide.get("subtitle", ""),
        slide.get("body", ""),
        slide.get("visual_description", ""),
        slide.get("icon", "")
    ]

    return _normalize_text(" ".join(str(v) for v in values if v))


# =========================================================
# SECTION COVERAGE CHECK
# =========================================================

def _find_missing_sections(sections, slides):
    """
    Check whether every planner section is represented
    somewhere in the Design Agent output.

    We intentionally check both title and description
    because the Design Agent may slightly rewrite a title
    while preserving the actual content.
    """

    if not sections:
        return []

    slide_texts = [
        _slide_search_text(slide)
        for slide in slides
    ]

    missing = []

    for section in sections:

        title = _normalize_text(
            _section_title(section)
        )

        description = _normalize_text(
            _section_description(section)
        )

        if not title and not description:
            continue

        found = False

        for slide_text in slide_texts:

            # Exact title match
            if title and title in slide_text:
                found = True
                break

            # Meaningful description match
            if description:

                words = [
                    word
                    for word in re.findall(
                        r"\b[a-zA-Z0-9]+\b",
                        description
                    )
                    if len(word) >= 4
                ]

                if words:

                    matched = sum(
                        1
                        for word in words
                        if word in slide_text
                    )

                    # Enough meaningful words survived
                    if matched >= max(
                        2,
                        min(4, len(words) // 2)
                    ):
                        found = True
                        break

        if not found:
            missing.append(section)

    return missing


# =========================================================
# REPAIR MISSING SECTIONS
# =========================================================

def _repair_missing_sections(
    result,
    missing_sections,
    planner_summary
):
    """
    Ask the AI to repair only missing planner sections.

    This does NOT regenerate the complete design.

    Existing slides/layout/style remain authoritative.
    """

    if not missing_sections:
        return result

    repair_prompt = f"""
You are repairing an existing social media design plan.

The Content Planner is authoritative.

Some planner sections are missing from the current
Design Agent output.

Your ONLY job is to create additional slides for the
missing sections.

Do NOT remove existing slides.

Do NOT rewrite existing slides.

Do NOT change the topic.

Do NOT change the planner meaning.

Do NOT invent facts.

Do NOT invent statistics.

Do NOT invent sources.

Do NOT add filler.

=========================================================
PLANNER
=========================================================

{json.dumps(
    planner_summary,
    ensure_ascii=False,
    indent=2
)}

=========================================================
CURRENT DESIGN
=========================================================

{json.dumps(
    result,
    ensure_ascii=False,
    indent=2
)}

=========================================================
MISSING SECTIONS
=========================================================

{json.dumps(
    missing_sections,
    ensure_ascii=False,
    indent=2
)}

=========================================================
REPAIR RULES
=========================================================

Create exactly one useful slide for each missing section.

Each repaired slide MUST clearly represent its
corresponding planner section.

The section title should appear directly or in a
very clear equivalent form.

Use the section description as the source of truth.

Keep the existing design language consistent.

Choose a suitable layout for the section.

Do not force the same layout if another layout
better communicates the content.

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON.

Return exactly:

{{
    "slides": [
        {{
            "purpose": "content",
            "title": "",
            "subtitle": "",
            "body": "",
            "visual_type": "",
            "visual_description": "",
            "icon": "",
            "layout": ""
        }}
    ]
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise design repair agent. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": repair_prompt
            }
        ],
        temperature=0.35,
        max_tokens=2500
    )

    raw_content = (
        response
        .choices[0]
        .message
        .content
    )

    repair = clean_design_json(raw_content)

    repaired_slides = repair.get("slides", [])

    if not isinstance(repaired_slides, list):
        return result

    for slide in repaired_slides:

        if not isinstance(slide, dict):
            continue

        slide.setdefault(
            "purpose",
            "content"
        )

        slide.setdefault(
            "title",
            ""
        )

        slide.setdefault(
            "subtitle",
            ""
        )

        slide.setdefault(
            "body",
            ""
        )

        slide.setdefault(
            "visual_type",
            "topic_specific"
        )

        slide.setdefault(
            "visual_description",
            ""
        )

        slide.setdefault(
            "icon",
            ""
        )

        slide.setdefault(
            "layout",
            "adaptive"
        )

        result["slides"].append(slide)

    return result


# =========================================================
# DESIGN AGENT
# =========================================================

def create_design_plan(planner_data: dict):

    if not isinstance(planner_data, dict):
        raise ValueError(
            "planner_data must be a dictionary"
        )

    # -----------------------------------------------------
    # Read planner output
    # -----------------------------------------------------

    post_type = planner_data.get(
        "post_type",
        ""
    )

    content_format = normalize_format(
        planner_data.get(
            "format",
            "single_post"
        )
    )

    selected_style = planner_data.get(
        "selected_style",
        "AI selected"
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
        "cta",
        ""
    )

    hashtags = planner_data.get(
        "hashtags",
        []
    )

    visual_direction = planner_data.get(
        "visual_direction",
        ""
    )

    design_layout = planner_data.get(
        "design_layout",
        ""
    )

    audience = planner_data.get(
        "audience",
        ""
    )

    source_required = planner_data.get(
        "source_required",
        False
    )

    requires_research = planner_data.get(
        "requires_research",
        False
    )

    reasoning = planner_data.get(
        "reasoning",
        ""
    )

    # -----------------------------------------------------
    # Clean planner context
    # -----------------------------------------------------

    planner_summary = {
        "post_type": post_type,
        "format": content_format,
        "selected_style": selected_style,
        "headline": headline,
        "subheadline": subheadline,
        "introduction": introduction,
        "sections": sections,
        "key_takeaway": key_takeaway,
        "cta": cta,
        "hashtags": hashtags,
        "visual_direction": visual_direction,
        "design_layout": design_layout,
        "audience": audience,
        "source_required": source_required,
        "requires_research": requires_research,
        "reasoning": reasoning
    }

    # =====================================================
    # DESIGN PROMPT
    # =====================================================

    prompt = f"""
You are the DESIGN AGENT of an intelligent,
agentic AI Social Media Manager.

Your job is to convert a Content Planner decision
into a professional visual design plan.

You are NOT a fixed template generator.

The user provides the intent.

The AI decides the best visual execution.

=========================================================
CONTENT PLANNER OUTPUT
=========================================================

{json.dumps(
    planner_summary,
    ensure_ascii=False,
    indent=2
)}

=========================================================
CORE PRINCIPLE
=========================================================

Design according to the actual meaning,
purpose and context.

Do NOT assume every post is educational.

Do NOT assume every post is a carousel.

Do NOT assume every post needs cards.

Do NOT assume every post needs gradients.

Do NOT assume every post needs icons.

Do NOT assume every post needs the same layout.

=========================================================
FORMAT
=========================================================

Respect the planner's format.

If format is single_post:

Create exactly ONE complete visual.

If format is carousel:

Choose the number of slides according to the
actual information structure.

There is NO fixed slide count.

Do NOT force 8 slides.

Do NOT create filler slides.

=========================================================
CRITICAL CONTENT INTEGRITY RULE
=========================================================

THIS RULE HAS HIGHEST PRIORITY.

Every section supplied by the Content Planner MUST
be represented in the final carousel.

A planner section must NEVER disappear.

For every item inside:

"sections"

create at least one corresponding content slide.

The section can be represented by:

- its exact title
- a clearly equivalent title
- its section description
- a concise faithful version of its content

But the actual meaning MUST remain.

Example:

If planner provides 7 sections:

1. SEO
2. Content Marketing
3. Social Media Advertising
4. Email Marketing
5. PPC
6. Influencer Marketing
7. Conversion Rate Optimization

then ALL SEVEN MUST appear.

Do NOT stop after section 6.

Do NOT merge sections merely to reduce slide count.

Do NOT remove the final section because a conclusion
slide seems useful.

A hook slide and conclusion slide are optional and
are ADDITIONAL to the planner sections.

Therefore:

7 planner sections

may become:

1 hook
+ 7 content slides
+ optional conclusion

OR

7 content slides

OR another sensible structure.

But NEVER:

1 hook
+ 6 sections
+ conclusion

because that loses planner information.

=========================================================
SECTION NUMBERING
=========================================================

When the planner sections contain numbered concepts,
preserve the numbering or an obvious equivalent.

If there are N planner sections, the final design must
cover all N sections.

=========================================================
CONTENT PRESERVATION
=========================================================

The planner is authoritative.

Preserve:

- headline
- section meaning
- section descriptions
- key takeaway
- CTA
- important facts

Do NOT invent:

- facts
- statistics
- claims
- products
- sources
- URLs
- offers

Do not change factual meaning.

=========================================================
CAROUSEL STRUCTURE
=========================================================

A carousel may contain:

- hook
- content sections
- takeaway
- CTA

But none of these should replace planner sections.

Use a hook only when useful.

Use a conclusion only when useful.

Do NOT create unnecessary slides.

=========================================================
VISUAL INTELLIGENCE
=========================================================

Choose visuals based on the actual topic.

Possible visual approaches:

- photography
- illustration
- 3D
- editorial
- infographic
- diagram
- conceptual art
- cinematic
- product-focused
- cultural artwork
- typography-led
- collage
- chart/data visual
- symbolic visual
- minimalist

Choose what fits.

Avoid generic repeated visuals such as:

- generic laptops
- generic office people
- blue technology backgrounds
- random business stock imagery

=========================================================
DESIGN VARIATION
=========================================================

The system will generate many posts.

Intelligently vary:

- composition
- alignment
- image placement
- typography
- background treatment
- visual scale
- whitespace
- card usage
- color direction
- layout direction

Possible layouts include:

- centered
- asymmetric
- editorial
- split
- full-bleed
- image-led
- text-led
- large typography
- diagonal
- magazine
- poster
- cinematic
- minimal
- layered
- collage
- grid

These are possibilities, NOT mandatory templates.

=========================================================
READABILITY
=========================================================

Important text must remain readable.

Use:

- strong hierarchy
- sufficient contrast
- sensible spacing
- clear grouping
- appropriate text density

Maximum two font families.

=========================================================
AI VISUAL
=========================================================

AI visuals provide imagery only.

Never depend on image generation for:

- headlines
- paragraphs
- statistics
- labels
- CTA
- source text

Important text will be rendered separately.

=========================================================
SOURCE
=========================================================

If source_required is true:

Reserve a readable source area.

Never invent a source.

=========================================================
BRANDING
=========================================================

Reserve a subtle branding area.

Branding must not overpower content.

=========================================================
CANVAS
=========================================================

1080 x 1350 pixels
Portrait orientation

=========================================================
OUTPUT JSON
=========================================================

Return ONLY valid JSON.

Use exactly:

{{
    "canvas": {{
        "width": 1080,
        "height": 1350,
        "orientation": "portrait"
    }},

    "format": "single_post",

    "theme": {{
        "name": "",
        "primary_color": "#000000",
        "secondary_color": "#000000",
        "accent_color": "#000000",
        "background_color": "#000000",
        "text_color": "#FFFFFF"
    }},

    "typography": {{
        "headline_size": "large",
        "subheadline_size": "medium",
        "section_title_size": "medium",
        "body_size": "small",
        "cta_size": "medium"
    }},

    "background": {{
        "type": "",
        "description": "",
        "ai_visual_required": true,
        "ai_visual_prompt": ""
    }},

    "global_layout": {{
        "style": "",
        "padding": "40px",
        "alignment": "",
        "card_style": "",
        "border_radius": "24px",
        "visual_hierarchy": ""
    }},

    "slides": [
        {{
            "slide_number": 1,
            "purpose": "",
            "title": "",
            "subtitle": "",
            "body": "",
            "visual_type": "",
            "visual_description": "",
            "icon": "",
            "layout": ""
        }}
    ],

    "cta": {{
        "text": "",
        "placement": ""
    }},

    "source_area": {{
        "required": false,
        "placement": "bottom",
        "text": ""
    }},

    "branding_area": {{
        "required": true,
        "placement": "bottom_right"
    }}
}}

=========================================================
FINAL REQUIREMENTS
=========================================================

1. Return JSON only.

2. Canvas MUST be 1080 x 1350.

3. Format MUST be single_post or carousel.

4. Single post MUST contain exactly 1 slide.

5. Carousel slide count must be decided intelligently.

6. NEVER force 8 slides.

7. NEVER create filler slides.

8. EVERY planner section MUST be represented.

9. NEVER silently drop a planner section.

10. Hook and conclusion are optional.

11. Hook/conclusion MUST NOT replace planner sections.

12. Preserve planner meaning.

13. Do not invent facts.

14. Do not invent sources.

15. Visual direction must fit the topic.

16. Design must be professional and social-media ready.

17. Let the CONTENT determine the DESIGN.
"""

    # =====================================================
    # GROQ REQUEST
    # =====================================================

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert social media "
                    "visual design planning agent. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.65,
        max_tokens=3500
    )

    # =====================================================
    # READ RESPONSE
    # =====================================================

    raw_content = (
        response
        .choices[0]
        .message
        .content
    )

    if not raw_content:
        raise ValueError(
            "Design Agent returned an empty response."
        )

    print(
        "\n========== DESIGN AGENT RAW RESPONSE =========="
    )
    print(raw_content)
    print("================================================\n")

    result = clean_design_json(raw_content)

    # =====================================================
    # REQUIRED FIELDS
    # =====================================================

    required_fields = [
        "canvas",
        "format",
        "theme",
        "typography",
        "background",
        "global_layout",
        "slides",
        "cta",
        "source_area",
        "branding_area"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"Design Agent missing field: {field}"
            )

    # =====================================================
    # FORMAT VALIDATION
    # =====================================================

    result["format"] = normalize_format(
        result.get(
            "format",
            content_format
        )
    )

    # Always respect planner format.
    #
    # The Design Agent is allowed to make creative
    # decisions INSIDE the planner's selected format,
    # but it must not unexpectedly change carousel
    # into single post or vice versa.

    result["format"] = content_format

    # =====================================================
    # CANVAS VALIDATION
    # =====================================================

    result["canvas"] = {
        "width": 1080,
        "height": 1350,
        "orientation": "portrait"
    }

    # =====================================================
    # SLIDES VALIDATION
    # =====================================================

    if not isinstance(
        result.get("slides"),
        list
    ):
        result["slides"] = []

    valid_slides = []

    for index, slide in enumerate(
        result["slides"],
        start=1
    ):

        if not isinstance(
            slide,
            dict
        ):
            continue

        slide["slide_number"] = index

        slide.setdefault(
            "purpose",
            "content"
        )

        slide.setdefault(
            "title",
            ""
        )

        slide.setdefault(
            "subtitle",
            ""
        )

        slide.setdefault(
            "body",
            ""
        )

        slide.setdefault(
            "visual_type",
            "topic_specific"
        )

        slide.setdefault(
            "visual_description",
            ""
        )

        slide.setdefault(
            "icon",
            ""
        )

        slide.setdefault(
            "layout",
            "adaptive"
        )

        valid_slides.append(
            slide
        )

    # =====================================================
    # SINGLE POST
    # =====================================================

    if result["format"] == "single_post":

        if valid_slides:

            valid_slides = [
                valid_slides[0]
            ]

        else:

            valid_slides = [
                {
                    "slide_number": 1,
                    "purpose": "complete_post",
                    "title": headline,
                    "subtitle": subheadline,
                    "body": introduction,
                    "visual_type": "topic_specific",
                    "visual_description": visual_direction,
                    "icon": "",
                    "layout": design_layout
                }
            ]

    # =====================================================
    # CAROUSEL
    # =====================================================

    else:

        if not valid_slides:
            raise ValueError(
                "Design Agent created an empty carousel."
            )

        # -------------------------------------------------
        # FIRST CONTENT VALIDATION
        # -------------------------------------------------

        missing_sections = _find_missing_sections(
            sections=sections,
            slides=valid_slides
        )

        if missing_sections:

            print(
                "\n⚠️ DESIGN AGENT SECTION COVERAGE ISSUE"
            )

            print(
                "Missing sections:"
            )

            for section in missing_sections:
                print(
                    f" - {_section_title(section)}"
                )

            print(
                "\n🔧 Running Design Repair Agent..."
            )

            temporary_result = {
                **result,
                "slides": valid_slides
            }

            temporary_result = _repair_missing_sections(
                result=temporary_result,
                missing_sections=missing_sections,
                planner_summary=planner_summary
            )

            valid_slides = temporary_result.get(
                "slides",
                valid_slides
            )

        # -------------------------------------------------
        # SECOND COVERAGE CHECK
        # -------------------------------------------------

        still_missing = _find_missing_sections(
            sections=sections,
            slides=valid_slides
        )

        if still_missing:

            missing_names = [
                _section_title(section)
                for section in still_missing
                if _section_title(section)
            ]

            raise ValueError(
                "Design Agent could not preserve all "
                f"planner sections. Missing: {missing_names}"
            )

        # -------------------------------------------------
        # Sensible upper protection
        # -------------------------------------------------

        # This is NOT a fixed slide count.
        #
        # It only prevents catastrophic model output
        # from creating hundreds of slides.

        max_allowed_slides = max(
            12,
            len(sections) + 3
        )

        valid_slides = valid_slides[
            :max_allowed_slides
        ]

    # =====================================================
    # FINAL SLIDE NUMBERS
    # =====================================================

    for index, slide in enumerate(
        valid_slides,
        start=1
    ):
        slide["slide_number"] = index

    result["slides"] = valid_slides

    # =====================================================
    # FINAL SECTION COVERAGE CHECK
    # =====================================================

    if result["format"] == "carousel":

        final_missing = _find_missing_sections(
            sections=sections,
            slides=result["slides"]
        )

        if final_missing:

            missing_names = [
                _section_title(section)
                for section in final_missing
                if _section_title(section)
            ]

            raise ValueError(
                "Final Design validation failed. "
                f"Missing planner sections: {missing_names}"
            )

    # =====================================================
    # CTA VALIDATION
    # =====================================================

    if not isinstance(
        result.get("cta"),
        dict
    ):
        result["cta"] = {
            "text": cta,
            "placement": "bottom"
        }

    result["cta"].setdefault(
        "text",
        cta
    )

    result["cta"].setdefault(
        "placement",
        "bottom"
    )

    # =====================================================
    # SOURCE VALIDATION
    # =====================================================

    if not isinstance(
        result.get("source_area"),
        dict
    ):
        result["source_area"] = {
            "required": bool(source_required),
            "placement": "bottom",
            "text": ""
        }

    result["source_area"].setdefault(
        "required",
        bool(source_required)
    )

    result["source_area"].setdefault(
        "placement",
        "bottom"
    )

    result["source_area"].setdefault(
        "text",
        ""
    )

    # =====================================================
    # BRANDING VALIDATION
    # =====================================================

    if not isinstance(
        result.get("branding_area"),
        dict
    ):
        result["branding_area"] = {
            "required": True,
            "placement": "bottom_right"
        }

    result["branding_area"].setdefault(
        "required",
        True
    )

    result["branding_area"].setdefault(
        "placement",
        "bottom_right"
    )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    return result