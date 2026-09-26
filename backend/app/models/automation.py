from pydantic import BaseModel
from typing import Optional


class AutomationCreate(BaseModel):
    profile_id: Optional[str] = None
    niche: str
    topic: str
    language: str = "English"
    tone: str = "Professional"
    frequency: str = "daily"
    posting_time: str
    is_enabled: bool = True
    is_paused: bool = False


class AutomationUpdate(BaseModel):
    niche: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = None
    tone: Optional[str] = None
    frequency: Optional[str] = None
    posting_time: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_paused: Optional[bool] = None