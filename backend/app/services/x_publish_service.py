import requests


X_API_BASE_URL = "https://api.x.com/2"
X_POST_URL = f"{X_API_BASE_URL}/tweets"
X_MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"


def publish_x_text_post(
    access_token: str,
    text: str,
):
    if not access_token:
        raise ValueError("X access token is missing.")

    if not text or not text.strip():
        raise ValueError("X post text is empty.")

    response = requests.post(
        X_POST_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "text": text.strip(),
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"X post creation failed: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    if not data.get("data", {}).get("id"):
        raise RuntimeError(
            "X post ID was not returned."
        )

    return {
        "post_id": data["data"]["id"],
        "raw": data,
    }


def upload_x_media(
    access_token: str,
    image_url: str,
):
    if not access_token:
        raise ValueError("X access token is missing.")

    if not image_url:
        raise ValueError("X image URL is missing.")

    # Download generated image first
    image_response = requests.get(
        image_url,
        timeout=30,
    )

    if not image_response.ok:
        raise RuntimeError(
            f"Could not download image: "
            f"{image_response.status_code}"
        )

    media_response = requests.post(
        X_MEDIA_UPLOAD_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        files={
            "media": (
                "image.jpg",
                image_response.content,
                "image/jpeg",
            )
        },
        timeout=60,
    )

    if not media_response.ok:
        raise RuntimeError(
            f"X media upload failed: "
            f"{media_response.status_code} - "
            f"{media_response.text}"
        )

    data = media_response.json()

    media_id = data.get("media_id_string")

    if not media_id:
        raise RuntimeError(
            "X media ID was not returned."
        )

    return media_id


def publish_x_image_post(
    access_token: str,
    text: str,
    image_url: str,
):
    media_id = upload_x_media(
        access_token=access_token,
        image_url=image_url,
    )

    response = requests.post(
        X_POST_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "text": text.strip(),
            "media": {
                "media_ids": [media_id],
            },
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"X image post creation failed: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    post_id = data.get("data", {}).get("id")

    if not post_id:
        raise RuntimeError(
            "X post ID was not returned."
        )

    return {
        "post_id": post_id,
        "media_id": media_id,
        "raw": data,
    }