from pydantic import BaseModel


class ProfileCreate(BaseModel):
    name: str
    email: str
    niche: str
    language: str = "English"
    tone: str = "Professional"