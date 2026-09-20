import os
import uuid
import textwrap

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient


# =========================================================
# ENV
# =========================================================

load_dotenv(".env")

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    print("⚠️ HF_TOKEN missing. Fallback mode will be used.")


# =========================================================
# HUGGING FACE
# =========================================================

client = InferenceClient(
    token=HF_TOKEN
)

IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"


# =========================================================
# DIRECTORIES
# =========================================================

def get_output_directory():

    output_dir = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        "generated_images"
    )

    os.makedirs(output_dir, exist_ok=True)

    return output_dir


# =========================================================
# FONTS
# =========================================================

def get_font(size, bold=False):

    if bold:
        paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/calibrib.ttf"
        ]
    else:
        paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibri.ttf"
        ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# =========================================================
# NICHE THEMES
# =========================================================

NICHE_THEMES = {

    "technology": """
futuristic artificial intelligence environment,
digital interface, glowing data visualization,
modern technology, cyber-inspired atmosphere,
premium technology campaign
""",

    "artificial intelligence": """
advanced artificial intelligence environment,
AI neural network visualization,
digital brain, futuristic data systems,
premium technology aesthetic
""",

    "healthcare": """
modern healthcare environment,
medical technology, clean clinical atmosphere,
doctor and healthcare technology,
premium medical campaign
""",

    "education": """
modern education environment,
books, digital learning, classroom,
students learning, knowledge and technology,
premium educational campaign
""",

    "fashion": """
high-end fashion editorial,
elegant clothing, fashion magazine aesthetic,
studio lighting, premium luxury composition
""",

    "food": """
professional food photography,
beautifully plated food,
restaurant quality presentation,
appetizing premium food styling
""",

    "finance": """
modern fintech environment,
financial charts, business analytics,
data visualization, investment growth,
professional corporate atmosphere
""",

    "travel": """
beautiful travel destination,
cinematic landscape, tourism photography,
adventure and exploration,
premium travel campaign
""",

    "fitness": """
modern fitness environment,
athlete training, gym equipment,
healthy lifestyle, energetic sports photography
""",

    "beauty": """
premium beauty editorial,
elegant skincare environment,
cosmetics, sophisticated studio lighting,
luxury beauty campaign
""",

    "business": """
modern corporate environment,
business professionals, premium office,
leadership, strategy and growth,
corporate campaign photography
""",

    "environment": """
beautiful natural environment,
green energy, sustainability,
trees, clean planet, climate awareness,
environmental campaign
"""
}


def get_visual_theme(niche):

    niche_lower = niche.lower()

    # Exact / partial niche matching
    for key, theme in NICHE_THEMES.items():

        if key in niche_lower:
            return theme

    return """
modern professional commercial environment,
premium campaign photography,
clean composition,
visually attractive professional aesthetic
"""


# =========================================================
# AI VISUAL GENERATION
# =========================================================

def generate_ai_visual(
    niche: str = "",
    topic: str = "",
    style: str = "Professional",
    language: str = "English",
    prompt: str | None = None
):

    if not HF_TOKEN:
        raise Exception("HF_TOKEN missing from .env")

    # -----------------------------------------------------
    # IMPORTANT:
    # If Design Agent / Renderer already created a detailed
    # visual prompt, use that prompt directly.
    #
    # This keeps the system agentic.
    # The image generator should NOT overwrite the AI's
    # visual decision with its own hardcoded design.
    # -----------------------------------------------------

    if prompt and prompt.strip():

        final_prompt = prompt.strip()

    else:

        visual_theme = get_visual_theme(
            niche
        )

        final_prompt = f"""
Create a premium professional visual for a social media post.

Topic:
{topic}

Niche:
{niche}

Style:
{style}

Language:
{language}

Visual direction:
{visual_theme}

Requirements:

- Square 1:1 composition
- Professional commercial quality
- Modern social media campaign aesthetic
- Strong visual hierarchy
- Topic-specific visual concept
- Niche-specific visual elements
- Beautiful lighting
- Good depth
- Clean composition
- Premium look
- Suitable for Instagram, Facebook and LinkedIn
- Leave clear negative space for text overlay
- No watermark
- No logos
- No brand names
- No fake statistics
- No unnecessary text
- Do not create a poster full of text
- Focus mainly on the visual concept
- Avoid distorted people
- Avoid distorted hands
- Avoid visual clutter

The result should look like a professional designer created
the visual for a premium social media campaign.
"""

    print("🤖 Generating AI visual...")

    image = client.text_to_image(
        prompt=final_prompt,
        model=IMAGE_MODEL
    )

    if image is None:
        raise Exception("Hugging Face returned no image.")

    return image.convert("RGB")


