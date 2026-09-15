import re


SENSITIVE_KEYWORDS = [
    "war",
    "terrorism",
    "terrorist",
    "violence",
    "death",
    "murder",
    "suicide",
    "politics",
    "election",
    "religion",
    "hate",
]


def check_safety(
    caption: str,
    news_title: str = None,
    news_source: str = None
):
    """
    Basic safety and content validation for AI-generated posts.
    """

    issues = []

    # 1. Caption must exist
    if not caption or not caption.strip():
        issues.append("Caption is empty.")

    # 2. News-based post should have source
    if news_title and not news_source:
        issues.append("News source is missing.")

    # 3. Check sensitive keywords
    text = f"{caption} {news_title or ''}".lower()

    detected_sensitive_topics = []

    for keyword in SENSITIVE_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            detected_sensitive_topics.append(keyword)

    if detected_sensitive_topics:
        issues.append(
            "Sensitive topic detected."
        )

    # 4. Decide whether human review is required
    if issues:
        decision = "review_required"
        safe = False
    else:
        decision = "safe_to_publish"
        safe = True

    return {
        "safe": safe,
        "decision": decision,
        "issues": issues,
        "sensitive_topics": detected_sensitive_topics
    }