# =========================================================
# FACT CHECK AGENT - FINAL STABLE VERSION
# =========================================================
#
# Purpose:
#
# Generated Post
#      ↓
# Extract ONLY factual claims
#      ↓
# Search multiple sources
#      ↓
# Remove irrelevant sources
#      ↓
# Check source quality
#      ↓
# Check source independence
#      ↓
# Evidence scoring
#      ↓
# Gemini only for ambiguous factual claims
#      ↓
# VERIFIED / REVIEW_REQUIRED / NOT_VERIFIED
#
# Important:
# - Questions are NOT factual claims.
# - CTAs are NOT factual claims.
# - Advice/instructions are NOT factual claims.
# - Generic marketing language is NOT factual claims.
# - Motivational/promotional language is NOT factual claims.
# - Actual factual/news/statistical claims ARE checked.
# - Gemini is NOT mandatory for every claim.
# =========================================================

import os
import re
import json
import requests
import xml.etree.ElementTree as ET

from google import genai
from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# =========================================================
# TRUSTED SOURCE LIST
# =========================================================

HIGH_QUALITY_SOURCES = {
    # News organizations
    "reuters",
    "associated press",
    "bbc",
    "the guardian",
    "new york times",
    "the washington post",
    "bloomberg",
    "cnbc",
    "the verge",
    "techcrunch",
    "wired",
    "wall street journal",
    "nature",
    "axios",
    "fortune",

    # Technology companies / official sources
    "openai",
    "google",
    "microsoft",
    "meta",
    "apple",
    "nvidia",
    "anthropic",

    # Research / security organizations
    "metr",
    "ai security institute",
    "aisi",
}


MEDIUM_QUALITY_SOURCES = {
    "forbes",
    "business insider",
    "times of india",
    "the indian express",
    "hindustan times",
    "india today",
    "ndtv",
    "economic times",
    "mint",
    "news18",
    "cnn",
    "abc news",
    "cbs news",
    "al jazeera",
    "the hacker news",
    "et telecom",
}


# =========================================================
# SOURCE NORMALIZATION
# =========================================================

def normalize_source_name(source_name: str):
    """
    Normalize source names so aliases are treated as one source.
    """

    if not source_name:
        return ""

    source = source_name.lower().strip()

    source = re.sub(
        r"\s+",
        " ",
        source
    )

    aliases = {
        "wsj": "wall street journal",
        "the wsj": "wall street journal",
        "ap": "associated press",
        "ap news": "associated press",
        "guardian": "the guardian",
        "the guardian": "the guardian",
    }

    return aliases.get(
        source,
        source
    )


# =========================================================
# SOURCE QUALITY
# =========================================================

def get_source_quality(source_name: str):

    source = normalize_source_name(
        source_name
    )

    if source in HIGH_QUALITY_SOURCES:
        return {
            "level": "high",
            "score": 0.90,
            "reason": (
                "Recognized authoritative or established source."
            )
        }

    if source in MEDIUM_QUALITY_SOURCES:
        return {
            "level": "medium",
            "score": 0.70,
            "reason": (
                "Recognized media or specialist source."
            )
        }

    return {
        "level": "low",
        "score": 0.40,
        "reason": (
            "Source is not in the trusted-source list."
        )
    }


# =========================================================
# HTML CLEANER
# =========================================================

def clean_html(text: str):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"&nbsp;",
        " ",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# STOP WORDS
# =========================================================

STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "that",
    "this",
    "these",
    "those",
    "as",
    "at",
    "it",
    "its",
    "be",
    "been",
    "being",
    "into",
    "about",
    "after",
    "before",
    "during",
    "recent",
    "report",
    "reports",
    "researchers",
    "your",
    "you",
    "us",
    "we",
    "our",
    "they",
    "them",
    "their",
}


# =========================================================
# TEXT TOKENS
# =========================================================

def get_keywords(text: str):

    if not text:
        return set()

    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower()
    )

    return {
        word
        for word in words
        if len(word) >= 3
        and word not in STOP_WORDS
    }


# =========================================================
# RELEVANCE CHECK
# =========================================================

def calculate_relevance(
    claim: str,
    title: str,
    description: str
):
    """
    Calculate relevance between claim and source metadata.
    """

    claim_words = get_keywords(
        claim
    )

    evidence_words = get_keywords(
        f"{title or ''} {description or ''}"
    )

    if not claim_words:
        return 0.0

    common_words = (
        claim_words &
        evidence_words
    )

    score = len(common_words) / len(
        claim_words
    )

    return round(
        min(score, 1.0),
        2
    )


# =========================================================
# NEWS SEARCH
# =========================================================

def search_news_sources(
    claim: str,
    limit: int = 12
):

    url = (
        "https://news.google.com/rss/search?"
        f"q={requests.utils.quote(claim)}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    response = requests.get(
        url,
        timeout=10,
        headers={
            "User-Agent":
            "AI-Social-Media-Manager/1.0"
        }
    )

    response.raise_for_status()

    root = ET.fromstring(
        response.content
    )

    sources = []

    for item in root.findall(".//item")[:limit]:

        title = item.findtext(
            "title"
        )

        link = item.findtext(
            "link"
        )

        published = item.findtext(
            "pubDate"
        )

        source = item.findtext(
            "source"
        )

        description = item.findtext(
            "description"
        )

        description = clean_html(
            description
        )

        quality = get_source_quality(
            source
        )

        relevance = calculate_relevance(
            claim=claim,
            title=title,
            description=description
        )

        sources.append({

            "title": title,

            "link": link,

            "published": published,

            "source": source,

            "description": description,

            "source_quality":
                quality["level"],

            "source_quality_score":
                quality["score"],

            "source_quality_reason":
                quality["reason"],

            "normalized_source":
                normalize_source_name(
                    source
                ),

            "relevance_score":
                relevance,

            "relevant_to_claim":
                relevance >= 0.20
        })

    return sources


# =========================================================
# FACTUAL CLAIM DETECTION
# =========================================================

QUESTION_START_WORDS = {
    "what",
    "how",
    "why",
    "when",
    "where",
    "who",
    "which",
    "whose",
    "whom",
    "should",
    "could",
    "would",
    "can",
    "may",
    "might",
    "will",
    "do",
    "does",
    "did",
    "is",
    "are",
    "was",
    "were",
}


# =========================================================
# NON-FACTUAL / PROMOTIONAL SIGNALS
# =========================================================

CTA_PATTERNS = [
    r"\bfollow us\b",
    r"\bfollow for\b",
    r"\bsubscribe\b",
    r"\blearn more\b",
    r"\bclick here\b",
    r"\bvisit us\b",
    r"\bcontact us\b",
    r"\bget started\b",
    r"\bstart today\b",
    r"\bstart now\b",
    r"\btry it today\b",
    r"\btry this today\b",
    r"\bshare this\b",
    r"\bsave this\b",
    r"\bswipe\b",
    r"\bswipe through\b",
    r"\bcheck out\b",
    r"\bdiscover\b",
]


