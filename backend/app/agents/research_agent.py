import json
import re
import os
import requests

from typing import Any, Dict, List, Optional

from app.services.content_generator import client


# ---------------------------------------------------------
# JSON CLEANER
# ---------------------------------------------------------

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Safely extract and parse JSON from an AI response.

    Handles:
    - markdown code fences
    - extra text before/after JSON
    - trailing commas
    - common smart quotes
    """

    text = (raw_text or "").strip()

    if not text:
        raise ValueError("AI returned an empty response")

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    # First attempt: response itself is valid JSON
    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # Find JSON object inside extra text
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI returned no JSON object")

    json_text = text[start:end + 1]

    # Second attempt: normal JSON
    try:
        result = json.loads(json_text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # Third attempt: remove trailing commas
    cleaned = re.sub(
        r",\s*([}\]])",
        r"\1",
        json_text,
    )

    try:
        result = json.loads(cleaned)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # Fourth attempt: repair smart quotes
    repaired = (
        cleaned
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )

    try:
        result = json.loads(repaired)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"AI returned invalid JSON: {exc}"
        ) from exc


# ---------------------------------------------------------
# ARTICLE META EXTRACTION
# ---------------------------------------------------------

def extract_meta_content(
    html: str,
    property_name: str = "",
    name: str = "",
) -> str:
    """
    Extract content from common HTML meta tags.

    Kept for compatibility with the existing research agent.
    """

    if not html:
        return ""

    patterns = []

    if property_name:
        patterns.extend([
            rf'<meta[^>]+property=["\']{re.escape(property_name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(property_name)}["\']',
        ])

    if name:
        patterns.extend([
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(name)}["\']',
        ])

    for pattern in patterns:
        match = re.search(
            pattern,
            html,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    return ""


# ---------------------------------------------------------
# GNEWS API
# ---------------------------------------------------------

def research_tech_news(
    topic: str = "Artificial Intelligence",
    category: str = "ai",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Fetch latest real news from GNews API.

    Categories:
    - ai
    - technology
    - business
    - trending
    - all

    Returns:
    - title
    - description
    - link
    - published
    - source
    - image
    """

    if not topic or not topic.strip():
        raise ValueError("Topic is required")

    limit = max(1, min(limit, 10))

    # -----------------------------------------------------
    # GET API KEY
    # -----------------------------------------------------

    api_key = os.getenv("GNEWS_API_KEY")

    if not api_key:
        raise ValueError(
            "GNEWS_API_KEY is not configured in the backend environment."
        )

    # -----------------------------------------------------
    # GNEWS SEARCH ENDPOINT
    # -----------------------------------------------------

    url = "https://gnews.io/api/v4/search"

    # -----------------------------------------------------
    # CATEGORY SEARCH QUERY
    # -----------------------------------------------------

    category = (category or "ai").lower().strip()

    if category == "business":

        search_topic = (
            "business OR startup OR economy OR finance OR market"
        )

    elif category == "technology":

        search_topic = (
            "technology OR software OR gadgets OR cybersecurity"
        )

    elif category == "trending":

        search_topic = "India"

    elif category == "all":

        search_topic = (
            "technology OR business OR "
            "artificial intelligence OR startup"
        )

    else:

        search_topic = topic.strip()

    # -----------------------------------------------------
    # REQUEST PARAMETERS
    # -----------------------------------------------------

    params = {
        "q": search_topic,
        "lang": "en",
        "country": "in",
        "max": limit,
        "sortby": "publishedAt",
    }

    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json",
    }

    # -----------------------------------------------------
    # REQUEST
    # -----------------------------------------------------

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()
    print("TRENDING GNEWS RESPONSE:", response.text)

    data = response.json()

    # -----------------------------------------------------
    # EXTRACT ARTICLES
    # -----------------------------------------------------

    articles = []

    for article in data.get("articles", []):

        source = article.get("source") or {}

        title = str(
            article.get("title") or ""
        ).strip()

        description = str(
            article.get("description") or ""
        ).strip()

        link = str(
            article.get("url") or ""
        ).strip()

        published = str(
            article.get("publishedAt") or ""
        ).strip()

        source_name = str(
            source.get("name") or "Unknown Source"
        ).strip()

        image = str(
            article.get("image") or ""
        ).strip()

        # -------------------------------------------------
        # DESCRIPTION CLEANUP
        # -------------------------------------------------

        description = re.sub(
            r"\s+",
            " ",
            description,
        ).strip()

        if len(description) > 300:

            description = (
                description[:297].rstrip()
                + "..."
            )

        # -------------------------------------------------
        # FINAL ARTICLE
        # -------------------------------------------------

        articles.append({
            "title": title,
            "link": link,
            "published": published,
            "source": source_name,
            "description": description,
            "image": image,
        })

    return articles


