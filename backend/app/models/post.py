from pydantic import BaseModel
from typing import List, Optional


class PostCreate(BaseModel):
    profile_id: Optional[str] = None
    niche: str
    topic: str
    caption: str
    hashtags: List[str]
    post_idea: str
    style: str
    language: str
    tone: str
    news_title: Optional[str] = None
    news_source: Optional[str] = None
    status: str = "generated"


class PostUpdate(BaseModel):
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    post_idea: Optional[str] = None
    tone: Optional[str] = None
    style: Optional[str] = None
    status: Optional[str] = None