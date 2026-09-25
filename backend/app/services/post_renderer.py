# backend/app/services/post_renderer.py
import uuid
import os
import textwrap
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

from app.services.image_generator import generate_ai_visual
from app.services.structured_visual_renderer import render_structured_visual


# ============================================================
# CANVAS
# ============================================================

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350

DEFAULT_MARGIN = 64
MIN_MARGIN = 40

DEFAULT_RADIUS = 28


# ============================================================
# FONT HELPERS
# ============================================================

def _font_path(bold: bool = False) -> str:
    """
    Tries common Windows fonts first.
    Falls back to DejaVu Sans if available.
    """

    candidates = []

    if bold:
        candidates = [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return ""


def get_font(size: int, bold: bool = False):
    path = _font_path(bold=bold)

    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass

    return ImageFont.load_default()


# ============================================================
# BASIC HELPERS
# ============================================================

def _safe_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _hex_to_rgb(value: str, fallback=(245, 245, 245)):
    value = _safe_text(value)

    if not value:
        return fallback

    value = value.replace("#", "")

    if len(value) != 6:
        return fallback

    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _rounded_rectangle(
    draw: ImageDraw.ImageDraw,
    box,
    radius: int,
    fill,
    outline=None,
    width: int = 1,
):
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


# ============================================================
# DESIGN VALUES
# ============================================================

def get_design_values(design: dict) -> dict:
    """
    Safely extracts all AI-generated design metadata.

    Renderer never assumes that the AI returned every field.
    """

    design = design if isinstance(design, dict) else {}

    canvas = design.get("canvas")
    if not isinstance(canvas, dict):
        canvas = {}

    theme = design.get("theme")
    if not isinstance(theme, dict):
        theme = {}

    background = design.get("background")
    if not isinstance(background, dict):
        background = {}

    global_layout = design.get("global_layout")
    if not isinstance(global_layout, dict):
        global_layout = {}

    return {
        "canvas": canvas,
        "theme": theme,
        "background": background,
        "global_layout": global_layout,

        "background_type": _safe_text(
            background.get("type")
        ).lower(),

        "background_description": _safe_text(
            background.get("description")
        ),

        "ai_visual_required": background.get(
            "ai_visual_required",
            True,
        ),

        "ai_visual_prompt": _safe_text(
            background.get("ai_visual_prompt")
        ),

        "environment": _safe_text(
            background.get("environment")
        ),

        "subject": _safe_text(
            background.get("subject")
        ),

        "visual_style": _safe_text(
            background.get("visual_style")
        ),

        "lighting": _safe_text(
            background.get("lighting")
        ),

        "background_composition": _safe_text(
            background.get("composition")
        ),

        "background_safe_area": _safe_text(
            background.get("text_safe_area")
        ),

        "composition_type": _safe_text(
            global_layout.get("composition_type")
        ).lower(),

        "image_position": _safe_text(
            global_layout.get("image_position")
        ).lower(),

        "text_position": _safe_text(
            global_layout.get("text_position")
        ).lower(),

        "text_safe_area": _safe_text(
            global_layout.get("text_safe_area")
        ),

        "visual_balance": _safe_text(
            global_layout.get("visual_balance")
        ),

        "style": _safe_text(
            global_layout.get("style")
        ),

        "padding": _safe_text(
            global_layout.get("padding")
        ),

        "alignment": _safe_text(
            global_layout.get("alignment")
        ),

        "card_style": _safe_text(
            global_layout.get("card_style")
        ),

        "border_radius": _safe_text(
            global_layout.get("border_radius")
        ),
    }


# ============================================================
# COLOR HELPERS
# ============================================================

def _theme_color(theme: dict, keys, fallback):
    for key in keys:
        value = theme.get(key)

        if value:
            return _hex_to_rgb(value, fallback)

    return fallback


def get_theme_colors(design: dict):
    values = get_design_values(design)

    theme = values["theme"]

    background = _theme_color(
        theme,
        [
            "background",
            "background_color",
            "bg",
        ],
        (245, 245, 245),
    )

    primary = _theme_color(
        theme,
        [
            "primary",
            "primary_color",
            "accent",
        ],
        (25, 25, 25),
    )

    secondary = _theme_color(
        theme,
        [
            "secondary",
            "secondary_color",
        ],
        (90, 90, 90),
    )

    text = _theme_color(
        theme,
        [
            "text",
            "text_color",
        ],
        (20, 20, 20),
    )

    muted = _theme_color(
        theme,
        [
            "muted",
            "muted_text",
        ],
        (100, 100, 100),
    )

    return {
        "background": background,
        "primary": primary,
        "secondary": secondary,
        "text": text,
        "muted": muted,
    }


# ============================================================
# TEXT MEASUREMENT
# ============================================================

def _text_bbox(
    draw,
    text,
    font,
    spacing=8,
    stroke_width=0,
):
    if not text:
        return (0, 0, 0, 0)

    return draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        spacing=spacing,
        stroke_width=stroke_width,
    )


