from app.database.supabase import supabase


def create_automation_settings(settings_data):
    """
    Create new automation settings for a user.
    """

    response = (
        supabase
        .table("automation_settings")
        .insert(settings_data)
        .execute()
    )

    return response.data


def get_automation_settings(profile_id=None):
    """
    Get automation settings.
    If profile_id is provided, return settings for that profile.
    """

    query = (
        supabase
        .table("automation_settings")
        .select("*")
        .order("created_at", desc=True)
    )

    if profile_id:
        query = query.eq("profile_id", profile_id)

    response = query.execute()

    return response.data


def get_automation_setting(setting_id):
    """
    Get one automation setting by ID.
    """

    response = (
        supabase
        .table("automation_settings")
        .select("*")
        .eq("id", setting_id)
        .single()
        .execute()
    )

    return response.data


def update_automation_settings(setting_id, updates):
    """
    Update automation settings.
    """

    response = (
        supabase
        .table("automation_settings")
        .update(updates)
        .eq("id", setting_id)
        .execute()
    )

    return response.data


def enable_automation(setting_id):
    """
    Enable automation.
    Scheduler synchronization is handled by the API layer.
    """

    return update_automation_settings(
        setting_id,
        {
            "is_enabled": True,
            "is_paused": False
        }
    )


def disable_automation(setting_id):
    """
    Disable automation.
    Scheduler synchronization is handled by the API layer.
    """

    return update_automation_settings(
        setting_id,
        {
            "is_enabled": False,
            "is_paused": False
        }
    )


def pause_automation(setting_id):
    """
    Pause automation temporarily.
    Scheduler synchronization is handled by the API layer.
    """

    return update_automation_settings(
        setting_id,
        {
            "is_paused": True
        }
    )


def resume_automation(setting_id):
    """
    Resume paused automation.
    Scheduler synchronization is handled by the API layer.
    """

    return update_automation_settings(
        setting_id,
        {
            "is_paused": False,
            "is_enabled": True
        }
    )


def delete_automation_settings(setting_id):
    """
    Delete automation settings.
    """

    response = (
        supabase
        .table("automation_settings")
        .delete()
        .eq("id", setting_id)
        .execute()
    )

    return response.data