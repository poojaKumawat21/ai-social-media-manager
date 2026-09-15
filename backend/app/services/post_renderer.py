import os
import re
import uuid

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from app.services.image_generator import generate_ai_visual


# =========================================================
# CONFIG
# =========================================================

WIDTH = 1080
HEIGHT = 1350

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "generated_images"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# =========================================================
# FONT
# =========================================================

def get_font(size, bold=False):

    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf"
        if bold
        else "C:/Windows/Fonts/arial.ttf",

        "C:/Windows/Fonts/calibrib.ttf"
        if bold
        else "C:/Windows/Fonts/calibri.ttf",

        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for path in font_paths:

        if os.path.exists(path):

            return ImageFont.truetype(
                path,
                size
            )

    return ImageFont.load_default()


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text)

    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u200b": "",
        "\u2022": "•",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.replace("□", "-")

    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
        "",
        text
    )

    return text.strip()


# =========================================================
# COLOR
# =========================================================

def hex_to_rgb(hex_color):

    if not hex_color:
        return (255, 255, 255)

    hex_color = str(hex_color).strip()

    if not hex_color.startswith("#"):
        hex_color = "#" + hex_color

    if len(hex_color) != 7:
        return (255, 255, 255)

    try:

        return tuple(
            int(hex_color[i:i + 2], 16)
            for i in (1, 3, 5)
        )

    except ValueError:

        return (255, 255, 255)


# =========================================================
# GRADIENT
# =========================================================

def draw_gradient(
    draw,
    color1,
    color2
):

    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    for y in range(HEIGHT):

        ratio = y / max(HEIGHT - 1, 1)

        color = tuple(
            int(
                rgb1[i] * (1 - ratio)
                + rgb2[i] * ratio
            )
            for i in range(3)
        )

        draw.line(
            [(0, y), (WIDTH, y)],
            fill=color
        )


# =========================================================
# TEXT WRAPPING
# =========================================================

def wrap_text(
    draw,
    text,
    font,
    max_width
):

    text = clean_text(text)

    if not text:
        return []

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            current_line + " " + word
        ).strip()

        bbox = draw.textbbox(
            (0, 0),
            test_line,
            font=font
        )

        line_width = (
            bbox[2] - bbox[0]
        )

        if line_width <= max_width:

            current_line = test_line

        else:

            if current_line:
                lines.append(
                    current_line
                )

            current_line = word

    if current_line:
        lines.append(
            current_line
        )

    return lines


# =========================================================
# DRAW WRAPPED TEXT
# =========================================================

def draw_wrapped_text(
    draw,
    text,
    xy,
    font,
    fill,
    max_width,
    line_spacing=10
):

    text = clean_text(text)

    if not text:
        return xy[1]

    x, y = xy

    lines = wrap_text(
        draw,
        text,
        font,
        max_width
    )

    for line in lines:

        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill
        )

        bbox = draw.textbbox(
            (x, y),
            line,
            font=font
        )

        line_height = (
            bbox[3] - bbox[1]
        )

        y += (
            line_height
            + line_spacing
        )

    return y


# =========================================================
# ROUNDED CARD
# =========================================================

def rounded_card(
    draw,
    box,
    fill,
    radius=30
):

    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill
    )


# =========================================================
# PREPARE AI IMAGE
# =========================================================

def prepare_ai_image(
    ai_visual,
    width,
    height
):

    if ai_visual is None:
        return None

    image = ai_visual.convert(
        "RGB"
    )

    ratio = max(
        width / image.width,
        height / image.height
    )

    new_width = int(
        image.width * ratio
    )

    new_height = int(
        image.height * ratio
    )

    image = image.resize(
        (
            new_width,
            new_height
        ),
        Image.Resampling.LANCZOS
    )

    left = (
        new_width - width
    ) // 2

    top = (
        new_height - height
    ) // 2

    image = image.crop(
        (
            left,
            top,
            left + width,
            top + height
        )
    )

    return image


# =========================================================
# PASTE AI IMAGE
# =========================================================

