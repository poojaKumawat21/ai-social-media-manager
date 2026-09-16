from pydantic import BaseModel


class ProfileCreate(BaseModel):
    name: str
    niche: str
    language: str = "English"
    tone: str = "Professional"


class ProfileUpdate(BaseModel):
    name: str | None = None
    niche: str | None = None
    language: str | None = None
    tone: str | None = None