def _text_size(
    draw,
    text,
    font,
    spacing=8,
):
    bbox = _text_bbox(
        draw,
        text,
        font,
        spacing=spacing,
    )

    return (
        max(0, bbox[2] - bbox[0]),
        max(0, bbox[3] - bbox[1]),
    )


def _wrap_text(
    draw,
    text: str,
    font,
    max_width: int,
):
    text = _safe_text(text)

    if not text:
        return ""

    words = text.split()

    if not words:
        return ""

    lines = []
    current = ""

    for word in words:
        test = word if not current else f"{current} {word}"

        width, _ = _text_size(
            draw,
            test,
            font,
        )

        if width <= max_width:
            current = test
            continue

        if current:
            lines.append(current)

        current = word

    if current:
        lines.append(current)

    return "\n".join(lines)


def _fit_text(
    draw,
    text: str,
    max_width: int,
    max_height: int,
    max_size: int,
    min_size: int = 24,
    bold: bool = False,
    spacing: int = 8,
):
    """
    Dynamically reduces font size until the text fits.
    """

    text = _safe_text(text)

    if not text:
        return "", get_font(min_size, bold=bold)

    for size in range(max_size, min_size - 1, -2):
        font = get_font(size, bold=bold)

        wrapped = _wrap_text(
            draw,
            text,
            font,
            max_width,
        )

        width, height = _text_size(
            draw,
            wrapped,
            font,
            spacing=spacing,
        )

        if width <= max_width and height <= max_height:
            return wrapped, font

    font = get_font(min_size, bold=bold)

    wrapped = _wrap_text(
        draw,
        text,
        font,
        max_width,
    )

    return wrapped, font


# ============================================================
# SAFE AREA
# ============================================================

def resolve_safe_area(
    design_values: dict,
    width: int,
    height: int,
):
    """
    AI safe-area metadata is used as guidance.
    Renderer always keeps a minimum physical margin.
    """

    safe_text = (
        design_values.get("text_safe_area")
        or design_values.get("background_safe_area")
        or ""
    ).lower()

    margin = DEFAULT_MARGIN

    if "wide" in safe_text:
        margin = 80

    if "large" in safe_text:
        margin = 96

    margin = _clamp(
        margin,
        MIN_MARGIN,
        140,
    )

    return (
        margin,
        margin,
        width - margin,
        height - margin,
    )


# ============================================================
# BACKGROUND
# ============================================================

def draw_background(
    image: Image.Image,
    design: dict,
):
    """
    Creates a clean background.

    Gradient is NOT automatically applied to every design.
    """

    values = get_design_values(design)
    colors = get_theme_colors(design)

    bg_type = values["background_type"]
    visual_style = values["visual_style"].lower()

    background_color = colors["background"]

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Plain / minimal background
    # --------------------------------------------------------

    if (
        bg_type in {
            "solid",
            "plain",
            "minimal",
            "flat",
        }
        or "minimal" in visual_style
    ):
        draw.rectangle(
            [0, 0, image.width, image.height],
            fill=background_color,
        )
        return

    # --------------------------------------------------------
    # Gradient only when requested
    # --------------------------------------------------------

    if (
        "gradient" in bg_type
        or "gradient" in visual_style
    ):
        primary = colors["primary"]

        for y in range(image.height):
            ratio = y / max(1, image.height - 1)

            color = tuple(
                int(
                    background_color[i] * (1 - ratio)
                    + primary[i] * ratio * 0.18
                )
                for i in range(3)
            )

            draw.line(
                [(0, y), (image.width, y)],
                fill=color,
            )

        return

    # --------------------------------------------------------
    # Dark cinematic
    # --------------------------------------------------------

    if (
        "dark" in bg_type
        or "cinematic" in visual_style
    ):
        dark = tuple(
            int(v * 0.35)
            for v in background_color
        )

        draw.rectangle(
            [0, 0, image.width, image.height],
            fill=dark,
        )
        return

    # --------------------------------------------------------
    # Default clean background
    # --------------------------------------------------------

    draw.rectangle(
        [0, 0, image.width, image.height],
        fill=background_color,
    )


# ============================================================
# AI IMAGE PROCESSING
# ============================================================

def _resolve_image_box(
    image_position: str,
    composition: str,
    canvas_width: int,
    canvas_height: int,
):
    """
    Generic composition support.

    These are renderer capabilities, NOT topic mappings.
    """

    position = (
        f"{image_position} {composition}"
    ).lower()

    if (
        "left" in position
        and "right" not in position
    ):
        return (
            0,
            0,
            int(canvas_width * 0.55),
            canvas_height,
        )

    if "right" in position:
        return (
            int(canvas_width * 0.45),
            0,
            canvas_width,
            canvas_height,
        )

    if "top" in position:
        return (
            0,
            0,
            canvas_width,
            int(canvas_height * 0.58),
        )

    if "bottom" in position:
        return (
            0,
            int(canvas_height * 0.42),
            canvas_width,
            canvas_height,
        )

    if "center" in position:
        return (
            int(canvas_width * 0.08),
            int(canvas_height * 0.08),
            int(canvas_width * 0.92),
            int(canvas_height * 0.92),
        )

    # Full bleed is the safest fallback for image-first designs.
    return (
        0,
        0,
        canvas_width,
        canvas_height,
    )


