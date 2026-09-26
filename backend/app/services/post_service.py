from app.database.supabase import supabase


def save_post(post_data):
    response = (
        supabase
        .table("posts")
        .insert(post_data)
        .execute()
    )

    return response.data


def get_previous_posts(profile_id=None, limit=20):

    query = (
        supabase
        .table("posts")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )

    if profile_id:
        query = query.eq("profile_id", profile_id)

    response = query.execute()

    return response.data