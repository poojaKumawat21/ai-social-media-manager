import io
import uuid

from app.database.supabase import supabase


BUCKET_NAME = "generated-posts"


def upload_image_to_storage(image, folder="generated"):
    """
    Upload a PIL Image to Supabase Storage
    and return its public URL.
    """

    if image is None:
        raise ValueError("Image is required for upload.")

    # Convert PIL Image → PNG bytes
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    # Unique filename
    filename = f"{folder}/{uuid.uuid4().hex}.png"

    # Upload to Supabase Storage
    supabase.storage.from_(BUCKET_NAME).upload(
        filename,
        image_bytes.getvalue(),
        {
            "content-type": "image/png",
            "upsert": "false",
        },
    )

    # Generate public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(filename)

    return {
        "storage_path": filename,
        "public_url": public_url,
        "bucket": BUCKET_NAME,
    }