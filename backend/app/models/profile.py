from pydantic import BaseModel
from datetime import date


class ProfileCreate(BaseModel):

    name: str

    email: str | None = None

    dob: date

    niche: str

    language: str = "English"

    tone: str = "Professional"


class ProfileUpdate(BaseModel):

    name: str | None = None

    email: str | None = None

    dob: date | None = None

    niche: str | None = None

    language: str | None = None

    tone: str | None = None

    avatar_url: str | None = None