ADVICE_PATTERNS = [
    r"^\s*use\b",
    r"^\s*try\b",
    r"^\s*consider\b",
    r"^\s*focus on\b",
    r"^\s*start\b",
    r"^\s*build\b",
    r"^\s*create\b",
    r"^\s*optimize\b",
    r"^\s*leverage\b",
    r"^\s*identify\b",
    r"^\s*monitor\b",
    r"^\s*track\b",
    r"^\s*set up\b",
    r"^\s*invest in\b",
    r"^\s*make sure\b",
    r"^\s*remember\b",
]


MARKETING_PATTERNS = [
    r"\bboost your\b",
    r"\bgrow your\b",
    r"\bgrow your business\b",
    r"\bboost traffic\b",
    r"\bincrease your\b",
    r"\bimprove your\b",
    r"\blevel up\b",
    r"\blevel up your\b",
    r"\blevel up\b",
    r"\bdrive more\b",
    r"\battract more\b",
    r"\bengage more\b",
    r"\bconvert more\b",
    r"\bactionable\b",
    r"\bpowerful\b",
    r"\beffective\b",
    r"\bsimple\b",
    r"\bultimate\b",
    r"\bwinning\b",
    r"\bgame-changing\b",
    r"\bgame changing\b",
    r"\bproven strategies\b",
    r"\bproven tactic\b",
    r"\bproven tactics\b",
    r"\bsuccessful digital marketing\b",
    r"\bbackbone of\b",
    r"\bready to implement\b",
    r"\bready to use\b",
]


GENERIC_COPY_PATTERNS = [
    r"\bready to\b",
    r"\blet'?s\b",
    r"\bhere'?s how\b",
    r"\bthese tips\b",
    r"\bthese strategies\b",
    r"\bthese tactics\b",
    r"\bthese steps\b",
    r"\bthese methods\b",
    r"\bthese ideas\b",
    r"\bquick tips\b",
    r"\bmarketing tips\b",
    r"\bfor more tips\b",
]


FACTUAL_VERB_PATTERNS = [
    r"\bannounced\b",
    r"\breleased\b",
    r"\blaunched\b",
    r"\bunveiled\b",
    r"\bintroduced\b",
    r"\bpublished\b",
    r"\bapproved\b",
    r"\bbanned\b",
    r"\bacquired\b",
    r"\bmerged\b",
    r"\bsigned\b",
    r"\bappointed\b",
    r"\breported\b",
    r"\bconfirmed\b",
    r"\bdisclosed\b",
    r"\bmeasured\b",
    r"\bfound\b",
    r"\bdetected\b",
    r"\brecorded\b",
    r"\bincreased\b",
    r"\bdecreased\b",
    r"\brose\b",
    r"\bfell\b",
    r"\bgained\b",
    r"\blost\b",
]


STATISTICAL_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*%",
    r"\b\d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)\b",
    r"\b\d+(?:\.\d+)?\s*(?:kg|km|m|cm|mm|gb|tb|mb)\b",
    r"\b\d+(?:\.\d+)?\s*(?:years?|months?|days?|hours?|minutes?)\b",
    r"\b\d{4}\b",
    r"\b\d+(?:\.\d+)?x\b",
    r"\b\d+(?:\.\d+)?\s*(?:times|percent)\b",
]


def is_question_or_non_factual(
    sentence: str
):
    """
    Determine whether a sentence is clearly
    non-factual promotional/copywriting text.
    """

    text = sentence.strip()

    if not text:
        return True

    lower = text.lower()

    # -----------------------------------------------------
    # Questions
    # -----------------------------------------------------

    if "?" in text:
        return True

    words = lower.split()

    if not words:
        return True

    first_word = re.sub(
        r"[^a-z]",
        "",
        words[0]
    )

    if first_word in QUESTION_START_WORDS:
        return True

    # -----------------------------------------------------
    # Hashtag-only
    # -----------------------------------------------------

    if text.startswith("#"):
        return True

    # -----------------------------------------------------
    # CTA language
    # -----------------------------------------------------

    for pattern in CTA_PATTERNS:
        if re.search(
            pattern,
            lower,
            flags=re.IGNORECASE
        ):
            return True

    # -----------------------------------------------------
    # Generic marketing/copywriting
    # -----------------------------------------------------

    for pattern in MARKETING_PATTERNS:
        if re.search(
            pattern,
            lower,
            flags=re.IGNORECASE
        ):
            return True

    for pattern in GENERIC_COPY_PATTERNS:
        if re.search(
            pattern,
            lower,
            flags=re.IGNORECASE
        ):
            return True

    # -----------------------------------------------------
    # Imperative/advice sentence
    # -----------------------------------------------------

    for pattern in ADVICE_PATTERNS:
        if re.search(
            pattern,
            lower,
            flags=re.IGNORECASE
        ):
            return True

    # -----------------------------------------------------
    # Short promotional phrases
    # -----------------------------------------------------

    if len(words) <= 12:
        promotional_words = {
            "tips",
            "strategy",
            "strategies",
            "tactics",
            "growth",
            "success",
            "business",
            "marketing",
            "follow",
            "start",
            "today",
        }

        overlap = sum(
            1
            for word in words
            if re.sub(r"[^a-z]", "", word)
            in promotional_words
        )

        if overlap >= 2:
            return True

    return False


def contains_strong_factual_signal(
    sentence: str
):
    """
    Detect strong signals that a sentence is
    actually making a factual assertion.
    """

    lower = sentence.lower()

    # -----------------------------------------------------
    # Dates / numbers / statistics
    # -----------------------------------------------------

    for pattern in STATISTICAL_PATTERNS:
        if re.search(
            pattern,
            lower,
            flags=re.IGNORECASE
        ):
            return True

    # -----------------------------------------------------
    # Explicit factual verbs
    # -----------------------------------------------------

    for pattern in FACTUAL_VERB_PATTERNS:
        if re.search(
            pattern,
            lower,
            flags=re.IGNORECASE
        ):
            return True

    return False


# =========================================================
# CLAIM EXTRACTION
# =========================================================