def paste_ai_image(
    base_image,
    ai_visual,
    box,
    radius=35,
    brightness=0.92
):

    if ai_visual is None:
        return

    x1, y1, x2, y2 = box

    width = x2 - x1
    height = y2 - y1

    image = prepare_ai_image(
        ai_visual,
        width,
        height
    )

    if image is None:
        return

    image = ImageEnhance.Brightness(
        image
    ).enhance(brightness)

    mask = Image.new(
        "L",
        (
            width,
            height
        ),
        0
    )

    mask_draw = ImageDraw.Draw(
        mask
    )

    mask_draw.rounded_rectangle(
        (
            0,
            0,
            width,
            height
        ),
        radius=radius,
        fill=255
    )

    base_image.paste(
        image,
        (
            x1,
            y1
        ),
        mask
    )


# =========================================================
# AI VISUAL PROMPT
# =========================================================

def build_visual_prompt(
    slide,
    design_plan
):

    title = clean_text(
        slide.get(
            "title",
            ""
        )
    )

    subtitle = clean_text(
        slide.get(
            "subtitle",
            ""
        )
    )

    visual_description = clean_text(
        slide.get(
            "visual_description",
            ""
        )
    )

    theme = design_plan.get(
        "theme",
        {}
    )

    theme_name = clean_text(
        theme.get(
            "name",
            "context-appropriate"
        )
    )

    visual_style = clean_text(
        design_plan.get(
            "visual_style",
            ""
        )
    )

    layout = clean_text(
        slide.get(
            "layout",
            design_plan.get(
                "layout",
                ""
            )
        )
    )

    topic = clean_text(
        design_plan.get(
            "topic",
            title
        )
    )

    prompt = f"""
Create a high-quality visual for a social media post.

Main topic:
{topic}

Slide title:
{title}

Slide context:
{subtitle}

Visual concept:
{visual_description}

Design theme:
{theme_name}

Visual style:
{visual_style}

Layout direction:
{layout}

Requirements:
- represent the actual topic and context
- follow the requested visual concept
- follow the design theme
- use a polished professional social-media aesthetic
- make the visual appropriate for the actual purpose of the post
- use context-appropriate realism, illustration, 3D, editorial,
  festive, celebratory, minimal, or other visual treatment
- create strong visual composition
- maintain useful negative space where text may be rendered
- do not generate important written content inside the image
- do not generate logos
- do not generate watermarks
- do not generate random typography
- do not add unrelated objects
"""

    return prompt.strip()


# =========================================================
# GENERATE SLIDE VISUAL
# =========================================================

def generate_slide_visual(
    slide,
    design_plan
):

    try:

        prompt = build_visual_prompt(
            slide,
            design_plan
        )

        print(
            f"🤖 Generating visual for slide "
            f"{slide.get('slide_number', '?')}..."
        )

        visual = generate_ai_visual(
            niche=design_plan.get(
                "inferred_niche",
                design_plan.get(
                    "theme",
                    {}
                ).get(
                    "name",
                    "Social Media"
                )
            ),
            topic=prompt,
            style=design_plan.get(
                "visual_style",
                design_plan.get(
                    "selected_style",
                    "Professional"
                )
            ),
            language=design_plan.get(
                "language",
                "English"
            )
        )

        print(
            f"✅ Visual generated for slide "
            f"{slide.get('slide_number', '?')}"
        )

        return visual

    except Exception as e:

        print(
            f"⚠️ Slide visual generation failed: {e}"
        )

        return None


# =========================================================
# GET AI DESIGN VALUES
# =========================================================

def get_design_values(
    slide,
    design_plan
):

    theme = design_plan.get(
        "theme",
        {}
    )

    # AI-selected colors.
    # Fallback values are only crash protection.

    primary_color = theme.get(
        "primary_color",
        "#1E3A8A"
    )

    secondary_color = theme.get(
        "secondary_color",
        primary_color
    )

    accent_color = theme.get(
        "accent_color",
        "#3B82F6"
    )

    background_color = theme.get(
        "background_color",
        "#FFFFFF"
    )

    text_color = theme.get(
        "text_color",
        "#111827"
    )

    # AI-selected layout.

    layout = slide.get(
        "layout",
        design_plan.get(
            "layout",
            ""
        )
    )

    layout = clean_text(
        layout
    ).lower()

    # AI-selected purpose.

    purpose = slide.get(
        "purpose",
        "content"
    )

    purpose = clean_text(
        purpose
    ).lower()

    return {
        "primary_color": primary_color,
        "secondary_color": secondary_color,
        "accent_color": accent_color,
        "background_color": background_color,
        "text_color": text_color,
        "layout": layout,
        "purpose": purpose
    }


