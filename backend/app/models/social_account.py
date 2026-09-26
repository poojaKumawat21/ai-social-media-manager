from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SocialAccountCreate(BaseModel):
    platform: str
    platform_user_id: Optional[str] = None
    account_name: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    scopes: List[str] = []


class SocialAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    scopes: Optional[List[str]] = None
    status: Optional[str] = None