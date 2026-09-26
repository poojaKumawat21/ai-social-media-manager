import re
import time
import requests


GRAPH_BASE_URL = "https://graph.instagram.com"


def normalize_media_url(url: str) -> str:
    """
    Converts markdown-stored URLs like:
    [https://example.com/image.png](https://example.com/image.png)

    into:
    https://example.com/image.png
    """

    if not url:
        return url

    match = re.search(r"\]\((https?://[^)]+)\)", url)

    if match:
        return match.group(1)

    return url.strip()


def create_instagram_media_container(
    instagram_user_id: str,
    access_token: str,
    image_url: str,
    caption: str = "",
) -> str:
    """
    Creates an Instagram media container for an image post.
    """

    image_url = normalize_media_url(image_url)

    url = f"{GRAPH_BASE_URL}/{instagram_user_id}/media"

    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }

    response = requests.post(
        url,
        data=payload,
        timeout=60,
    )

    if not response.ok:
        raise Exception(
            f"Instagram media container creation failed: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    creation_id = data.get("id")

    if not creation_id:
        raise Exception(
            f"Instagram did not return a creation ID: {data}"
        )

    return creation_id


def wait_for_instagram_media_ready(
    creation_id: str,
    access_token: str,
    max_attempts: int = 20,
    wait_seconds: int = 3,
):
    """
    Waits until Instagram finishes processing the media container.
    """

    url = f"{GRAPH_BASE_URL}/{creation_id}"

    for _ in range(max_attempts):

        response = requests.get(
            url,
            params={
                "fields": "status_code",
                "access_token": access_token,
            },
            timeout=30,
        )

        if not response.ok:
            raise Exception(
                f"Instagram media status check failed: "
                f"{response.status_code} - {response.text}"
            )

        data = response.json()
        status = data.get("status_code")

        if status == "FINISHED":
            return True

        if status in ["ERROR", "EXPIRED"]:
            raise Exception(
                f"Instagram media processing failed: {data}"
            )

        time.sleep(wait_seconds)

    raise Exception(
        "Instagram media container was not ready within the expected time."
    )


def publish_instagram_media(
    instagram_user_id: str,
    access_token: str,
    creation_id: str,
) -> str:
    """
    Publishes a ready Instagram media container.
    """

    url = f"{GRAPH_BASE_URL}/{instagram_user_id}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": access_token,
    }

    response = requests.post(
        url,
        data=payload,
        timeout=60,
    )

    if not response.ok:
        raise Exception(
            f"Instagram media publish failed: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    media_id = data.get("id")

    if not media_id:
        raise Exception(
            f"Instagram did not return a published media ID: {data}"
        )

    return media_id


def publish_instagram_image_post(
    instagram_user_id: str,
    access_token: str,
    image_url: str,
    caption: str = "",
) -> dict:
    """
    Complete Instagram image publishing flow:

    1. Create media container
    2. Wait until media is processed
    3. Publish media
    """

    creation_id = create_instagram_media_container(
        instagram_user_id=instagram_user_id,
        access_token=access_token,
        image_url=image_url,
        caption=caption,
    )

    wait_for_instagram_media_ready(
        creation_id=creation_id,
        access_token=access_token,
    )

    media_id = publish_instagram_media(
        instagram_user_id=instagram_user_id,
        access_token=access_token,
        creation_id=creation_id,
    )

    return {
        "success": True,
        "creation_id": creation_id,
        "media_id": media_id,
    }