# =========================================================
# RENDER SLIDE
# =========================================================

def render_slide(
    slide,
    design_plan,
    output_path,
    ai_visual=None,
    slide_index=0
):

    values = get_design_values(
        slide,
        design_plan
    )

    primary_color = values[
        "primary_color"
    ]

    secondary_color = values[
        "secondary_color"
    ]

    accent_color = values[
        "accent_color"
    ]

    background_color = values[
        "background_color"
    ]

    text_color = values[
        "text_color"
    ]

    layout = values[
        "layout"
    ]

    purpose = values[
        "purpose"
    ]

    # =====================================================
    # BACKGROUND
    # =====================================================

    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT
        ),
        hex_to_rgb(
            background_color
        )
    )

    draw = ImageDraw.Draw(
        image
    )

    # AI-selected theme controls
    # the background instead of a fixed palette.

    draw_gradient(
        draw,
        background_color,
        secondary_color
    )

    # =====================================================
    # DATA
    # =====================================================

    slide_number = slide.get(
        "slide_number",
        slide_index + 1
    )

    title = clean_text(
        slide.get(
            "title",
            ""
        )
    )

    subtitle = clean_text(
        slide.get(
            "subtitle",
            ""
        )
    )

    body = clean_text(
        slide.get(
            "body",
            ""
        )
    )

    visual_description = clean_text(
        slide.get(
            "visual_description",
            ""
        )
    )

    # =====================================================
    # FONTS
    # =====================================================

    small_font = get_font(
        25
    )

    label_font = get_font(
        30,
        bold=True
    )

    title_font = get_font(
        58,
        bold=True
    )

    subtitle_font = get_font(
        33
    )

    body_font = get_font(
        29
    )

    number_font = get_font(
        38,
        bold=True
    )

    # =====================================================
    # AI-DRIVEN LAYOUT
    # =====================================================

    # We don't choose the creative layout here.
    # We only implement layouts selected by Design Agent.

    is_cover = (
        purpose == "cover"
        or layout in [
            "cover",
            "hero",
            "hero_cover",
            "title"
        ]
    )

    is_final = (
        purpose in [
            "final",
            "takeaway",
            "cta"
        ]
        or layout in [
            "final",
            "takeaway",
            "cta"
        ]
    )

    is_split = (
        "split" in layout
        or layout in [
            "editorial_split",
            "split_screen",
            "image_text_split"
        ]
    )

    is_image_first = (
        "image" in layout
        and "text" not in layout
    )

    # =====================================================
    # COVER / HERO
    # =====================================================

    if is_cover:

        draw.rounded_rectangle(
            (
                70,
                50,
                260,
                72
            ),
            radius=12,
            fill=accent_color
        )

        draw.text(
            (
                70,
                105
            ),
            "AI SOCIAL MEDIA MANAGER",
            font=small_font,
            fill=primary_color
        )

        draw_wrapped_text(
            draw,
            title,
            (
                70,
                175
            ),
            title_font,
            primary_color,
            930,
            line_spacing=8
        )

        if subtitle:

            draw_wrapped_text(
                draw,
                subtitle,
                (
                    70,
                    350
                ),
                subtitle_font,
                text_color,
                900,
                line_spacing=8
            )

        if ai_visual is not None:

            paste_ai_image(
                image,
                ai_visual,
                (
                    70,
                    470,
                    1010,
                    825
                ),
                radius=35,
                brightness=0.94
            )

        if body:

            rounded_card(
                draw,
                (
                    70,
                    875,
                    1010,
                    1135
                ),
                "#FFFFFF",
                radius=28
            )

            draw.text(
                (
                    105,
                    910
                ),
                "OVERVIEW",
                font=label_font,
                fill=accent_color
            )

            draw_wrapped_text(
                draw,
                body,
                (
                    105,
                    965
                ),
                body_font,
                text_color,
                850,
                line_spacing=8
            )

    # =====================================================
    # FINAL / TAKEAWAY / CTA
    # =====================================================

    elif is_final:

        draw.text(
            (
                70,
                85
            ),
            "KEY TAKEAWAY",
            font=label_font,
            fill=accent_color
        )

        draw_wrapped_text(
            draw,
            title,
            (
                70,
                155
            ),
            title_font,
            primary_color,
            920,
            line_spacing=8
        )

        if ai_visual is not None:

            paste_ai_image(
                image,
                ai_visual,
                (
                    70,
                    360,
                    1010,
                    680
                ),
                radius=32,
                brightness=0.94
            )

        if body:

            rounded_card(
                draw,
                (
                    70,
                    730,
                    1010,
                    1015
                ),
                "#FFFFFF",
                radius=28
            )

            draw_wrapped_text(
                draw,
                body,
                (
                    105,
                    780
                ),
                body_font,
                text_color,
                850,
                line_spacing=9
            )

        cta_data = design_plan.get(
            "cta",
            {}
        )

        if isinstance(
            cta_data,
            dict
        ):

            cta = clean_text(
                cta_data.get(
                    "text",
                    ""
                )
            )

        else:

            cta = clean_text(
                cta_data
            )

        if cta:

            draw.rounded_rectangle(
                (
                    105,
                    1055,
                    975,
                    1160
                ),
                radius=25,
                fill=primary_color
            )

            draw_wrapped_text(
                draw,
                cta,
                (
                    140,
                    1085
                ),
                label_font,
                "#FFFFFF",
                800,
                line_spacing=5
            )

    # =====================================================
    # IMAGE-FIRST LAYOUT
    # =====================================================

    elif is_image_first:

        if ai_visual is not None:

            paste_ai_image(
                image,
                ai_visual,
                (
                    40,
                    40,
                    1040,
                    820
                ),
                radius=40,
                brightness=0.94
            )

        draw_wrapped_text(
            draw,
            title,
            (
                70,
                865
            ),
            title_font,
            primary_color,
            900,
            line_spacing=8
        )

        if subtitle:

            draw_wrapped_text(
                draw,
                subtitle,
                (
                    70,
                    1010
                ),
                subtitle_font,
                text_color,
                900,
                line_spacing=8
            )

        if body:

            draw_wrapped_text(
                draw,
                body,
                (
                    70,
                    1110
                ),
                body_font,
                text_color,
                900,
                line_spacing=7
            )

    # =====================================================
    # SPLIT LAYOUT
    # =====================================================

    elif is_split:

        # Text side

        rounded_card(
            draw,
            (
                50,
                50,
                530,
                1300
            ),
            "#FFFFFF",
            radius=35
        )

        draw.rounded_rectangle(
            (
                80,
                80,
                190,
                190
            ),
            radius=30,
            fill=primary_color
        )

        draw.text(
            (
                112,
                105
            ),
            str(slide_number),
            font=number_font,
            fill="#FFFFFF"
        )

        draw_wrapped_text(
            draw,
            title,
            (
                80,
                250
            ),
            title_font,
            primary_color,
            390,
            line_spacing=8
        )

        if subtitle:

            draw_wrapped_text(
                draw,
                subtitle,
                (
                    80,
                    500
                ),
                subtitle_font,
                text_color,
                390,
                line_spacing=8
            )

        if body:

            draw_wrapped_text(
                draw,
                body,
                (
                    80,
                    700
                ),
                body_font,
                text_color,
                390,
                line_spacing=8
            )

        # Image side

        if ai_visual is not None:

            paste_ai_image(
                image,
                ai_visual,
                (
                    560,
                    50,
                    1030,
                    1300
                ),
                radius=35,
                brightness=0.94
            )

    # =====================================================
    # STANDARD CONTENT LAYOUT
    # =====================================================

    else:

        # Number

        draw.rounded_rectangle(
            (
                70,
                60,
                155,
                145
            ),
            radius=25,
            fill=primary_color
        )

        draw.text(
            (
                95,
                80
            ),
            str(slide_number),
            font=number_font,
            fill="#FFFFFF"
        )

        # Title

        draw_wrapped_text(
            draw,
            title,
            (
                190,
                60
            ),
            title_font,
            primary_color,
            800,
            line_spacing=7
        )

        # Subtitle

        if subtitle:

            draw_wrapped_text(
                draw,
                subtitle,
                (
                    70,
                    225
                ),
                subtitle_font,
                text_color,
                900,
                line_spacing=7
            )

        # Visual

        if ai_visual is not None:

            paste_ai_image(
                image,
                ai_visual,
                (
                    70,
                    330,
                    1010,
                    690
                ),
                radius=32,
                brightness=0.94
            )

        # Information

        if body:

            rounded_card(
                draw,
                (
                    70,
                    730,
                    1010,
                    1070
                ),
                "#FFFFFF",
                radius=28
            )

            draw_wrapped_text(
                draw,
                body,
                (
                    105,
                    775
                ),
                body_font,
                text_color,
                850,
                line_spacing=9
            )

        # Visual concept

        if visual_description:

            draw_wrapped_text(
                draw,
                "Visual concept: "
                + visual_description,
                (
                    105,
                    1085
                ),
                small_font,
                accent_color,
                850,
                line_spacing=6
            )

    # =====================================================
    # BRANDING
    # =====================================================

    draw.text(
        (
            750,
            1285
        ),
        "AI Social Media Manager",
        font=small_font,
        fill=primary_color
    )

    # =====================================================
    # SAVE
    # =====================================================

    image.save(
        output_path,
        quality=95
    )

    return output_path