def paste_ai_image(
    base: Image.Image,
    ai_image: Image.Image | None,
    image_position: str = "",
    composition: str = "",
    opacity: int = 255,
):
    if ai_image is None:
        return base

    if not isinstance(ai_image, Image.Image):
        return base

    box = _resolve_image_box(
        image_position=image_position,
        composition=composition,
        canvas_width=base.width,
        canvas_height=base.height,
    )

    x1, y1, x2, y2 = box

    target_width = max(1, x2 - x1)
    target_height = max(1, y2 - y1)

    try:
        fitted = ImageOps.fit(
            ai_image.convert("RGB"),
            (target_width, target_height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    except Exception:
        fitted = ai_image.convert("RGB").resize(
            (target_width, target_height),
            Image.Resampling.LANCZOS,
        )

    if opacity < 255:
        fitted = fitted.convert("RGBA")
        alpha = fitted.getchannel("A")
        alpha = alpha.point(
            lambda value: int(value * opacity / 255)
        )
        fitted.putalpha(alpha)

        base.paste(
            fitted,
            (x1, y1),
            fitted,
        )
    else:
        base.paste(
            fitted,
            (x1, y1),
        )

    return base


# ============================================================
# OVERLAY HELPERS
# ============================================================

def draw_overlay(
    image: Image.Image,
    box,
    color=(0, 0, 0),
    alpha=90,
    radius=24,
):
    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(overlay)

    x1, y1, x2, y2 = box

    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        fill=(
            color[0],
            color[1],
            color[2],
            alpha,
        ),
    )

    image.alpha_composite(overlay)


def add_soft_vignette(image: Image.Image):
    """
    Very subtle vignette for readability.
    """

    width, height = image.size

    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(overlay)

    # Subtle bottom fade
    for i in range(220):
        alpha = int(
            55 * (i / 220)
        )

        y = height - 220 + i

        draw.line(
            [(0, y), (width, y)],
            fill=(0, 0, 0, alpha),
        )

    image.alpha_composite(overlay)


# ============================================================
# TEXT READABILITY HELPERS
# ============================================================

def _relative_luminance(rgb):
    """Approximate perceived luminance in the 0..1 range."""
    r, g, b = [max(0, min(255, int(v))) / 255.0 for v in rgb[:3]]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _sample_region_luminance(image: Image.Image, box):
    """Sample the rendered image region to decide whether text needs a panel."""
    try:
        x1, y1, x2, y2 = [int(v) for v in box]
        x1 = max(0, min(image.width - 1, x1))
        y1 = max(0, min(image.height - 1, y1))
        x2 = max(x1 + 1, min(image.width, x2))
        y2 = max(y1 + 1, min(image.height, y2))
        crop = image.convert("RGB").crop((x1, y1, x2, y2))
        # Downsample so this remains cheap even for 1080x1350 renders.
        crop.thumbnail((32, 32))
        pixels = list(crop.getdata())
        if not pixels:
            return 0.5
        return sum(_relative_luminance(px) for px in pixels) / len(pixels)
    except Exception:
        return 0.5


def _text_color_for_region(image: Image.Image, box, preferred):
    """Choose readable text color while respecting the preferred theme color when possible."""
    lum = _sample_region_luminance(image, box)
    preferred_lum = _relative_luminance(preferred)

    # Dark image/background -> light text. Light image/background -> dark text.
    if lum < 0.45:
        return (255, 255, 255)
    if lum > 0.62:
        return (18, 18, 18)

    return preferred if preferred_lum < 0.5 else (255, 255, 255)


def _add_readability_panel(image: Image.Image, box, text_color, force=False):
    """Add a restrained translucent panel behind text when the visual is busy."""
    x1, y1, x2, y2 = [int(v) for v in box]
    pad_x = 28
    pad_y = 24
    panel = (
        max(18, x1 - pad_x),
        max(18, y1 - pad_y),
        min(image.width - 18, x2 + pad_x),
        min(image.height - 18, y2 + pad_y),
    )

    # If text is light, use a dark panel; otherwise use a light panel.
    if _relative_luminance(text_color) > 0.55:
        fill = (0, 0, 0, 168 if force else 145)
    else:
        fill = (255, 255, 255, 220 if force else 188)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle(panel, radius=DEFAULT_RADIUS, fill=fill)
    image.alpha_composite(overlay)

    return panel


def _boxes_overlap(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)


# ============================================================
# TEXT BLOCKS
# ============================================================

def draw_text_block(
    image: Image.Image,
    text: str,
    box,
    colors,
    max_size: int,
    min_size: int,
    bold: bool = False,
    alignment: str = "left",
):
    text = _safe_text(text)

    if not text:
        return

    draw = ImageDraw.Draw(image)

    x1, y1, x2, y2 = box

    width = max(1, x2 - x1)
    height = max(1, y2 - y1)

    wrapped, font = _fit_text(
        draw,
        text,
        max_width=width,
        max_height=height,
        max_size=max_size,
        min_size=min_size,
        bold=bold,
        spacing=8,
    )

    bbox = _text_bbox(
        draw,
        wrapped,
        font,
        spacing=8,
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    if alignment == "center":
        x = x1 + (width - text_width) / 2
    elif alignment == "right":
        x = x2 - text_width
    else:
        x = x1

    y = y1 + max(
        0,
        (height - text_height) / 2,
    )

    draw.multiline_text(
        (int(x), int(y)),
        wrapped,
        font=font,
        fill=colors["text"],
        spacing=8,
        align=alignment,
    )


# ============================================================
# SLIDE CONTENT
# ============================================================

def _get_slide_text(slide: dict):
    title = _safe_text(
        slide.get("title")
        or slide.get("headline")
    )

    subtitle = _safe_text(
        slide.get("subtitle")
        or slide.get("subheadline")
    )

    body = _safe_text(
        slide.get("body")
        or slide.get("description")
        or slide.get("content")
    )

    takeaway = _safe_text(
        slide.get("key_takeaway")
        or slide.get("takeaway")
    )

    return {
        "title": title,
        "subtitle": subtitle,
        "body": body,
        "takeaway": takeaway,
    }


def _get_slide_design_values(
    slide: dict,
    design: dict,
):
    """
    Slide-level values override global values.
    """

    global_values = get_design_values(design)

    composition = _safe_text(
        slide.get("composition")
    ).lower()

    if not composition:
        composition = global_values["composition_type"]

    image_position = _safe_text(
        slide.get("image_position")
    ).lower()

    if not image_position:
        image_position = global_values["image_position"]

    text_position = _safe_text(
        slide.get("text_position")
    ).lower()

    if not text_position:
        text_position = global_values["text_position"]

    text_safe_area = _safe_text(
        slide.get("text_safe_area")
    )

    if not text_safe_area:
        text_safe_area = global_values["text_safe_area"]

    text_alignment = _safe_text(
        slide.get("text_alignment")
    ).lower()

    if not text_alignment:
        text_alignment = "left"

    return {
        "composition": composition,
        "image_position": image_position,
        "text_position": text_position,
        "text_safe_area": text_safe_area,
        "text_alignment": text_alignment,
    }


# ============================================================
# LAYOUT RESOLUTION
# ============================================================

def resolve_layout_boxes(
    composition: str,
    image_position: str,
    text_position: str,
    width: int,
    height: int,
):
    """
    Converts AI composition instructions into renderer boxes.

    No topic-specific logic is used here.
    """

    composition = _safe_text(composition).lower()
    image_position = _safe_text(image_position).lower()
    text_position = _safe_text(text_position).lower()

    margin = DEFAULT_MARGIN

    full = (
        margin,
        margin,
        width - margin,
        height - margin,
    )

    # --------------------------------------------------------
    # Full image / overlay
    # --------------------------------------------------------

    if (
        "full_bleed" in composition
        or "image_full" in composition
        or "centered_overlay" in composition
        or "image_dominant" in composition
    ):
        image_box = (
            0,
            0,
            width,
            height,
        )

        text_box = (
            margin,
            int(height * 0.60),
            width - margin,
            height - margin,
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Image left / text right
    # --------------------------------------------------------

    if (
        "image_left" in composition
        or (
            "left" in image_position
            and "right" in text_position
        )
    ):
        image_box = (
            0,
            0,
            int(width * 0.52),
            height,
        )

        text_box = (
            int(width * 0.56),
            margin,
            width - margin,
            height - margin,
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Text left / image right
    # --------------------------------------------------------

    if (
        "text_left" in composition
        or (
            "right" in image_position
            and "left" in text_position
        )
    ):
        image_box = (
            int(width * 0.48),
            0,
            width,
            height,
        )

        text_box = (
            margin,
            margin,
            int(width * 0.43),
            height - margin,
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Image top / text bottom
    # --------------------------------------------------------

    if (
        "image_top" in composition
        or (
            "top" in image_position
            and "bottom" in text_position
        )
    ):
        image_box = (
            0,
            0,
            width,
            int(height * 0.58),
        )

        text_box = (
            margin,
            int(height * 0.63),
            width - margin,
            height - margin,
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Text top / image bottom
    # --------------------------------------------------------

    if (
        "text_top" in composition
        or (
            "bottom" in image_position
            and "top" in text_position
        )
    ):
        text_box = (
            margin,
            margin,
            width - margin,
            int(height * 0.40),
        )

        image_box = (
            0,
            int(height * 0.43),
            width,
            height,
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Diagonal / editorial / asymmetric
    # --------------------------------------------------------

    if (
        "diagonal" in composition
        or "editorial" in composition
        or "asymmetric" in composition
    ):
        image_box = (
            int(width * 0.35),
            int(height * 0.08),
            width - margin,
            int(height * 0.88),
        )

        text_box = (
            margin,
            int(height * 0.20),
            int(width * 0.55),
            int(height * 0.80),
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Collage
    # --------------------------------------------------------

    if "collage" in composition:
        image_box = (
            int(width * 0.10),
            int(height * 0.18),
            int(width * 0.90),
            int(height * 0.78),
        )

        text_box = (
            margin,
            margin,
            width - margin,
            int(height * 0.25),
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Typographic
    # --------------------------------------------------------

    if (
        "typographic" in composition
        or "text_dominant" in composition
        or "minimal" in composition
    ):
        text_box = full

        image_box = (
            int(width * 0.60),
            int(height * 0.55),
            width - margin,
            height - margin,
        )

        return image_box, text_box

    # --------------------------------------------------------
    # Default balanced layout
    # --------------------------------------------------------

    image_box = (
        int(width * 0.50),
        int(height * 0.08),
        width - margin,
        int(height * 0.92),
    )

    text_box = (
        margin,
        int(height * 0.16),
        int(width * 0.47),
        int(height * 0.84),
    )

    return image_box, text_box


# ============================================================
# SINGLE SLIDE RENDER
# ============================================================

def render_slide(
    slide: dict,
    design: dict,
    ai_image: Image.Image | None = None,
    slide_index: int = 0,
    total_slides: int = 1,
    planner_data: dict | None = None,
):
    """
    Main slide renderer.

    AI decides the design.
    Renderer executes it safely.
    """

    planner_data = planner_data or {}

    width = CANVAS_WIDTH
    height = CANVAS_HEIGHT

    image = Image.new(
        "RGBA",
        (width, height),
        (245, 245, 245, 255),
    )

    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    draw_background(
        image,
        design,
    )

    values = get_design_values(design)
    colors = get_theme_colors(design)

    slide_values = _get_slide_design_values(
        slide,
        design,
    )

    visual_strategy = design.get("visual_strategy", {})
    if not isinstance(visual_strategy, dict):
        visual_strategy = {}

    visual_type = _safe_text(
        slide.get("visual_type")
        or visual_strategy.get("type")
    ).lower()

    renderer = _safe_text(
        visual_strategy.get("renderer")
    ).lower()

    if not renderer:
        renderer = (
            "ai_image"
            if visual_type in {"photo", "illustration"}
            else "chart"
            if visual_type == "graph"
            else "structured"
        )

    composition = slide_values["composition"]
    image_position = slide_values["image_position"]
    text_position = slide_values["text_position"]
    text_alignment = slide_values["text_alignment"]

    # --------------------------------------------------------
    # AI image
    # --------------------------------------------------------

    if ai_image is not None:
        image_box, text_box = resolve_layout_boxes(
            composition=composition,
            image_position=image_position,
            text_position=text_position,
            width=width,
            height=height,
        )

        # Resize/crop according to AI composition.
        image_for_slide = ImageOps.fit(
            ai_image.convert("RGB"),
            (
                max(1, image_box[2] - image_box[0]),
                max(1, image_box[3] - image_box[1]),
            ),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

        image.paste(
            image_for_slide,
            (
                image_box[0],
                image_box[1],
            ),
        )

    else:
        _, text_box = resolve_layout_boxes(
            composition=composition,
            image_position=image_position,
            text_position=text_position,
            width=width,
            height=height,
        )

    # --------------------------------------------------------
    # Structured visual layer
    # --------------------------------------------------------
    # Structured/chart/hybrid types are rendered with PIL so exact text,
    # numbers and labels stay under our control. AI image generation is
    # never used for these unless the Design Agent explicitly requested
    # a hybrid treatment.
    if visual_type in {
        "infographic", "graph", "timeline", "cards",
        "event_poster", "diagram"
    } and renderer in {"structured", "chart", "hybrid"}:
        try:
            rendered_structured = render_structured_visual(
                image=image,
                visual_type=visual_type,
                slide=slide,
                design=design,
                planner_data=planner_data,
            )
            if not rendered_structured:
                print(
                    f"[WARN] No structured data available for visual_type={visual_type}; "
                    "falling back to text-safe composition."
                )
        except Exception as exc:
            # Never break a working post because an optional visual renderer fails.
            print(
                f"[WARN] Structured visual rendering failed for "
                f"slide {slide_index + 1}: {type(exc).__name__}: {exc}"
            )

    # --------------------------------------------------------
    # Read slide text
    # --------------------------------------------------------

    text_data = _get_slide_text(slide)

    title = text_data["title"]
    subtitle = text_data["subtitle"]
    body = text_data["body"]
    takeaway = text_data["takeaway"]

    # --------------------------------------------------------
    # Decide readability overlay / text-safe panel
    # --------------------------------------------------------

    overlay_needed = (
        "overlay" in composition
        or "full_bleed" in composition
        or "image_dominant" in composition
        or "centered" in composition
    )

    # The design agent chooses the composition, but the renderer owns
    # the final readability guarantee. Never rely on the AI image itself
    # to contain readable text.
    preferred_text = colors["text"]
    effective_text_color = preferred_text

    if ai_image is not None:
        effective_text_color = _text_color_for_region(
            image,
            text_box,
            preferred_text,
        )

        image_box_for_layout, _ = resolve_layout_boxes(
            composition=composition,
            image_position=image_position,
            text_position=text_position,
            width=width,
            height=height,
        )

        text_over_image = _boxes_overlap(text_box, image_box_for_layout)

        if overlay_needed or text_over_image:
            # Full-bleed/overlay layouts get a stronger panel; split layouts
            # get a lighter panel only when text actually sits over imagery.
            _add_readability_panel(
                image,
                text_box,
                effective_text_color,
                force=overlay_needed,
            )

    # Use the computed color for every text element on this slide.
    colors = dict(colors)
    colors["text"] = effective_text_color

    # --------------------------------------------------------
    # Text layout
    # --------------------------------------------------------

    tx1, ty1, tx2, ty2 = text_box

    text_width = max(
        1,
        tx2 - tx1,
    )

    current_y = ty1

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    if title:
        title_height_limit = int(
            max(150, (ty2 - ty1) * 0.30)
        )

        title_wrapped, title_font = _fit_text(
            draw,
            title,
            max_width=text_width,
            max_height=title_height_limit,
            max_size=68,
            min_size=34,
            bold=True,
            spacing=8,
        )

        title_bbox = _text_bbox(
            draw,
            title_wrapped,
            title_font,
            spacing=8,
        )

        title_height = (
            title_bbox[3] - title_bbox[1]
        )

        if text_alignment == "center":
            title_x = tx1 + (
                text_width
                - (title_bbox[2] - title_bbox[0])
            ) / 2
        elif text_alignment == "right":
            title_x = tx2 - (
                title_bbox[2] - title_bbox[0]
            )
        else:
            title_x = tx1

        # Small stroke keeps large headlines readable over detailed imagery.
        title_stroke = 2 if ai_image is not None else 0
        stroke_fill = (0, 0, 0) if _relative_luminance(colors["text"]) > 0.55 else (255, 255, 255)
        draw.multiline_text(
            (
                int(title_x),
                int(current_y),
            ),
            title_wrapped,
            font=title_font,
            fill=colors["text"],
            spacing=8,
            align=text_alignment,
            stroke_width=title_stroke,
            stroke_fill=stroke_fill,
        )

        current_y += title_height + 18

    # --------------------------------------------------------
    # Subtitle
    # --------------------------------------------------------

    if subtitle and current_y < ty2:
        subtitle_height_limit = int(
            max(100, (ty2 - current_y) * 0.24)
        )

        subtitle_wrapped, subtitle_font = _fit_text(
            draw,
            subtitle,
            max_width=text_width,
            max_height=subtitle_height_limit,
            max_size=34,
            min_size=22,
            bold=False,
            spacing=7,
        )

        subtitle_bbox = _text_bbox(
            draw,
            subtitle_wrapped,
            subtitle_font,
            spacing=7,
        )

        subtitle_height = (
            subtitle_bbox[3]
            - subtitle_bbox[1]
        )

        if text_alignment == "center":
            subtitle_x = tx1 + (
                text_width
                - (
                    subtitle_bbox[2]
                    - subtitle_bbox[0]
                )
            ) / 2

        elif text_alignment == "right":
            subtitle_x = tx2 - (
                subtitle_bbox[2]
                - subtitle_bbox[0]
            )

        else:
            subtitle_x = tx1

        draw.multiline_text(
            (
                int(subtitle_x),
                int(current_y),
            ),
            subtitle_wrapped,
            font=subtitle_font,
            fill=colors["secondary"],
            spacing=7,
            align=text_alignment,
        )

        current_y += subtitle_height + 20

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    if body and current_y < ty2:
        body_height_limit = int(
            max(120, ty2 - current_y - 80)
        )

        body_wrapped, body_font = _fit_text(
            draw,
            body,
            max_width=text_width,
            max_height=body_height_limit,
            max_size=28,
            min_size=20,
            bold=False,
            spacing=9,
        )

        body_bbox = _text_bbox(
            draw,
            body_wrapped,
            body_font,
            spacing=9,
        )

        body_height = (
            body_bbox[3]
            - body_bbox[1]
        )

        if text_alignment == "center":
            body_x = tx1 + (
                text_width
                - (
                    body_bbox[2]
                    - body_bbox[0]
                )
            ) / 2

        elif text_alignment == "right":
            body_x = tx2 - (
                body_bbox[2]
                - body_bbox[0]
            )

        else:
            body_x = tx1

        draw.multiline_text(
            (
                int(body_x),
                int(current_y),
            ),
            body_wrapped,
            font=body_font,
            fill=colors["text"],
            spacing=9,
            align=text_alignment,
        )

        current_y += body_height + 22

    # --------------------------------------------------------
    # Takeaway
    # --------------------------------------------------------

    if takeaway and current_y < ty2:
        remaining_height = ty2 - current_y

        if remaining_height > 60:
            takeaway_box = (
                tx1,
                int(current_y),
                tx2,
                int(
                    min(
                        ty2,
                        current_y + 150,
                    )
                ),
            )

            _rounded_rectangle(
                draw,
                takeaway_box,
                radius=18,
                fill=(
                    colors["primary"][0],
                    colors["primary"][1],
                    colors["primary"][2],
                    35,
                ),
            )

            takeaway_text = _safe_text(
                takeaway
            )

            takeaway_wrapped, takeaway_font = _fit_text(
                draw,
                takeaway_text,
                max_width=max(
                    1,
                    text_width - 36,
                ),
                max_height=100,
                max_size=24,
                min_size=18,
                bold=True,
                spacing=6,
            )

            draw.multiline_text(
                (
                    tx1 + 18,
                    current_y + 16,
                ),
                takeaway_wrapped,
                font=takeaway_font,
                fill=colors["text"],
                spacing=6,
                align=text_alignment,
            )

    # --------------------------------------------------------
    # Subtle readability finish
    # --------------------------------------------------------

    if ai_image is not None and (
        "cinematic" in values["visual_style"].lower()
        or "editorial" in values["visual_style"].lower()
    ):
        add_soft_vignette(image)

    # --------------------------------------------------------
    # Convert to RGB
    # --------------------------------------------------------

    return image.convert("RGB")


# ============================================================
# AI VISUAL GENERATION
# ============================================================

def build_ai_visual_prompt(
    slide: dict,
    design: dict,
    planner_data: dict | None = None,
):
    """
    Builds an image-generation prompt.

    Important:
    This prompt must describe the visual only.
    It must NOT ask the image model to generate text.
    """

    planner_data = planner_data or {}

    values = get_design_values(design)

    topic = _safe_text(
        planner_data.get("topic")
    )

    niche = _safe_text(
        planner_data.get("niche")
        or planner_data.get("inferred_niche")
    )

    visual_subject = _safe_text(
        slide.get("visual_subject")
        or values["subject"]
    )

    visual_environment = _safe_text(
        slide.get("visual_environment")
        or values["environment"]
    )

    visual_style = _safe_text(
        slide.get("visual_style")
        or values["visual_style"]
    )

    composition = _safe_text(
        slide.get("composition")
        or values["background_composition"]
        or values["composition_type"]
    )

    lighting = _safe_text(
        slide.get("lighting")
        or values["lighting"]
    )

    image_position = _safe_text(
        slide.get("image_position")
        or values["image_position"]
    )

    text_safe_area = _safe_text(
        slide.get("text_safe_area")
        or values["text_safe_area"]
    )

    prompt_parts = [
        "Create a professional social-media visual.",
        "The image must look like a genuine professionally designed editorial/social-media photograph or illustration.",
        "Do not generate any text, letters, captions, logos, watermarks, UI, or typography inside the image.",
        "Avoid generic AI aesthetics such as glowing brains, random robots, floating holograms, excessive neon, blue digital gradients, or meaningless circuit patterns unless genuinely relevant to the subject.",
        "Use realistic materials, believable lighting, natural perspective, coherent objects, and contextually appropriate details.",
    ]

    if topic:
        prompt_parts.append(
            f"Topic context: {topic}."
        )

    if niche:
        prompt_parts.append(
            f"Field/context: {niche}."
        )

    if visual_subject:
        prompt_parts.append(
            f"Primary visual subject: {visual_subject}."
        )

    if visual_environment:
        prompt_parts.append(
            f"Environment: {visual_environment}."
        )

    if visual_style:
        prompt_parts.append(
            f"Visual style: {visual_style}."
        )

    if composition:
        prompt_parts.append(
            f"Composition: {composition}."
        )

    if lighting:
        prompt_parts.append(
            f"Lighting: {lighting}."
        )

    if image_position:
        prompt_parts.append(
            f"Image placement concept: {image_position}."
        )

    if text_safe_area:
        prompt_parts.append(
            f"Keep important visual details away from the intended text-safe area: {text_safe_area}."
        )

    prompt_parts.append(
        "High visual quality, clean composition, professional color treatment, realistic depth, sharp subject, balanced negative space."
    )

    return " ".join(prompt_parts)


# ============================================================
# SLIDE IMAGE GENERATION
# ============================================================

def generate_slide_visual(
    slide: dict,
    design: dict,
    planner_data: dict | None = None,
):
    prompt = build_ai_visual_prompt(
        slide=slide,
        design=design,
        planner_data=planner_data,
    )

    try:
        return generate_ai_visual(
            prompt=prompt,
        )
    except TypeError:
        # Supports older image_generator signatures.
        return generate_ai_visual(prompt)


# ============================================================
# FULL POST RENDER
# ============================================================
def render_social_post(
    design: dict | None = None,
    planner_data: dict | None = None,
    design_plan: dict | None = None,
):
    """
    Main public renderer.

    Supports both:
        design=
        design_plan=

    Returns JSON-safe image metadata.
    PIL Image objects are saved locally and are NOT returned
    inside the API response.
    """

    if design is None:
        design = design_plan

    if not isinstance(design, dict):
        raise ValueError(
            "Design data must be a dictionary."
        )

    planner_data = planner_data or {}

    slides = design.get("slides")

    if not isinstance(slides, list):
        slides = []

    # Single post must always have exactly one slide.
    post_format = _safe_text(
        design.get("format")
    ).lower()

    if (
        post_format in {
            "single",
            "single_post",
            "image",
        }
        and slides
    ):
        slides = slides[:1]

    if not slides:
        global_layout = design.get(
            "global_layout",
            {},
        )

        if not isinstance(global_layout, dict):
            global_layout = {}

        slides = [
            {
                "title": _safe_text(
                    planner_data.get("headline")
                ),
                "subtitle": _safe_text(
                    planner_data.get("subheadline")
                ),
                "body": _safe_text(
                    planner_data.get("introduction")
                ),
                "composition": _safe_text(
                    global_layout.get(
                        "composition_type",
                    )
                ),
                "image_position": _safe_text(
                    global_layout.get(
                        "image_position",
                    )
                ),
                "text_position": _safe_text(
                    global_layout.get(
                        "text_position",
                    )
                ),
                "text_safe_area": _safe_text(
                    global_layout.get(
                        "text_safe_area",
                    )
                ),
                "text_alignment": "left",
                "visual_subject": "",
                "visual_environment": "",
            }
        ]

    rendered_images = []

    # Unique folder for this generated post.
    post_id = uuid.uuid4().hex

    output_dir = os.path.join(
        "generated_posts",
        post_id,
    )

    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    total_slides = len(slides)

    for index, slide in enumerate(slides):

        if not isinstance(slide, dict):
            slide = {}

        ai_image = None

        # ----------------------------------------------------
        # Visual strategy routing
        # ----------------------------------------------------
        visual_strategy = design.get("visual_strategy", {})
        if not isinstance(visual_strategy, dict):
            visual_strategy = {}

        visual_type = _safe_text(
            slide.get("visual_type")
            or visual_strategy.get("type")
        ).lower()

        renderer = _safe_text(
            visual_strategy.get("renderer")
        ).lower()

        # Renderer is derived from the semantic visual type when
        # Design Agent did not explicitly provide one.
        if not renderer:
            if visual_type in {"photo", "illustration"}:
                renderer = "ai_image"
            elif visual_type == "graph":
                renderer = "chart"
            else:
                renderer = "structured"

        # Only these strategies are allowed to call the image model.
        should_generate_ai = renderer in {"ai_image", "hybrid"}

        print(
            f"[RENDER] slide={index + 1}/{total_slides} "
            f"visual_type={visual_type or 'unknown'} "
            f"renderer={renderer or 'unknown'} "
            f"ai_generation={'yes' if should_generate_ai else 'no'}"
        )

        if should_generate_ai:
            try:
                print(f"[RENDER] Generating AI visual for slide {index + 1}...")
                ai_image = generate_slide_visual(
                    slide=slide,
                    design=design,
                    planner_data=planner_data,
                )
                print(
                    f"[RENDER] AI visual generated for slide {index + 1}: "
                    f"{ai_image.size if hasattr(ai_image, 'size') else 'unknown'}"
                )
            except Exception as exc:
                # Do not crash the whole post because image generation failed.
                print(
                    f"[WARN] AI visual generation failed for slide {index + 1}: "
                    f"{type(exc).__name__}: {exc}"
                )
                ai_image = None

        rendered = render_slide(
            slide=slide,
            design=design,
            ai_image=ai_image,
            slide_index=index,
            total_slides=total_slides,
            planner_data=planner_data,
        )

        filename = f"slide_{index + 1}.png"

        output_path = os.path.join(
            output_dir,
            filename,
        )

        rendered.save(
            output_path,
            format="PNG",
            optimize=True,
        )

        rendered_images.append(
            {
                "slide_number": index + 1,
                "filename": filename,
                "path": output_path,
                "url": f"/generated-images/{post_id}/{filename}",
                "visual_type": visual_type or "unknown",
                "renderer": renderer or "structured",
            }
        )

    return {
        "status": "success",
        "post_id": post_id,
        "format": post_format or "single_post",
        "slide_count": len(rendered_images),
        "images": rendered_images,
    }
# ============================================================
# SAVE RENDERED SLIDES
# ============================================================

def save_rendered_slides(
    rendered_post: dict,
    output_dir: str,
    prefix: str = "post",
):
    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    saved_files = []

    slides = rendered_post.get(
        "slides",
        [],
    )

    for slide in slides:
        index = slide.get(
            "index",
            len(saved_files),
        )

        image = slide.get(
            "image"
        )

        if image is None:
            continue

        filename = (
            f"{prefix}_slide_{index + 1}.png"
        )

        path = os.path.join(
            output_dir,
            filename,
        )

        image.save(
            path,
            format="PNG",
            optimize=True,
        )

        saved_files.append(
            {
                "index": index,
                "path": path,
            }
        )

    return saved_files