def extract_claims(text: str):

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    claims = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if len(sentence) < 25:
            continue

        # -------------------------------------------------
        # Skip obvious non-factual content
        # -------------------------------------------------

        if is_question_or_non_factual(
            sentence
        ):
            continue

        # -------------------------------------------------
        # Strong factual claim
        # -------------------------------------------------

        if contains_strong_factual_signal(
            sentence
        ):
            claims.append(
                sentence
            )
            continue

        # -------------------------------------------------
        # Conservative rule:
        #
        # Long declarative statements can be factual,
        # but generic marketing sentences should not.
        # -------------------------------------------------

        lower = sentence.lower()

        generic_marketing_score = 0

        for pattern in MARKETING_PATTERNS:
            if re.search(
                pattern,
                lower,
                flags=re.IGNORECASE
            ):
                generic_marketing_score += 1

        for pattern in GENERIC_COPY_PATTERNS:
            if re.search(
                pattern,
                lower,
                flags=re.IGNORECASE
            ):
                generic_marketing_score += 1

        if generic_marketing_score > 0:
            continue

        # -------------------------------------------------
        # Very long declarative statements:
        #
        # Only treat as factual if they contain stronger
        # factual structure such as named entities,
        # measurable terms, or explicit factual wording.
        # -------------------------------------------------

        factual_structure_patterns = [
            r"\baccording to\b",
            r"\bresearch shows\b",
            r"\bstudy found\b",
            r"\bresearch found\b",
            r"\bdata shows\b",
            r"\bdata indicate\b",
            r"\bexperts say\b",
            r"\breport says\b",
            r"\breport found\b",
            r"\bgovernment\b",
            r"\bcompany\b",
            r"\borganization\b",
            r"\bofficials\b",
            r"\bscientists\b",
            r"\bresearchers\b",
            r"\bstudy\b",
            r"\breport\b",
        ]

        if any(
            re.search(
                pattern,
                lower,
                flags=re.IGNORECASE
            )
            for pattern in factual_structure_patterns
        ):
            claims.append(
                sentence
            )
            continue

        # -------------------------------------------------
        # Do NOT automatically treat every long sentence
        # as factual.
        #
        # This prevents ordinary social-media copy such as:
        #
        # "These strategies help businesses..."
        #
        # from triggering expensive source searches.
        # -------------------------------------------------

    # -----------------------------------------------------
    # Remove duplicates cleanly
    # -----------------------------------------------------

    unique_claims = []

    seen = set()

    for claim in claims:

        normalized = re.sub(
            r"\s+",
            " ",
            claim.lower().strip()
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        unique_claims.append(
            claim
        )

    return unique_claims


# =========================================================
# FILTER RELEVANT SOURCES
# =========================================================

def get_relevant_sources(
    claim: str,
    sources: list
):

    relevant = []

    for source in sources:

        if not source.get(
            "relevant_to_claim",
            False
        ):
            continue

        if not source.get(
            "title"
        ):
            continue

        if not source.get(
            "source"
        ):
            continue

        relevant.append(
            source
        )

    relevant.sort(
        key=lambda item: (
            item.get(
                "source_quality_score",
                0
            ),
            item.get(
                "relevance_score",
                0
            )
        ),
        reverse=True
    )

    return relevant


# =========================================================
# INDEPENDENT SOURCE COUNT
# =========================================================

def count_independent_sources(
    sources: list
):

    source_names = set()

    for source in sources:

        normalized = normalize_source_name(
            source.get("source")
        )

        if normalized:
            source_names.add(
                normalized
            )

    return len(
        source_names
    )


# =========================================================
# DETERMINISTIC EVIDENCE ANALYSIS
# =========================================================

def deterministic_evidence_check(
    claim: str,
    relevant_sources: list
):

    high_sources = [
        source
        for source in relevant_sources
        if source.get(
            "source_quality"
        ) == "high"
    ]

    medium_sources = [
        source
        for source in relevant_sources
        if source.get(
            "source_quality"
        ) == "medium"
    ]

    low_sources = [
        source
        for source in relevant_sources
        if source.get(
            "source_quality"
        ) == "low"
    ]

    high_count = len(
        {
            normalize_source_name(
                source.get("source")
            )
            for source in high_sources
            if source.get("source")
        }
    )

    medium_count = len(
        {
            normalize_source_name(
                source.get("source")
            )
            for source in medium_sources
            if source.get("source")
        }
    )

    low_count = len(
        {
            normalize_source_name(
                source.get("source")
            )
            for source in low_sources
            if source.get("source")
        }
    )

    # -----------------------------------------------------
    # 2+ independent high-quality
    # -----------------------------------------------------

    if high_count >= 2:

        return {
            "decision": "SUPPORTED",
            "confidence": 0.90,
            "reason": (
                "The claim is supported by "
                "multiple independent high-quality sources."
            ),
            "supporting_sources": [
                source.get("source")
                for source in high_sources[:3]
            ],
            "needs_ai": False
        }

    # -----------------------------------------------------
    # 1 high + 1 medium
    # -----------------------------------------------------

    if high_count >= 1 and medium_count >= 1:

        return {
            "decision": "SUPPORTED",
            "confidence": 0.82,
            "reason": (
                "The claim is supported by "
                "independent sources including "
                "at least one high-quality source."
            ),
            "supporting_sources": [
                source.get("source")
                for source in (
                    high_sources[:2]
                    + medium_sources[:2]
                )
            ],
            "needs_ai": False
        }

    # -----------------------------------------------------
    # Single high
    # -----------------------------------------------------

    if high_count == 1:

        return {
            "decision": "REVIEW_REQUIRED",
            "confidence": 0.65,
            "reason": (
                "A high-quality source supports "
                "the claim, but independent "
                "corroboration is limited."
            ),
            "supporting_sources": [
                source.get("source")
                for source in high_sources
            ],
            "needs_ai": True
        }

    # -----------------------------------------------------
    # Multiple medium
    # -----------------------------------------------------

    if medium_count >= 2:

        return {
            "decision": "REVIEW_REQUIRED",
            "confidence": 0.60,
            "reason": (
                "Multiple established sources "
                "mention the claim, but stronger "
                "authoritative evidence is preferred."
            ),
            "supporting_sources": [
                source.get("source")
                for source in medium_sources[:3]
            ],
            "needs_ai": True
        }

    # -----------------------------------------------------
    # Only low-quality
    # -----------------------------------------------------

    if low_count > 0:

        return {
            "decision": "REVIEW_REQUIRED",
            "confidence": 0.40,
            "reason": (
                "Only weak or unrecognized sources "
                "were found."
            ),
            "supporting_sources": [],
            "needs_ai": True
        }

    # -----------------------------------------------------
    # Nothing
    # -----------------------------------------------------

    return {
        "decision": "UNCERTAIN",
        "confidence": 0.0,
        "reason": (
            "No sufficiently relevant evidence "
            "was found."
        ),
        "supporting_sources": [],
        "needs_ai": True
    }


# =========================================================
# OPTIONAL GEMINI EVIDENCE ANALYSIS
# =========================================================

def compare_claim_with_sources(
    claim: str,
    sources: list
):

    if not sources:

        return {
            "decision": "UNCERTAIN",
            "confidence": 0.0,
            "reason": (
                "No evidence sources were found."
            ),
            "supporting_sources": [],
            "contradicting_sources": []
        }

    if client is None:

        return {
            "decision": "UNCERTAIN",
            "confidence": 0.0,
            "reason": (
                "Gemini is unavailable. "
                "Human review is required."
            ),
            "supporting_sources": [],
            "contradicting_sources": []
        }

    evidence = []

    for index, source in enumerate(
        sources,
        start=1
    ):

        evidence.append({

            "source_number": index,

            "source":
                source.get("source"),

            "title":
                source.get("title"),

            "description":
                source.get("description"),

            "quality":
                source.get("source_quality"),

            "relevance":
                source.get("relevance_score")
        })

    prompt = f"""
You are a strict fact-checking AI.

Compare ONLY the factual claim with the supplied evidence.

CLAIM:
{claim}

EVIDENCE:
{json.dumps(evidence, indent=2)}

Rules:
- Do not invent facts.
- Do not treat advice as facts.
- Do not treat CTAs as facts.
- Do not treat marketing slogans as facts.
- A title/snippet is weaker than detailed evidence.
- Prefer independent authoritative sources.
- If evidence is insufficient return UNCERTAIN.
- If evidence conflicts return CONTRADICTED.

Return ONLY JSON:

{{
    "decision": "SUPPORTED",
    "confidence": 0.85,
    "reason": "Short explanation.",
    "supporting_sources": [1],
    "contradicting_sources": []
}}

Allowed decisions:
SUPPORTED
CONTRADICTED
UNCERTAIN
"""

    try:

        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        raw = interaction.output_text.strip()

        if raw.startswith("```"):

            raw = re.sub(
                r"^```(?:json)?\s*",
                "",
                raw,
                flags=re.IGNORECASE
            )

            raw = re.sub(
                r"\s*```$",
                "",
                raw
            )

        raw = raw.strip()

        if not raw.startswith("{"):

            start = raw.find("{")
            end = raw.rfind("}")

            if start != -1 and end != -1:
                raw = raw[
                    start:end + 1
                ]

        result = json.loads(
            raw
        )

        decision = result.get(
            "decision",
            "UNCERTAIN"
        )

        if decision not in {
            "SUPPORTED",
            "CONTRADICTED",
            "UNCERTAIN"
        }:
            decision = "UNCERTAIN"

        try:
            confidence = float(
                result.get(
                    "confidence",
                    0
                )
            )
        except Exception:
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        return {
            "decision": decision,
            "confidence": round(
                confidence,
                2
            ),
            "reason": result.get(
                "reason",
                "AI evidence analysis completed."
            ),
            "supporting_sources": result.get(
                "supporting_sources",
                []
            ),
            "contradicting_sources": result.get(
                "contradicting_sources",
                []
            )
        }

    except Exception as error:

        return {
            "decision": "UNCERTAIN",
            "confidence": 0.0,
            "reason": (
                "AI evidence analysis unavailable. "
                "Human review is required."
            ),
            "supporting_sources": [],
            "contradicting_sources": [],
            "error": str(error)
        }


# =========================================================
# VERIFY ONE CLAIM
# =========================================================

def verify_claim(
    claim: str,
    minimum_sources: int = 2
):

    try:

        sources = search_news_sources(
            claim=claim,
            limit=12
        )

    except Exception as error:

        return {
            "claim": claim,
            "decision": "review_required",
            "verified": False,
            "confidence": 0.0,
            "sources_found": 0,
            "relevant_sources": 0,
            "independent_sources": 0,
            "high_quality_sources": 0,
            "medium_quality_sources": 0,
            "low_quality_sources": 0,
            "sources": [],
            "evidence_analysis": None,
            "reason": "Source search failed.",
            "error": str(error)
        }

    relevant_sources = get_relevant_sources(
        claim=claim,
        sources=sources
    )

    independent_count = (
        count_independent_sources(
            relevant_sources
        )
    )

    high_count = sum(
        1
        for source in relevant_sources
        if source.get(
            "source_quality"
        ) == "high"
    )

    medium_count = sum(
        1
        for source in relevant_sources
        if source.get(
            "source_quality"
        ) == "medium"
    )

    low_count = sum(
        1
        for source in relevant_sources
        if source.get(
            "source_quality"
        ) == "low"
    )

    # -----------------------------------------------------
    # No relevant sources
    # -----------------------------------------------------

    if not relevant_sources:

        return {
            "claim": claim,
            "decision": "not_verified",
            "verified": False,
            "confidence": 0.05,
            "sources_found": len(
                sources
            ),
            "relevant_sources": 0,
            "independent_sources": 0,
            "high_quality_sources": 0,
            "medium_quality_sources": 0,
            "low_quality_sources": 0,
            "sources": sources,
            "evidence_analysis": {
                "decision": "UNCERTAIN",
                "confidence": 0.05,
                "reason": (
                    "No sufficiently relevant "
                    "evidence was found."
                ),
                "supporting_sources": [],
                "contradicting_sources": []
            },
            "reason": (
                "No sufficiently relevant "
                "evidence was found."
            )
        }

    # -----------------------------------------------------
    # Deterministic check
    # -----------------------------------------------------

    deterministic_result = (
        deterministic_evidence_check(
            claim=claim,
            relevant_sources=relevant_sources
        )
    )

    # -----------------------------------------------------
    # Strong evidence
    # -----------------------------------------------------

    if (
        deterministic_result["decision"]
        == "SUPPORTED"
    ):

        return {
            "claim": claim,
            "decision": "verified",
            "verified": True,
            "confidence": deterministic_result[
                "confidence"
            ],
            "sources_found": len(
                sources
            ),
            "relevant_sources": len(
                relevant_sources
            ),
            "independent_sources":
                independent_count,
            "high_quality_sources":
                high_count,
            "medium_quality_sources":
                medium_count,
            "low_quality_sources":
                low_count,
            "sources": relevant_sources,
            "evidence_analysis":
                deterministic_result,
            "reason": (
                "The claim is supported by "
                "multiple relevant independent "
                "high-quality sources."
            )
        }

    # -----------------------------------------------------
    # Ambiguous factual claim
    # -----------------------------------------------------

    ai_result = compare_claim_with_sources(
        claim=claim,
        sources=relevant_sources[:6]
    )

    ai_decision = ai_result.get(
        "decision",
        "UNCERTAIN"
    )

    ai_confidence = ai_result.get(
        "confidence",
        0.0
    )

    # -----------------------------------------------------
    # AI supported + enough independent evidence
    # -----------------------------------------------------

    if (
        ai_decision == "SUPPORTED"
        and independent_count >= minimum_sources
        and (
            high_count >= 1
            or medium_count >= 2
        )
    ):

        return {
            "claim": claim,
            "decision": "verified",
            "verified": True,
            "confidence": round(
                max(
                    ai_confidence,
                    0.75
                ),
                2
            ),
            "sources_found": len(
                sources
            ),
            "relevant_sources": len(
                relevant_sources
            ),
            "independent_sources":
                independent_count,
            "high_quality_sources":
                high_count,
            "medium_quality_sources":
                medium_count,
            "low_quality_sources":
                low_count,
            "sources": relevant_sources,
            "evidence_analysis":
                ai_result,
            "reason": (
                "The claim is supported by "
                "multiple relevant independent sources."
            )
        }

    # -----------------------------------------------------
    # Contradicted
    # -----------------------------------------------------

    if ai_decision == "CONTRADICTED":

        return {
            "claim": claim,
            "decision": "review_required",
            "verified": False,
            "confidence": round(
                max(
                    ai_confidence,
                    0.70
                ),
                2
            ),
            "sources_found": len(
                sources
            ),
            "relevant_sources": len(
                relevant_sources
            ),
            "independent_sources":
                independent_count,
            "high_quality_sources":
                high_count,
            "medium_quality_sources":
                medium_count,
            "low_quality_sources":
                low_count,
            "sources": relevant_sources,
            "evidence_analysis":
                ai_result,
            "reason": (
                "Evidence conflicts with the claim. "
                "Human review is required."
            )
        }

    # -----------------------------------------------------
    # Final review
    # -----------------------------------------------------

    return {
        "claim": claim,
        "decision": "review_required",
        "verified": False,
        "confidence": round(
            min(
                ai_confidence,
                0.65
            ),
            2
        ),
        "sources_found": len(
            sources
        ),
        "relevant_sources": len(
            relevant_sources
        ),
        "independent_sources":
            independent_count,
        "high_quality_sources":
            high_count,
        "medium_quality_sources":
            medium_count,
        "low_quality_sources":
            low_count,
        "sources": relevant_sources,
        "evidence_analysis":
            ai_result,
        "reason": (
            "Evidence was found, but it is "
            "not strong enough for automatic verification."
        )
    }


# =========================================================
# FACT CHECK COMPLETE POST
# =========================================================

def fact_check_post(
    caption: str,
    news_title: str = None,
    news_source: str = None
):

    # -----------------------------------------------------
    # Extract ONLY actual factual claims
    # -----------------------------------------------------

    claims = extract_claims(
        caption
    )

    # -----------------------------------------------------
    # News headline is explicitly factual/research-based
    # -----------------------------------------------------

    if news_title:
        news_title = news_title.strip()

        if news_title:
            claims.insert(
                0,
                news_title
            )

    # -----------------------------------------------------
    # Clean duplicates
    # -----------------------------------------------------

    unique_claims = []

    seen = set()

    for claim in claims:

        normalized = re.sub(
            r"\s+",
            " ",
            claim.lower().strip()
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        unique_claims.append(
            claim
        )

    claims = unique_claims

    # -----------------------------------------------------
    # No factual claims
    # -----------------------------------------------------

    if not claims:

        return {
            "decision": "not_applicable",
            "verified": True,
            "confidence": 1.0,
            "claims_checked": 0,
            "verified_claims": 0,
            "review_required_claims": 0,
            "not_verified_claims": 0,
            "contradicted_claims": 0,
            "claims": [],
            "news_source_provided":
                news_source,
            "reason": (
                "No factual claims were found. "
                "Fact checking was not required."
            )
        }

    # -----------------------------------------------------
    # Maximum 5 factual claims
    # -----------------------------------------------------

    results = []

    for claim in claims[:5]:

        result = verify_claim(
            claim=claim,
            minimum_sources=2
        )

        results.append(
            result
        )

    # -----------------------------------------------------
    # Counters
    # -----------------------------------------------------

    verified_count = sum(
        1
        for result in results
        if result.get(
            "decision"
        ) == "verified"
    )

    review_count = sum(
        1
        for result in results
        if result.get(
            "decision"
        ) == "review_required"
    )

    not_verified_count = sum(
        1
        for result in results
        if result.get(
            "decision"
        ) == "not_verified"
    )

    contradicted_count = sum(
        1
        for result in results
        if (
            result.get(
                "evidence_analysis"
            )
            and result.get(
                "evidence_analysis"
            ).get(
                "decision"
            ) == "CONTRADICTED"
        )
    )

    average_confidence = (
        sum(
            result.get(
                "confidence",
                0
            )
            for result in results
        )
        / len(results)
    )

    # -----------------------------------------------------
    # Overall decision
    # -----------------------------------------------------

    if contradicted_count > 0:

        overall_decision = (
            "review_required"
        )

        overall_reason = (
            "At least one factual claim "
            "was contradicted by evidence."
        )

    elif review_count > 0:

        overall_decision = (
            "review_required"
        )

        overall_reason = (
            "At least one factual claim "
            "requires human review."
        )

    elif not_verified_count > 0:

        overall_decision = (
            "not_verified"
        )

        overall_reason = (
            "One or more factual claims "
            "could not be sufficiently verified."
        )

    elif verified_count == len(results):

        overall_decision = "verified"

        overall_reason = (
            "All factual claims were "
            "successfully verified."
        )

    else:

        overall_decision = (
            "review_required"
        )

        overall_reason = (
            "The post requires additional review."
        )

    return {

        "decision":
            overall_decision,

        "verified":
            overall_decision == "verified",

        "confidence":
            round(
                average_confidence,
                2
            ),

        "claims_checked":
            len(results),

        "verified_claims":
            verified_count,

        "review_required_claims":
            review_count,

        "not_verified_claims":
            not_verified_count,

        "contradicted_claims":
            contradicted_count,

        "claims":
            results,

        "news_source_provided":
            news_source,

        "reason":
            overall_reason
    }

# =========================================================
# STRICT EVIDENCE PATCH - PRESERVES ORIGINAL IMPLEMENTATION
# =========================================================
# This patch intentionally overrides only the evidence-sensitive functions.
# All original functions and structure above remain preserved.

# Official publishers must be recognized by publisher/domain, not by the
# Google News wrapper URL.
HIGH_QUALITY_SOURCES.update({
    "google blog",
    "google ai",
    "google deepmind",
    "deepmind",
    "google research",
    "google cloud",
    "microsoft research",
})


def normalize_source_name(source_name: str):
    if not source_name:
        return ""
    source = str(source_name).lower().strip()
    source = re.sub(r"\s+", " ", source)
    aliases = {
        "wsj": "wall street journal",
        "the wsj": "wall street journal",
        "ap": "associated press",
        "ap news": "associated press",
        "guardian": "the guardian",
        "the guardian": "the guardian",
        "blog.google": "google blog",
        "google": "google",
        "google blog": "google blog",
        "google ai": "google ai",
        "google deepmind": "google deepmind",
        "deepmind": "google deepmind",
        "deepmind google": "google deepmind",
        "google research": "google research",
        "google cloud": "google cloud",
        "microsoft research": "microsoft research",
    }
    return aliases.get(source, source)


def get_source_quality(source_name: str, link: str = ""):
    """Classify the real publisher; a Google News wrapper is not the publisher."""
    source = normalize_source_name(source_name)
    url = str(link or "").lower()
    # Google News is only the delivery wrapper; never treat it as Google evidence.
    is_google_news_wrapper = "news.google.com" in url

    official_domains = (
        "blog.google", "google.com", "developers.google.com",
        "cloud.google.com", "support.google.com", "deepmind.google",
        "research.google", "openai.com", "microsoft.com",
        "research.microsoft.com", "anthropic.com", "nvidia.com",
        "apple.com", "meta.com", "ai.meta.com",
    )
    if not is_google_news_wrapper and any(domain in url for domain in official_domains):
        if "google" in url:
            source = "google blog" if "blog.google" in url else "google"
        elif "openai.com" in url:
            source = "openai"
        elif "microsoft" in url:
            source = "microsoft research" if "research" in url else "microsoft"
        elif "anthropic" in url:
            source = "anthropic"
        elif "nvidia" in url:
            source = "nvidia"
        elif "apple" in url:
            source = "apple"
        elif "meta" in url:
            source = "meta"

    if source in HIGH_QUALITY_SOURCES:
        official = {
            "google", "google blog", "google ai", "google deepmind",
            "google research", "google cloud", "openai", "microsoft",
            "microsoft research", "anthropic"
        }
        return {
            "level": "high",
            "score": 0.95 if source in official else 0.90,
            "reason": "Recognized authoritative, official, research, or established news source."
        }
    if source in MEDIUM_QUALITY_SOURCES:
        return {
            "level": "medium",
            "score": 0.70,
            "reason": "Recognized media or specialist source."
        }
    return {
        "level": "low",
        "score": 0.40,
        "reason": "Source is not in the trusted-source list."
    }


def extract_numeric_facts(text: str):
    if not text:
        return set()
    patterns = [
        r"\b\d+(?:\.\d+)?\s*%",
        r"\b\d+(?:\.\d+)?\s*x\b",
        r"\b\d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)\b",
        r"\b\d+(?:\.\d+)?\s*(?:kg|km|m|cm|mm|gb|tb|mb)\b",
        r"\b\d+(?:\.\d+)?\s*(?:years?|months?|days?|hours?|minutes?)\b",
        r"\b\d{4}\b",
        r"\b\d+(?:\.\d+)?\s*times\b",
    ]
    values = set()
    for pattern in patterns:
        for match in re.findall(pattern, str(text).lower(), flags=re.IGNORECASE):
            values.add(re.sub(r"\s+", " ", match.strip()))
    return values


def _named_terms(text: str):
    terms = set()
    for match in re.findall(
        r"\b(?:[A-Z][A-Za-z0-9.-]*)(?:\s+[A-Z][A-Za-z0-9.-]*)*\b",
        str(text or "")
    ):
        normalized = re.sub(r"[^a-z0-9]+", " ", match.lower()).strip()
        if len(normalized) >= 3:
            terms.add(normalized)
    return terms


def calculate_evidence_support(claim: str, title: str, description: str):
    """Exact-support score. This is deliberately stricter than relevance."""
    evidence_text = f"{title or ''} {description or ''}"
    claim_words = get_keywords(claim)
    evidence_words = get_keywords(evidence_text)
    if not claim_words:
        return {
            "score": 0.0, "keyword_overlap": 0.0,
            "numeric_match": True, "factual_signal": False,
            "entity_match": False, "action_match": False,
            "exact_support": False,
        }

    common = claim_words & evidence_words
    keyword_overlap = len(common) / len(claim_words)

    claim_numbers = extract_numeric_facts(claim)
    evidence_numbers = extract_numeric_facts(evidence_text)
    numeric_match = not claim_numbers or claim_numbers.issubset(evidence_numbers)

    factual_actions = {
        "announced", "released", "launched", "unveiled", "introduced",
        "published", "approved", "banned", "acquired", "merged", "signed",
        "appointed", "reported", "confirmed", "disclosed", "measured", "found",
        "detected", "recorded", "increased", "decreased", "rose", "fell",
        "gained", "lost", "occurred", "happened", "opened", "closed",
        "discovered", "denied", "won", "died",
    }
    claim_actions = claim_words & factual_actions
    evidence_actions = evidence_words & factual_actions
    action_match = bool(claim_actions & evidence_actions) if claim_actions else True

    claim_entities = _named_terms(claim)
    evidence_entities = _named_terms(evidence_text)
    entity_match = bool(claim_entities & evidence_entities) if claim_entities else True

    score = keyword_overlap
    if claim_actions and action_match:
        score += 0.15
    if claim_entities and entity_match:
        score += 0.15
    if claim_numbers and numeric_match:
        score += 0.15
    if claim_numbers and not numeric_match:
        score = min(score, 0.35)
    score = round(min(score, 1.0), 2)

    exact_support = (
        score >= 0.72
        and numeric_match
        and action_match
        and entity_match
    )
    return {
        "score": score,
        "keyword_overlap": round(keyword_overlap, 2),
        "numeric_match": numeric_match,
        "factual_signal": bool(claim_actions),
        "entity_match": entity_match,
        "action_match": action_match,
        "exact_support": exact_support,
    }


# More conservative factual extraction. A headline such as "7 proven strategies"
# is promotional; a sentence with a factual event/date is not.
CTA_PATTERNS += [
    r"\bstart implementing\b",
    r"\btry these\b",
    r"\buse these\b",
    r"\bexplore\b",
    r"\blink in bio\b",
]
ADVICE_PATTERNS += [
    r"^\s*avoid\b", r"^\s*choose\b", r"^\s*enable\b",
    r"^\s*post\b", r"^\s*follow\b", r"^\s*keep\b",
]
MARKETING_PATTERNS += [
    r"\bdrive results\b", r"\bhelp you\b", r"\btake your .* to\b",
    r"\bwatch your .* grow\b", r"\bunlock\b", r"\btransform\b",
    r"\bproven\b", r"\bgame-changing\b", r"\bgame changing\b",
]


def contains_strong_factual_signal(sentence: str):
    lower = sentence.lower()
    factual_verbs = (
        r"announced|released|launched|unveiled|introduced|published|approved|banned|"
        r"acquired|merged|signed|appointed|reported|confirmed|disclosed|measured|found|"
        r"detected|recorded|increased|decreased|rose|fell|gained|lost|occurred|happened|"
        r"opened|closed|discovered|denied|won|died"
    )
    if re.search(r"\b(?:" + factual_verbs + r")\b", lower):
        return True
    if re.search(r"\b(?:study|research|report|survey|data|according to|researchers|scientists)\b", lower):
        return True
    # Numbers/dates are factual only when the sentence has factual/statistical context.
    if re.search(r"\b\d+(?:\.\d+)?\s*(?:%|million|billion|trillion|thousand|times|years?|months?|days?|hours?)\b", lower):
        return bool(re.search(r"\b(?:study|research|report|survey|data|rate|revenue|users|population|number of|according to)\b", lower))
    return False


def extract_claims(text: str):
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    claims = []
    for sentence in sentences:
        sentence = re.sub(r"^[•\-–—\s]+", "", sentence.strip())
        sentence = re.sub(r"#[A-Za-z0-9_]+", "", sentence).strip()
        if not sentence or len(sentence) < 25:
            continue
        if is_question_or_non_factual(sentence):
            continue
        lower = sentence.lower()
        if any(re.search(pattern, lower, re.IGNORECASE)
               for pattern in MARKETING_PATTERNS + GENERIC_COPY_PATTERNS + CTA_PATTERNS + ADVICE_PATTERNS):
            continue
        if contains_strong_factual_signal(sentence):
            claims.append(sentence)
            continue
        structures = [
            r"\baccording to\b", r"\bresearch shows\b", r"\bstudy found\b",
            r"\bresearch found\b", r"\bdata shows\b", r"\bdata indicate\b",
            r"\bexperts say\b", r"\breport says\b", r"\breport found\b",
            r"\bgovernment\b", r"\bcompany\b", r"\borganization\b",
            r"\bofficials\b", r"\bscientists\b", r"\bresearchers\b",
            r"\bstudy\b", r"\breport\b",
        ]
        if any(re.search(pattern, lower, re.IGNORECASE) for pattern in structures):
            claims.append(sentence)

    unique = []
    seen = set()
    for claim in claims:
        normalized = re.sub(r"\s+", " ", claim.lower().strip())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(claim)
    return unique


def search_news_sources(claim: str, limit: int = 12):
    """Original search flow, enhanced with exact-support metadata."""
    url = (
        "https://news.google.com/rss/search?"
        f"q={requests.utils.quote(claim)}"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    )
    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "AI-Social-Media-Manager/1.0"}
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    sources = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title")
        link = item.findtext("link")
        published = item.findtext("pubDate")
        source = item.findtext("source")
        description = clean_html(item.findtext("description"))
        quality = get_source_quality(source, link)
        relevance = calculate_relevance(claim, title, description)
        evidence = calculate_evidence_support(claim, title, description)
        sources.append({
            "title": title, "link": link, "published": published, "source": source,
            "description": description, "source_quality": quality["level"],
            "source_quality_score": quality["score"], "source_quality_reason": quality["reason"],
            "normalized_source": normalize_source_name(source),
            "relevance_score": relevance, "relevant_to_claim": relevance >= 0.35,
            "evidence_support_score": evidence["score"],
            "keyword_overlap": evidence["keyword_overlap"],
            "numeric_match": evidence["numeric_match"],
            "factual_signal": evidence["factual_signal"],
            "entity_match": evidence["entity_match"],
            "action_match": evidence["action_match"],
            "supports_claim": evidence["exact_support"],
        })
    return sources


def get_relevant_sources(claim: str, sources: list):
    relevant = [
        source for source in sources
        if source.get("relevant_to_claim", False)
        and source.get("title")
        and source.get("source")
    ]
    relevant.sort(
        key=lambda item: (
            item.get("evidence_support_score", 0),
            item.get("source_quality_score", 0),
            item.get("relevance_score", 0),
        ),
        reverse=True,
    )
    return relevant


def get_supported_sources(sources: list):
    return [source for source in sources if source.get("supports_claim", False)]


def count_independent_sources(sources: list):
    return len({
        normalize_source_name(source.get("source"))
        for source in sources
        if normalize_source_name(source.get("source"))
    })


def deterministic_evidence_check(claim: str, relevant_sources: list):
    """Only exact-support sources enter the verification count."""
    supported = get_supported_sources(relevant_sources)
    groups = {"high": [], "medium": [], "low": []}
    for source in supported:
        groups.setdefault(source.get("source_quality", "low"), []).append(source)

    names = lambda values: {
        normalize_source_name(x.get("source"))
        for x in values if x.get("source")
    }
    high_names = names(groups["high"])
    medium_names = names(groups["medium"])
    low_names = names(groups["low"])
    independent = len(high_names | medium_names | low_names)

    if high_names:
        return {
            "decision": "SUPPORTED", "confidence": 0.90,
            "reason": "At least one authoritative source provides strong exact semantic support for the claim.",
            "supporting_sources": [x.get("source") for x in groups["high"][:3]],
            "supporting_source_count": independent, "needs_ai": False,
        }
    if len(medium_names) >= 2:
        return {
            "decision": "SUPPORTED", "confidence": 0.82,
            "reason": "The exact claim is supported by at least two independent medium-quality sources.",
            "supporting_sources": [x.get("source") for x in groups["medium"][:3]],
            "supporting_source_count": independent, "needs_ai": False,
        }
    if medium_names:
        return {
            "decision": "REVIEW_REQUIRED", "confidence": 0.60,
            "reason": "One medium-quality source provides strong support, but corroboration is limited.",
            "supporting_sources": [groups["medium"][0].get("source")],
            "supporting_source_count": independent, "needs_ai": True,
        }
    if low_names:
        return {
            "decision": "REVIEW_REQUIRED", "confidence": 0.35,
            "reason": "Only low-quality evidence supports the claim; low-quality sources cannot independently verify it.",
            "supporting_sources": [], "supporting_source_count": independent, "needs_ai": True,
        }
    return {
        "decision": "UNCERTAIN", "confidence": 0.15 if relevant_sources else 0.0,
        "reason": "Relevant sources were found, but none provides sufficiently strong exact evidence.",
        "supporting_sources": [], "supporting_source_count": 0, "needs_ai": True,
    }


def compare_claim_with_sources(claim: str, sources: list):
    """Gemini is a tie-breaker only; it cannot manufacture evidence."""
    if not sources or client is None:
        return {
            "decision": "UNCERTAIN", "confidence": 0.0,
            "reason": "Gemini unavailable or no evidence. Human review is required.",
            "supporting_sources": [], "contradicting_sources": [],
        }

    evidence = []
    for index, source in enumerate(sources, start=1):
        evidence.append({
            "source_number": index, "source": source.get("source"),
            "title": source.get("title"), "description": source.get("description"),
            "quality": source.get("source_quality"), "relevance": source.get("relevance_score"),
            "evidence_support": source.get("evidence_support_score"),
            "numeric_match": source.get("numeric_match"),
            "supports_claim": source.get("supports_claim"),
        })

    prompt = f"""
You are a STRICT fact-checking AI.
Determine whether the EXACT factual claim is supported by the supplied evidence.

CLAIM:
{claim}

EVIDENCE:
{json.dumps(evidence, indent=2)}

Rules:
1. Relevance and shared keywords are NOT proof.
2. The evidence must support the exact subject, event, action and object.
3. Exact dates, years, numbers, versions, quantities and names must be explicitly supported.
4. Never infer missing facts from general knowledge.
5. Low-quality sources can provide context but cannot be the sole basis for SUPPORTED.
6. Prefer official and authoritative sources.
7. If evidence is incomplete or ambiguous, return UNCERTAIN.
8. If evidence directly conflicts with the claim, return CONTRADICTED.
9. Never invent source numbers.

Return ONLY JSON:
{{
  "decision": "SUPPORTED",
  "confidence": 0.85,
  "reason": "Short explanation.",
  "supporting_sources": [1],
  "contradicting_sources": []
}}
"""
    try:
        interaction = client.interactions.create(model="gemini-3.6-flash", input=prompt)
        raw = interaction.output_text.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
        if not raw.startswith("{"):
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                raw = raw[start:end + 1]
        result = json.loads(raw)
        decision = result.get("decision", "UNCERTAIN")
        if decision not in {"SUPPORTED", "CONTRADICTED", "UNCERTAIN"}:
            decision = "UNCERTAIN"
        try:
            confidence = float(result.get("confidence", 0))
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        # Gemini may only cite sources that our deterministic layer marked as
        # exact-supporting and medium/high quality.
        valid_indices = {
            index for index, source in enumerate(sources, start=1)
            if source.get("supports_claim")
            and source.get("source_quality") in {"high", "medium"}
        }
        supporting = [
            index for index in result.get("supporting_sources", [])
            if isinstance(index, int) and index in valid_indices
        ]
        if decision == "SUPPORTED" and not supporting:
            decision = "UNCERTAIN"
            confidence = min(confidence, 0.50)

        return {
            "decision": decision, "confidence": round(confidence, 2),
            "reason": result.get("reason", "AI evidence analysis completed."),
            "supporting_sources": supporting,
            "contradicting_sources": result.get("contradicting_sources", []),
        }
    except Exception as error:
        return {
            "decision": "UNCERTAIN", "confidence": 0.0,
            "reason": "AI evidence analysis unavailable. Human review is required.",
            "supporting_sources": [], "contradicting_sources": [], "error": str(error),
        }


def verify_claim(claim: str, minimum_sources: int = 2):
    try:
        sources = search_news_sources(claim=claim, limit=12)
    except Exception as error:
        return {
            "claim": claim, "decision": "review_required", "verified": False,
            "confidence": 0.0, "sources_found": 0, "relevant_sources": 0,
            "supporting_sources": 0, "independent_sources": 0,
            "high_quality_sources": 0, "medium_quality_sources": 0,
            "low_quality_sources": 0, "sources": [], "evidence_analysis": None,
            "reason": "Source search failed.", "error": str(error),
        }

    relevant = get_relevant_sources(claim=claim, sources=sources)
    supported = get_supported_sources(relevant)
    independent = count_independent_sources(relevant)
    supporting = count_independent_sources(supported)
    high = len({normalize_source_name(x.get("source")) for x in supported if x.get("source_quality") == "high"})
    medium = len({normalize_source_name(x.get("source")) for x in supported if x.get("source_quality") == "medium"})
    low = len({normalize_source_name(x.get("source")) for x in supported if x.get("source_quality") == "low"})

    if not relevant:
        return {
            "claim": claim, "decision": "not_verified", "verified": False,
            "confidence": 0.05, "sources_found": len(sources), "relevant_sources": 0,
            "supporting_sources": 0, "independent_sources": 0,
            "high_quality_sources": 0, "medium_quality_sources": 0,
            "low_quality_sources": 0, "sources": sources,
            "evidence_analysis": {
                "decision": "UNCERTAIN", "confidence": 0.05,
                "reason": "No sufficiently relevant evidence was found.",
                "supporting_sources": [], "contradicting_sources": [],
            },
            "reason": "No sufficiently relevant evidence was found.",
        }

    deterministic = deterministic_evidence_check(claim, relevant)
    if deterministic["decision"] == "SUPPORTED":
        return {
            "claim": claim, "decision": "verified", "verified": True,
            "confidence": deterministic["confidence"], "sources_found": len(sources),
            "relevant_sources": len(relevant), "supporting_sources": supporting,
            "independent_sources": independent, "high_quality_sources": high,
            "medium_quality_sources": medium, "low_quality_sources": low,
            "sources": relevant, "evidence_analysis": deterministic,
            "reason": "The exact factual claim is supported by sufficiently strong authoritative evidence.",
        }

    ai = compare_claim_with_sources(claim=claim, sources=relevant[:6])
    ai_decision = ai.get("decision", "UNCERTAIN")
    ai_confidence = ai.get("confidence", 0.0)

    # AI can only confirm a claim when deterministic evidence already contains
    # either one exact high-quality source or two independent exact medium-quality sources.
    ai_can_verify = (
        ai_decision == "SUPPORTED"
        and ai_confidence >= 0.75
        and (
            high >= 1
            or (supporting >= minimum_sources and medium >= 2)
        )
    )
    if ai_can_verify:
        return {
            "claim": claim, "decision": "verified", "verified": True,
            "confidence": round(min(max(ai_confidence, 0.75), 0.95), 2),
            "sources_found": len(sources), "relevant_sources": len(relevant),
            "supporting_sources": supporting, "independent_sources": independent,
            "high_quality_sources": high, "medium_quality_sources": medium,
            "low_quality_sources": low, "sources": relevant,
            "evidence_analysis": ai,
            "reason": "The claim passed strict evidence analysis with authoritative or sufficiently corroborated support.",
        }

    if ai_decision == "CONTRADICTED":
        return {
            "claim": claim, "decision": "review_required", "verified": False,
            "confidence": round(max(ai_confidence, 0.70), 2),
            "sources_found": len(sources), "relevant_sources": len(relevant),
            "supporting_sources": supporting, "independent_sources": independent,
            "high_quality_sources": high, "medium_quality_sources": medium,
            "low_quality_sources": low, "sources": relevant,
            "evidence_analysis": ai,
            "reason": "Evidence conflicts with the claim. Human review is required.",
        }

    return {
        "claim": claim, "decision": "review_required", "verified": False,
        "confidence": round(min(ai_confidence, 0.65), 2),
        "sources_found": len(sources), "relevant_sources": len(relevant),
        "supporting_sources": supporting, "independent_sources": independent,
        "high_quality_sources": high, "medium_quality_sources": medium,
        "low_quality_sources": low, "sources": relevant,
        "evidence_analysis": ai,
        "reason": "Relevant evidence was found, but it is not strong enough for automatic verification.",
    }