# =========================================================
# RENDER COMPLETE SOCIAL POST
# =========================================================

def render_social_post(
    design_plan
):

    post_id = str(
        uuid.uuid4()
    )

    post_output_dir = os.path.join(
        OUTPUT_DIR,
        post_id
    )

    os.makedirs(
        post_output_dir,
        exist_ok=True
    )

    slides = design_plan.get(
        "slides",
        []
    )

    if not slides:

        raise ValueError(
            "Design plan contains no slides."
        )

    generated_images = []

    for index, slide in enumerate(
        slides
    ):

        print(
            f"\n🎨 Processing slide "
            f"{index + 1}/{len(slides)}"
        )

        # =================================================
        # GENERATE AI VISUAL
        # =================================================

        ai_visual = generate_slide_visual(
            slide,
            design_plan
        )

        # =================================================
        # SAVE RAW AI VISUAL
        # =================================================

        if ai_visual is not None:

            ai_visual_path = os.path.join(
                post_output_dir,
                f"ai_visual_{index + 1}.png"
            )

            ai_visual.save(
                ai_visual_path
            )

            print(
                f"🖼️ AI visual saved: "
                f"{ai_visual_path}"
            )

        # =================================================
        # RENDER FINAL SOCIAL MEDIA SLIDE
        # =================================================

        output_path = os.path.join(
            post_output_dir,
            f"slide_{index + 1}.png"
        )

        render_slide(
            slide,
            design_plan,
            output_path,
            ai_visual=ai_visual,
            slide_index=index
        )

        print(
            f"✅ Final slide saved: "
            f"{output_path}"
        )

        generated_images.append(
            {
                "slide_number": index + 1,
                "filename": (
                    f"slide_{index + 1}.png"
                ),
                "path": output_path,
                "url": (
                    f"/generated-images/"
                    f"{post_id}/"
                    f"slide_{index + 1}.png"
                )
            }
        )

    # =====================================================
    # RESULT
    # =====================================================

    return {
        "status": "success",
        "post_id": post_id,
        "format": design_plan.get(
            "format",
            "single_post"
        ),
        "slide_count": len(
            generated_images
        ),
        "images": generated_images
    }