# =========================================================
# COLOR THEME
# =========================================================

def get_colors(niche):

    niche = niche.lower()

    if "health" in niche:
        return "#0E766D", "#D8F3EF"

    if "education" in niche:
        return "#3159A5", "#DDE7FF"

    if "fashion" in niche:
        return "#8C526A", "#F6E4EA"

    if "food" in niche:
        return "#B85C27", "#FFE1CC"

    if "finance" in niche:
        return "#167A55", "#DDF5EA"

    if "travel" in niche:
        return "#187A9E", "#DDF4FB"

    if "fitness" in niche:
        return "#C94D2E", "#FFE0D8"

    if "beauty" in niche:
        return "#A95175", "#F8E1EC"

    if "business" in niche:
        return "#40566F", "#E1E8F0"

    if "environment" in niche:
        return "#287548", "#DDF2E3"

    if "technology" in niche or "artificial" in niche:
        return "#3154A5", "#DDE7FF"

    return "#3154A5", "#DDE7FF"


# =========================================================
# TEXT HELPERS
# =========================================================

def fit_text(
    draw,
    text,
    font,
    max_width
):

    words = text.split()

    lines = []
    current = ""

    for word in words:

        test = (
            current + " " + word
        ).strip()

        bbox = draw.textbbox(
            (0, 0),
            test,
            font=font
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test

        else:

            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


# =========================================================
# FINAL SOCIAL MEDIA POST DESIGN
# =========================================================

def compose_social_post(
    visual,
    niche,
    topic,
    style,
    language
):

    width = 1080
    height = 1080

    # Resize AI visual
    visual = visual.resize(
        (width, height)
    )

    # Dark overlay for readability
    overlay = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    overlay_draw = ImageDraw.Draw(
        overlay
    )

    # Gradient-like transparent overlays
    for y in range(height):

        alpha = int(
            190 * (1 - y / height)
        )

        overlay_draw.line(
            (0, y, width, y),
            fill=(0, 0, 0, alpha)
        )

    final_image = Image.alpha_composite(
        visual.convert("RGBA"),
        overlay
    ).convert("RGB")

    draw = ImageDraw.Draw(
        final_image
    )

    accent, light = get_colors(
        niche
    )

    # =====================================================
    # FONTS
    # =====================================================

    small_font = get_font(
        28,
        bold=True
    )

    title_font = get_font(
        68,
        bold=True
    )

    topic_font = get_font(
        34,
        bold=True
    )

    footer_font = get_font(
        23
    )

    # =====================================================
    # TOP BADGE
    # =====================================================

    draw.rounded_rectangle(
        (60, 55, 315, 120),
        radius=30,
        fill=accent
    )

    draw.text(
        (85, 73),
        "✦ AI SOCIAL",
        font=small_font,
        fill="white"
    )

    # =====================================================
    # NICHE LABEL
    # =====================================================

    draw.text(
        (65, 165),
        niche.upper(),
        font=topic_font,
        fill=light
    )

    # =====================================================
    # TOPIC HEADLINE
    # =====================================================

    headline = topic.strip()

    # Limit extremely long topics
    if len(headline) > 90:
        headline = headline[:87] + "..."

    lines = fit_text(
        draw,
        headline,
        title_font,
        900
    )

    y = 230

    for line in lines[:4]:

        draw.text(
            (65, y),
            line,
            font=title_font,
            fill="white",
            stroke_width=1,
            stroke_fill="#000000"
        )

        y += 82

    # =====================================================
    # STYLE BADGE
    # =====================================================

    badge_y = min(
        max(y + 35, 620),
        800
    )

    draw.rounded_rectangle(
        (65, badge_y, 310, badge_y + 55),
        radius=25,
        fill=accent
    )

    draw.text(
        (85, badge_y + 13),
        style.upper(),
        font=small_font,
        fill="white"
    )

    # =====================================================
    # DECORATIVE LINE
    # =====================================================

    draw.line(
        (65, 900, 1015, 900),
        fill=light,
        width=2
    )

    # =====================================================
    # FOOTER
    # =====================================================

    draw.text(
        (65, 935),
        "AI Social Media Manager",
        font=footer_font,
        fill="white"
    )

    draw.text(
        (760, 935),
        "CREATE • SHARE • GROW",
        font=footer_font,
        fill=light
    )

    return final_image


# =========================================================
# PROFESSIONAL FALLBACK
# =========================================================

def generate_fallback_post(
    niche,
    topic,
    style,
    language
):

    print(
        "🎨 Creating professional fallback post..."
    )

    width = 1080
    height = 1080

    accent, light = get_colors(
        niche
    )

    image = Image.new(
        "RGB",
        (width, height),
        "#08111F"
    )

    draw = ImageDraw.Draw(
        image
    )

    # Background shapes
    draw.ellipse(
        (650, -180, 1220, 390),
        fill="#182B50"
    )

    draw.ellipse(
        (-250, 760, 300, 1300),
        fill="#132642"
    )

    draw.rounded_rectangle(
        (35, 35, 1045, 1045),
        radius=35,
        outline=accent,
        width=3
    )

    small_font = get_font(
        27,
        bold=True
    )

    title_font = get_font(
        68,
        bold=True
    )

    topic_font = get_font(
        32,
        bold=True
    )

    footer_font = get_font(
        23
    )

    # Badge
    draw.rounded_rectangle(
        (65, 65, 320, 130),
        radius=30,
        fill=accent
    )

    draw.text(
        (90, 83),
        "✦ AI SOCIAL",
        font=small_font,
        fill="white"
    )

    # Niche
    draw.text(
        (65, 180),
        niche.upper(),
        font=topic_font,
        fill=light
    )

    # Topic
    headline = topic.strip()

    if len(headline) > 90:
        headline = headline[:87] + "..."

    lines = fit_text(
        draw,
        headline,
        title_font,
        900
    )

    y = 260

    for line in lines[:4]:

        draw.text(
            (65, y),
            line,
            font=title_font,
            fill="white"
        )

        y += 82

    # Style
    style_y = min(
        max(y + 50, 650),
        820
    )

    draw.rounded_rectangle(
        (65, style_y, 330, style_y + 60),
        radius=28,
        fill=accent
    )

    draw.text(
        (90, style_y + 15),
        style.upper(),
        font=small_font,
        fill="white"
    )

    # Footer line
    draw.line(
        (65, 900, 1015, 900),
        fill=accent,
        width=2
    )

    draw.text(
        (65, 940),
        "AI Social Media Manager",
        font=footer_font,
        fill="white"
    )

    return image


# =========================================================
# SAVE IMAGE
# =========================================================

def save_image(
    image,
    prefix="ai_post"
):

    output_dir = get_output_directory()

    file_name = (
        f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
    )

    file_path = os.path.join(
        output_dir,
        file_name
    )

    image.save(
        file_path,
        "JPEG",
        quality=95
    )

    return file_name, file_path


# =========================================================
# MAIN FUNCTION
# =========================================================

def generate_post_image(
    niche: str,
    topic: str,
    style: str = "Professional",
    language: str = "English"
):

    print(
        "🎨 Starting professional social media post generation..."
    )

    # =====================================================
    # AI MODE
    # =====================================================

    try:

        visual = generate_ai_visual(
            niche=niche,
            topic=topic,
            style=style,
            language=language
        )

        final_post = compose_social_post(
            visual=visual,
            niche=niche,
            topic=topic,
            style=style,
            language=language
        )

        file_name, file_path = save_image(
            final_post,
            prefix="ai_social_post"
        )

        print(
            f"✅ Final AI social post created: {file_path}"
        )

        return {
            "status": "success",
            "provider": "huggingface",
            "model": IMAGE_MODEL,
            "is_ai_generated": True,
            "design_type": "social_media_post",
            "file_name": file_name,
            "file_path": file_path
        }

    # =====================================================
    # FALLBACK MODE
    # =====================================================

    except Exception as error:

        print(
            f"⚠️ AI image generation failed: {error}"
        )

        print(
            "🔄 Using professional fallback..."
        )

        fallback = generate_fallback_post(
            niche=niche,
            topic=topic,
            style=style,
            language=language
        )

        file_name, file_path = save_image(
            fallback,
            prefix="fallback_social_post"
        )

        return {
            "status": "success",
            "provider": "pillow",
            "is_ai_generated": False,
            "design_type": "social_media_post",
            "file_name": file_name,
            "file_path": file_path,
            "ai_error": str(error)
        }