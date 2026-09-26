import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

client = Groq(api_key=GROQ_API_KEY)


def clean_json_response(raw_text: str):
    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw_text,
            flags=re.IGNORECASE,
        )

        raw_text = re.sub(
            r"\s*```$",
            "",
            raw_text,
        )

    raw_text = raw_text.strip()

    if not raw_text.startswith("{"):
        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}")

        if json_start != -1 and json_end != -1:
            raw_text = raw_text[json_start:json_end + 1]

    return json.loads(raw_text)


def generate_ai_ideas(topic: str):
    prompt = f"""
You are an AI Content Ideas Generator inside an AI Social Media Manager.

The user entered this topic:

{topic}

Generate exactly 8 unique and practical social media content ideas
based specifically on this topic.

IMPORTANT:
- Every idea MUST be relevant to the user's topic.
- Do not give generic ideas unrelated to the topic.
- Each idea should be different from the others.
- Ideas should be useful for Instagram, Facebook, LinkedIn or X.
- Mix different content types such as educational, tips, mistakes,
  trends, facts, how-to, questions, comparisons, case-study style, etc.
- Do not invent fake statistics, studies, companies or news.
- Keep the language simple and engaging.
- Do not use markdown.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "ideas": [
        {{
            "title": "Short content idea title",
            "description": "Short explanation of what the post should cover",
            "tags": ["Educational", "Tips"]
        }}
    ]
}}

The ideas array MUST contain exactly 8 objects.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional social media content "
                    "idea generation agent. Generate topic-specific "
                    "and practical content ideas."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
    )

    raw_content = response.choices[0].message.content

    result = clean_json_response(raw_content)

    ideas = result.get("ideas", [])

    if not isinstance(ideas, list):
        return []

    cleaned_ideas = []

    for idea in ideas[:8]:
        if not isinstance(idea, dict):
            continue

        title = str(idea.get("title", "")).strip()
        description = str(
            idea.get("description", "")
        ).strip()

        tags = idea.get("tags", [])

        if not isinstance(tags, list):
            tags = []

        tags = [
            str(tag).strip()
            for tag in tags
            if str(tag).strip()
        ]

        if title and description:
            cleaned_ideas.append(
                {
                    "title": title,
                    "description": description,
                    "tags": tags[:3],
                }
            )

    return cleaned_ideas