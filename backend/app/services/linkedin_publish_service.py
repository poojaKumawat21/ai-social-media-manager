import requests


LINKEDIN_POST_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_IMAGES_URL = "https://api.linkedin.com/rest/images?action=initializeUpload"

# LinkedIn API version: YYYYMM
LINKEDIN_VERSION = "202608"


def _linkedin_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": LINKEDIN_VERSION,
    }


def upload_image_to_linkedin(
    access_token: str,
    author_id: str,
    image_url: str,
) -> str:

    if not access_token:
        raise ValueError("LinkedIn access token is required.")

    if not author_id:
        raise ValueError("LinkedIn author ID is required.")

    if not image_url:
        raise ValueError("Image URL is required.")

    # ---------------------------------------------------------
    # STEP 1: Download image from Supabase Storage
    # ---------------------------------------------------------

    image_response = requests.get(
        image_url,
        timeout=30,
    )

    if not image_response.ok:
        raise RuntimeError(
            "Could not download image from storage: "
            f"{image_response.status_code} {image_response.text}"
        )

    image_bytes = image_response.content

    if not image_bytes:
        raise RuntimeError("Downloaded image is empty.")

    # ---------------------------------------------------------
    # STEP 2: Initialize LinkedIn image upload
    # ---------------------------------------------------------

    initialize_payload = {
        "initializeUploadRequest": {
            "owner": f"urn:li:person:{author_id}"
        }
    }

    headers = _linkedin_headers(access_token)
    headers["Content-Type"] = "application/json"

    initialize_response = requests.post(
        LINKEDIN_IMAGES_URL,
        json=initialize_payload,
        headers=headers,
        timeout=30,
    )

    if not initialize_response.ok:
        raise RuntimeError(
            "LinkedIn image initialization failed: "
            f"{initialize_response.status_code} "
            f"{initialize_response.text}"
        )

    initialize_data = initialize_response.json()

    value = initialize_data.get("value") or {}

    upload_url = value.get("uploadUrl")
    image_urn = value.get("image")

    if not upload_url:
        raise RuntimeError(
            "LinkedIn did not return an image upload URL."
        )

    if not image_urn:
        raise RuntimeError(
            "LinkedIn did not return an image URN."
        )

    # ---------------------------------------------------------
    # STEP 3: Upload actual image bytes
    # ---------------------------------------------------------

    upload_response = requests.put(
        upload_url,
        data=image_bytes,
        headers={
            "Content-Type": "image/png",
        },
        timeout=60,
    )

    if not upload_response.ok:
        raise RuntimeError(
            "LinkedIn image upload failed: "
            f"{upload_response.status_code} "
            f"{upload_response.text}"
        )

    return image_urn


def publish_linkedin_text_post(
    access_token: str,
    author_id: str,
    text: str,
    image_url: str | None = None,
) -> dict:

    if not access_token:
        raise ValueError("LinkedIn access token is required.")

    if not author_id:
        raise ValueError("LinkedIn author ID is required.")

    if not text or not text.strip():
        raise ValueError("Post text is required.")

    # ---------------------------------------------------------
    # Base LinkedIn post
    # ---------------------------------------------------------

    payload = {
        "author": f"urn:li:person:{author_id}",
        "commentary": text.strip(),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    # ---------------------------------------------------------
    # If image exists, upload it and attach it
    # ---------------------------------------------------------

    if image_url:
        image_urn = upload_image_to_linkedin(
            access_token=access_token,
            author_id=author_id,
            image_url=image_url,
        )

        payload["content"] = {
            "media": {
                "altText": "AI generated social media post",
                "id": image_urn,
            }
        }

    # ---------------------------------------------------------
    # Publish post
    # ---------------------------------------------------------

    headers = _linkedin_headers(access_token)
    headers["Content-Type"] = "application/json"

    response = requests.post(
        LINKEDIN_POST_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "LinkedIn post publishing failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    post_id = response.headers.get("x-restli-id")

    return {
        "success": True,
        "post_id": post_id,
        "status": "published",
        "image_attached": bool(image_url),
    }
def publish_linkedin_multi_image_post(
    access_token: str,
    author_id: str,
    text: str,
    image_urls: list[str],
) -> dict:

    if not access_token:
        raise ValueError("LinkedIn access token is required.")

    if not author_id:
        raise ValueError("LinkedIn author ID is required.")

    if not text or not text.strip():
        raise ValueError("Post text is required.")

    if not image_urls:
        raise ValueError("At least one image URL is required.")

    # LinkedIn MultiImage supports 2 to 20 images
    if len(image_urls) < 2:
        raise ValueError(
            "Multi-image post requires at least 2 images."
        )

    if len(image_urls) > 20:
        image_urls = image_urls[:20]

    # ---------------------------------------------------------
    # Upload every image and collect LinkedIn image URNs
    # ---------------------------------------------------------

    image_urns = []

    for image_url in image_urls:

        image_urn = upload_image_to_linkedin(
            access_token=access_token,
            author_id=author_id,
            image_url=image_url,
        )

        image_urns.append(image_urn)

    # ---------------------------------------------------------
    # Create LinkedIn MultiImage post
    # ---------------------------------------------------------

    payload = {
        "author": f"urn:li:person:{author_id}",
        "commentary": text.strip(),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
        "content": {
            "multiImage": {
                "images": [
                    {
                        "id": image_urn,
                        "altText": "AI generated social media post",
                    }
                    for image_urn in image_urns
                ]
            }
        },
    }

    headers = _linkedin_headers(access_token)
    headers["Content-Type"] = "application/json"

    response = requests.post(
        LINKEDIN_POST_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            "LinkedIn multi-image post publishing failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    post_id = response.headers.get("x-restli-id")

    return {
        "success": True,
        "post_id": post_id,
        "status": "published",
        "image_count": len(image_urns),
        "image_attached": True,
    }