# ---------------------------------------------------------
# RESEARCH DECISION
# ---------------------------------------------------------

def should_research(
    topic: str,
    description: str = "",
    planner_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Decide whether external research is required.

    Planner decision is respected first.
    """

    planner_data = planner_data or {}

    if planner_data.get(
        "requires_research"
    ) is True:

        return True

    text = (
        f"{topic} {description}"
    ).lower()

    research_signals = [
        "latest",
        "recent",
        "current",
        "today",
        "this week",
        "this month",
        "news",
        "breaking",
        "update",
        "updates",
        "2026",
        "new launch",
        "new release",
        "recently announced",
        "trending",
    ]

    return any(
        signal in text
        for signal in research_signals
    )


# ---------------------------------------------------------
# RESEARCH PLANNING + SOURCE EXTRACTION
# ---------------------------------------------------------

def research_topic(
    topic: str,
    description: str = "",
    planner_data: Optional[Dict[str, Any]] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Main Research Agent.

    Flow:

    Topic
      ↓
    Planner decision
      ↓
    Research required?
      ↓
    GNews API
      ↓
    AI summarizes available research
      ↓
    Structured research result
    """

    if not topic or not topic.strip():

        raise ValueError(
            "Topic is required"
        )

    planner_data = (
        planner_data or {}
    )

    research_required = should_research(
        topic=topic,
        description=description,
        planner_data=planner_data,
    )

    # -----------------------------------------------------
    # NO RESEARCH REQUIRED
    # -----------------------------------------------------

    if not research_required:

        return {
            "research_required": False,
            "research_reason": (
                "This topic does not require "
                "current external research."
            ),
            "search_queries": [],
            "summary": "",
            "facts": [],
            "sources": [],
            "warnings": [],
        }

    # -----------------------------------------------------
    # BUILD SEARCH QUERY
    # -----------------------------------------------------

    planner_queries = planner_data.get(
        "research_queries",
        [],
    )

    if (
        isinstance(planner_queries, list)
        and planner_queries
    ):

        search_query = str(
            planner_queries[0]
        ).strip()

    else:

        search_query = topic.strip()

    # -----------------------------------------------------
    # FETCH NEWS
    # -----------------------------------------------------

    try:

        articles = research_tech_news(
            topic=search_query,
            category="ai",
            limit=limit,
        )

    except Exception as exc:

        return {
            "research_required": True,
            "research_reason": (
                "External research was required, "
                "but the news source could not "
                "be reached."
            ),
            "search_queries": [
                search_query
            ],
            "summary": "",
            "facts": [],
            "sources": [],
            "warnings": [
                f"Research request failed: {str(exc)}"
            ],
        }

    # -----------------------------------------------------
    # NO RESULTS
    # -----------------------------------------------------

    if not articles:

        return {
            "research_required": True,
            "research_reason": (
                "External research was required, "
                "but no relevant articles were found."
            ),
            "search_queries": [
                search_query
            ],
            "summary": "",
            "facts": [],
            "sources": [],
            "warnings": [
                "No relevant news articles were found."
            ],
        }

    # -----------------------------------------------------
    # PREPARE ARTICLE DATA FOR AI
    # -----------------------------------------------------

    article_context = []

    for index, article in enumerate(
        articles,
        start=1,
    ):

        article_context.append({
            "article_number": index,
            "title": article.get(
                "title",
                "",
            ),
            "source": article.get(
                "source",
                "",
            ),
            "published": article.get(
                "published",
                "",
            ),
            "url": article.get(
                "link",
                "",
            ),
            "description": article.get(
                "description",
                "",
            ),
            "image": article.get(
                "image",
                "",
            ),
        })

    # -----------------------------------------------------
    # AI RESEARCH ANALYSIS
    # -----------------------------------------------------

    prompt = f"""
You are the Research Agent of an autonomous AI Social Media Manager.

Analyze the retrieved news articles for the user's topic.

USER TOPIC:

{topic}

USER DESCRIPTION:

{description}

PLANNER DATA:

{json.dumps(planner_data, ensure_ascii=False)}

RETRIEVED ARTICLES:

{json.dumps(article_context, ensure_ascii=False)}

IMPORTANT RULES:

1. Use ONLY information supported by the retrieved article metadata.
2. Do NOT invent facts.
3. Do NOT invent statistics.
4. Do NOT invent quotes.
5. Do NOT invent dates.
6. Do NOT invent URLs.
7. Do NOT claim an article says something that is not supported by
   the available information.
8. If the available article information is insufficient to verify a
   claim, do not include that claim as a verified fact.
9. Preserve the original source URL exactly.
10. Prefer reputable and relevant sources when several articles
    cover the same topic.
11. The research result will be passed to another AI agent that
    creates the social-media content.
12. Clearly mention uncertainty when the available information is
    insufficient.

Return ONLY valid JSON.

IMPORTANT OUTPUT RULES:

- Return plain JSON only.
- Do not use Markdown.
- Do not use code fences.
- Do not wrap URLs in Markdown.
- Every URL must be a plain string.
- Use double quotes for all JSON keys and strings.
- Do not add comments outside JSON.
- Do not invent facts.
- Only use information available in the provided article metadata.
- Do not leave any JSON string or object unfinished.
- Do not use trailing commas.
- Make sure every opening brace, bracket, and quote is properly closed.

Required structure:

{{
    "summary": "",
    "facts": [
        {{
            "claim": "",
            "source_url": "",
            "confidence": "high"
        }}
    ],
    "sources": [
        {{
            "title": "",
            "url": "",
            "publisher": "",
            "published_date": "",
            "relevance": ""
        }}
    ],
    "warnings": []
}}
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful research analyst. "
                        "Never fabricate facts or sources. "
                        "Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_tokens=3000,
        )

        raw_text = (
            response
            .choices[0]
            .message
            .content
            or ""
        )

        ai_result = clean_json_response(
            raw_text
        )

    except Exception as exc:

        return {
            "research_required": True,
            "research_reason": (
                "Articles were retrieved, but AI "
                "research analysis failed."
            ),
            "search_queries": [
                search_query
            ],
            "summary": "",
            "facts": [],
            "sources": article_context,
            "warnings": [
                f"AI research analysis failed: {str(exc)}"
            ],
        }

    # -----------------------------------------------------
    # NORMALIZE AI RESULT
    # -----------------------------------------------------

    facts = ai_result.get(
        "facts",
        [],
    )

    if not isinstance(
        facts,
        list,
    ):
        facts = []

    sources = ai_result.get(
        "sources",
        [],
    )

    if not isinstance(
        sources,
        list,
    ):
        sources = []

    warnings = ai_result.get(
        "warnings",
        [],
    )

    if not isinstance(
        warnings,
        list,
    ):
        warnings = []

    # -----------------------------------------------------
    # SAFETY:
    # KEEP ONLY REAL RETRIEVED URLs
    # -----------------------------------------------------

    retrieved_urls = {
        article["link"]
        for article in articles
        if article.get("link")
    }

    verified_facts = []

    for fact in facts:

        if not isinstance(
            fact,
            dict,
        ):
            continue

        source_url = str(
            fact.get(
                "source_url",
                "",
            )
        ).strip()

        claim = str(
            fact.get(
                "claim",
                "",
            )
        ).strip()

        if not claim:
            continue

        if (
            source_url
            and source_url in retrieved_urls
        ):

            verified_facts.append({
                "claim": claim,
                "source_url": source_url,
                "confidence": str(
                    fact.get(
                        "confidence",
                        "medium",
                    )
                ).strip(),
            })

    # -----------------------------------------------------
    # NORMALIZE SOURCES
    # -----------------------------------------------------

    normalized_sources = []

    for source in sources:

        if not isinstance(
            source,
            dict,
        ):
            continue

        url = str(
            source.get(
                "url",
                "",
            )
        ).strip()

        if (
            not url
            or url not in retrieved_urls
        ):
            continue

        normalized_sources.append({
            "title": str(
                source.get(
                    "title",
                    "",
                )
            ).strip(),

            "url": url,

            "publisher": str(
                source.get(
                    "publisher",
                    "",
                )
            ).strip(),

            "published_date": str(
                source.get(
                    "published_date",
                    "",
                )
            ).strip(),

            "relevance": str(
                source.get(
                    "relevance",
                    "",
                )
            ).strip(),
        })

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "research_required": True,

        "research_reason": (
            "Current external information was "
            "required for this topic."
        ),

        "search_queries": [
            search_query
        ],

        "summary": str(
            ai_result.get(
                "summary",
                "",
            )
        ).strip(),

        "facts": verified_facts,

        "sources": normalized_sources,

        "warnings": warnings,
    }