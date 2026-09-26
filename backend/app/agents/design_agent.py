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
# PLATFORM NORMALIZER
# =========================================================

def normalize_platform(value):
    if not value:
        return "general"

    value = str(value).strip().lower()

    allowed_platforms = {
        "instagram",
        "linkedin",
        "facebook",
        "x",
        "general",
    }

    if value not in allowed_platforms:
        return "general"

    return value


# =========================================================
# PLATFORM DESIGN RULES
# =========================================================

def get_platform_design_rules(platform="general"):
    """
    Platform-specific visual guidance.

    These rules do NOT replace the planner.
    They only tell the Design Agent how to adapt
    the visual execution for the selected platform.
    """

    platform = normalize_platform(platform)

    rules = {

        "instagram": """
- Optimize the visual for Instagram feed consumption.
- Use a strong visual hook.
- Prioritize mobile readability.
- Keep important text concise and visually clear.
- Prefer visually engaging compositions.
- Avoid dense paragraphs inside the visual.
- Carousel slides should be easy to scan and swipe.
- Strong visual identity is useful, but do not use
  generic Instagram templates repeatedly.
- The design should feel social, modern and visual-first.
- Do not make it look like a LinkedIn document.
""",

        "linkedin": """
- Optimize the visual for LinkedIn feed consumption.
- Use a clean, editorial and professional visual language.
- Prioritize information hierarchy and readability.
- Visuals should support professional insight or context.
- Avoid overly playful or Instagram-style compositions.
- Avoid excessive decorative elements.
- Keep typography and spacing professional.
- Carousel slides should feel structured and readable.
- The design should look appropriate in a professional feed.
""",

        "facebook": """
- Optimize the visual for Facebook feed consumption.
- Prioritize immediate readability on mobile.
- Use approachable and understandable visual composition.
- Visuals can be expressive and conversational when appropriate.
- Avoid excessive information density.
- Make the main message understandable quickly.
- Do not force a formal business-document aesthetic.
""",

        "x": """
- Optimize the visual for X feed consumption.
- Prioritize one strong visual idea.
- Keep visual text minimal and immediately readable.
- Avoid unnecessary visual complexity.
- Strong contrast and clear hierarchy are important.
- For carousels, keep slides focused and concise.
- Do not turn the visual into a dense infographic.
""",

        "general": """
- Create a professional social-media-ready visual.
- Prioritize clarity, readability and topic relevance.
- Let the actual content determine the design.
"""
    }

    return rules[platform]


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
        slide.get("visual_subject", ""),
        slide.get("visual_environment", ""),
        slide.get("composition", ""),
        slide.get("icon", "")
    ]

    return _normalize_text(
        " ".join(
            str(v)
            for v in values
            if v
        )
    )


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
    planner_summary,
    platform="general"
):
    """
    Ask the AI to repair only missing planner sections.

    This does NOT regenerate the complete design.

    Existing slides/layout/style remain authoritative.
    """

    if not missing_sections:
        return result

    platform = normalize_platform(platform)

    platform_rules = get_platform_design_rules(
        platform
    )

    repair_prompt = f"""
You are repairing an existing social media design plan.

The Content Planner is authoritative.

The selected platform is:

{platform.upper()}

=========================================================
PLATFORM VISUAL REQUIREMENTS
=========================================================

{platform_rules}

=========================================================
IMPORTANT
=========================================================

Platform-specific visual requirements must NOT change
the planner's meaning or remove planner sections.

The planner remains the source of truth.

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

The visual should remain topic-specific.

Reserve a sensible text-safe area.

Do not generate actual post text inside the AI visual.

The selected platform should influence visual execution,
but must never remove planner content.

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
            "visual_subject": "",
            "visual_environment": "",
            "composition": "",
            "image_position": "",
            "text_position": "",
            "text_safe_area": "",
            "text_alignment": "",
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
            "visual_subject",
            ""
        )

        slide.setdefault(
            "visual_environment",
            ""
        )

        slide.setdefault(
            "composition",
            ""
        )

        slide.setdefault(
            "image_position",
            ""
        )

        slide.setdefault(
            "text_position",
            ""
        )

        slide.setdefault(
            "text_safe_area",
            ""
        )

        slide.setdefault(
            "text_alignment",
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

def create_design_plan(
    planner_data: dict,
    platform: str = "general"
):

    if not isinstance(planner_data, dict):
        raise ValueError(
            "planner_data must be a dictionary"
        )
    platform = normalize_platform(
        platform or planner_data.get("platform")
    )

    platform_rules = get_platform_design_rules(
        platform
    )

    # -----------------------------------------------------
    # Platform
    # -----------------------------------------------------

    # Explicit function argument has priority.
    # If an existing caller only passes planner_data,
    # platform can still be recovered from planner_data.
    if not platform or platform == "general":

        platform = planner_data.get(
            "platform",
            "general"
        )

    platform = normalize_platform(
    platform or planner_data.get("platform")
    )

    platform_rules = get_platform_design_rules(
        platform
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
        "reasoning": reasoning,

        # Platform context
        "platform": platform,
        "platform_instructions": platform_rules,

        # Visual intelligence context
        "topic": planner_data.get(
            "topic",
            ""
        ),
        "description": planner_data.get(
            "description",
            ""
        ),
        "niche": planner_data.get(
            "inferred_niche",
            ""
        )
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
SELECTED PLATFORM
=========================================================

{platform.upper()}

=========================================================
PLATFORM-SPECIFIC VISUAL REQUIREMENTS
=========================================================

{platform_rules}

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

The selected platform should influence the visual
execution, but the planner remains authoritative.

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
ADVANCED VISUAL INTELLIGENCE
=========================================================

The final design must look like a professionally
art-directed social media post, NOT like a repeated
AI template.

The visual must be genuinely connected to the topic.

FIRST understand:

- topic
- niche
- audience
- message
- tone
- post purpose
- amount of text
- emotional/contextual meaning

THEN decide the visual execution.

Do NOT use the same visual structure for every post.

Do NOT simply change the background while keeping
the same composition.

The composition itself should intelligently vary.

=========================================================
VISUAL CONCEPT
=========================================================

Create a specific visual concept related to the topic.

The visual concept may include:

- real-world environment
- people
- objects
- technology
- architecture
- cultural elements
- product/contextual objects
- abstract concepts
- editorial photography
- illustration
- conceptual scene
- cinematic scene
- infographic elements

The visual should communicate the topic even before
the viewer reads all the text.

Avoid meaningless decorative AI imagery.

=========================================================
COMPOSITION INTELLIGENCE
=========================================================

AI MUST decide the best composition for THIS post.

Possible compositions include:

- full-bleed visual
- centered subject
- subject on left with negative space on right
- subject on right with negative space on left
- top visual / bottom text
- bottom visual / top text
- asymmetric editorial composition
- diagonal composition
- large typography with supporting visual
- image-led composition
- text-led composition
- magazine/editorial composition
- cinematic composition
- collage composition
- layered composition
- minimal composition
- immersive background composition
- object-focused composition
- human-centered composition

These are examples only.

Do NOT rotate through these layouts mechanically.

Do NOT select a layout merely because it was used
in a previous post.

Choose the composition based on the actual topic,
message and visual concept.

=========================================================
VISUAL DIVERSITY
=========================================================

The system will generate many posts over time.

Avoid repeating:

- same composition
- same subject position
- same background style
- same color treatment
- same card structure
- same typography arrangement
- same image-to-text ratio
- same visual hierarchy

Two posts about different topics should NOT
automatically look like the same template.

However, visual consistency of the user's brand may
still be maintained through subtle typography,
spacing and branding.

Professional consistency does NOT mean identical layouts.

=========================================================
REALISTIC / GENUINE VISUAL STYLE
=========================================================

When appropriate, prefer visuals that look like:

- professional editorial photography
- realistic lifestyle photography
- documentary-style photography
- premium commercial photography
- natural environmental photography
- realistic product/context photography
- sophisticated editorial illustration

Avoid making every image look like obvious AI art.

Avoid unnecessary:

- neon glow
- floating holograms
- random futuristic interfaces
- excessive blue gradients
- generic glowing brains
- generic robots
- random laptops
- meaningless circuit patterns
- artificial-looking people

Use such elements ONLY when they actually fit the topic.

=========================================================
TOPIC-SPECIFIC BACKGROUND
=========================================================

The background must support the topic.

For example:

Technology topic:
Use a believable technology/work environment,
digital infrastructure, device, laboratory or relevant
technical environment.

Education topic:
Use a realistic classroom, learning environment,
teacher/student context, books, campus or relevant
educational environment.

Marketing topic:
Use a realistic marketing/work environment,
campaign visualization, analytics context,
advertising or communication environment.

Festival/cultural topic:
Use culturally relevant environment,
decorations, architecture, objects and atmosphere.

Health topic:
Use appropriate healthcare environment,
professional setting or relevant human context.

Business topic:
Use a realistic professional/business environment,
meeting, workplace, product or relevant context.

These are examples, NOT hardcoded mappings.

The AI must infer the appropriate environment from
the actual topic.

=========================================================
TEXT-SAFE COMPOSITION
=========================================================

The AI-generated visual should leave intentional
negative space for separately rendered text.

Never place the main visual subject directly over
the intended headline area.

Choose a text-safe area such as:

- top
- bottom
- left
- right
- center
- overlay with controlled contrast

The text-safe area must depend on the composition.

The renderer will add the actual text later.

=========================================================
VISUAL PROMPT QUALITY
=========================================================

The ai_visual_prompt must describe:

- exact subject/context
- environment
- visual style
- lighting
- composition
- camera/perspective when relevant
- important visual elements
- background
- negative space for text
- realistic/professional appearance

Do NOT ask the image generator to render the
actual headline, body text, CTA, hashtags or source.

The image generator creates visual content only.

Actual text is rendered separately.

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
        "ai_visual_prompt": "",
        "environment": "",
        "subject": "",
        "visual_style": "",
        "lighting": "",
        "composition": "",
        "text_safe_area": ""
    }},

    "global_layout": {{
        "style": "",
        "padding": "40px",
        "alignment": "",
        "card_style": "",
        "border_radius": "24px",
        "visual_hierarchy": "",
        "composition_type": "",
        "image_position": "",
        "text_position": "",
        "text_safe_area": "",
        "visual_balance": ""
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
            "visual_subject": "",
            "visual_environment": "",
            "composition": "",
            "image_position": "",
            "text_position": "",
            "text_safe_area": "",
            "text_alignment": "",
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

18. Do not use a repetitive visual template.

19. The visual composition must be selected specifically
    for the current topic and message.

20. The background must be contextually relevant.

21. The image generator must not generate the actual
    post text.

22. Reserve intentional negative space for text.

23. The composition must look professionally art-directed.

24. Avoid obvious generic AI aesthetics when realistic
    visual treatment is more appropriate.

25. Do not make every post look like:
    image on one side + text on the other.

26. Do not make every post use cards.

27. Do not make every post use the same typography structure.

28. Variation must come from intelligent design decisions,
    not random changes.

29. Preserve readability and content hierarchy.

30. Platform-specific visual adaptation must NEVER
    remove or change planner sections.

31. The planner's selected format MUST be preserved.

32. The platform should influence visual execution,
    not content meaning.
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
    # BACKGROUND VALIDATION
    # =====================================================

    if not isinstance(
        result.get("background"),
        dict
    ):
        result["background"] = {}

    result["background"].setdefault(
        "type",
        "topic_specific"
    )

    result["background"].setdefault(
        "description",
        visual_direction
    )

    result["background"].setdefault(
        "ai_visual_required",
        True
    )

    result["background"].setdefault(
        "ai_visual_prompt",
        visual_direction
    )

    result["background"].setdefault(
        "environment",
        ""
    )

    result["background"].setdefault(
        "subject",
        ""
    )

    result["background"].setdefault(
        "visual_style",
        selected_style
    )

    result["background"].setdefault(
        "lighting",
        ""
    )

    result["background"].setdefault(
        "composition",
        ""
    )

    result["background"].setdefault(
        "text_safe_area",
        ""
    )

    # =====================================================
    # GLOBAL LAYOUT VALIDATION
    # =====================================================

    if not isinstance(
        result.get("global_layout"),
        dict
    ):
        result["global_layout"] = {}

    result["global_layout"].setdefault(
        "style",
        design_layout or "adaptive"
    )

    result["global_layout"].setdefault(
        "padding",
        "40px"
    )

    result["global_layout"].setdefault(
        "alignment",
        ""
    )

    result["global_layout"].setdefault(
        "card_style",
        ""
    )

    result["global_layout"].setdefault(
        "border_radius",
        "24px"
    )

    result["global_layout"].setdefault(
        "visual_hierarchy",
        ""
    )

    result["global_layout"].setdefault(
        "composition_type",
        ""
    )

    result["global_layout"].setdefault(
        "image_position",
        ""
    )

    result["global_layout"].setdefault(
        "text_position",
        ""
    )

    result["global_layout"].setdefault(
        "text_safe_area",
        ""
    )

    result["global_layout"].setdefault(
        "visual_balance",
        ""
    )

    # =====================================================
    # TYPOGRAPHY VALIDATION
    # =====================================================

    if not isinstance(
        result.get("typography"),
        dict
    ):
        result["typography"] = {}

    result["typography"].setdefault(
        "headline_size",
        "large"
    )

    result["typography"].setdefault(
        "subheadline_size",
        "medium"
    )

    result["typography"].setdefault(
        "section_title_size",
        "medium"
    )

    result["typography"].setdefault(
        "body_size",
        "small"
    )

    result["typography"].setdefault(
        "cta_size",
        "medium"
    )

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
            "visual_subject",
            ""
        )

        slide.setdefault(
            "visual_environment",
            ""
        )

        slide.setdefault(
            "composition",
            ""
        )

        slide.setdefault(
            "image_position",
            ""
        )

        slide.setdefault(
            "text_position",
            ""
        )

        slide.setdefault(
            "text_safe_area",
            ""
        )

        slide.setdefault(
            "text_alignment",
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
                    "visual_subject": "",
                    "visual_environment": "",
                    "composition": design_layout,
                    "image_position": "",
                    "text_position": "",
                    "text_safe_area": "",
                    "text_alignment": "",
                    "icon": "",
                    "layout": design_layout or "adaptive"
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
                planner_summary=planner_summary,
                platform=platform
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
    # FINAL PLATFORM METADATA
    # =====================================================

    result["platform"] = platform

    # Keep platform information available to the
    # downstream renderer/image-generation layer.
    result["platform_instructions"] = platform_rules

    # =====================================================
    # FINAL RESULT
    # =====================================================

    return result