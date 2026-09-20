import re
from difflib import SequenceMatcher


def _normalize_text(text: str) -> str:
    """
    Normalize text before comparing posts.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _similarity(text_a: str, text_b: str) -> float:
    """
    Calculate similarity between two text strings.
    """
    a = _normalize_text(text_a)
    b = _normalize_text(text_b)

    if not a or not b:
        return 0.0

    return round(SequenceMatcher(None, a, b).ratio(), 3)


def check_duplicate_content(
    current_content: dict,
    previous_posts: list[dict] | None = None,
) -> dict:
    """
    Check whether the current AI-generated post is too similar
    to the user's previous posts.

    current_content can contain:
    - topic
    - caption
    - post_idea
    - hashtags
    - style

    previous_posts should contain previously generated posts.
    """

    previous_posts = previous_posts or []

    current_topic = current_content.get("topic", "")
    current_caption = current_content.get("caption", "")
    current_idea = current_content.get("post_idea", "")

    current_text = " ".join(
        [
            str(current_topic),
            str(current_caption),
            str(current_idea),
        ]
    )

    if not current_text.strip():
        return {
            "duplicate": False,
            "decision": "review_required",
            "similarity": 0.0,
            "matched_post_id": None,
            "reason": "Current content is empty.",
        }

    highest_similarity = 0.0
    matched_post_id = None
    matched_topic = None

    for post in previous_posts:
        previous_text = " ".join(
            [
                str(post.get("topic", "")),
                str(post.get("caption", "")),
                str(post.get("post_idea", "")),
            ]
        )

        similarity = _similarity(current_text, previous_text)

        if similarity > highest_similarity:
            highest_similarity = similarity
            matched_post_id = post.get("id")
            matched_topic = post.get("topic")

    # Very high similarity = likely duplicate
    if highest_similarity >= 0.85:
        return {
            "duplicate": True,
            "decision": "regenerate_required",
            "similarity": highest_similarity,
            "matched_post_id": matched_post_id,
            "matched_topic": matched_topic,
            "reason": "The generated content is too similar to a previous post.",
        }

    # Moderate similarity = review
    if highest_similarity >= 0.65:
        return {
            "duplicate": False,
            "decision": "review_required",
            "similarity": highest_similarity,
            "matched_post_id": matched_post_id,
            "matched_topic": matched_topic,
            "reason": "The generated content has noticeable similarity to a previous post.",
        }

    # Low similarity = safe to continue
    return {
        "duplicate": False,
        "decision": "unique",
        "similarity": highest_similarity,
        "matched_post_id": matched_post_id,
        "matched_topic": matched_topic,
        "reason": "No significant similarity with previous posts was detected.",
    }