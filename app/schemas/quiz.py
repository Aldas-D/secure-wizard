"""Pydantic validacijos schemos klausimynui."""

from pydantic import BaseModel, Field, field_validator

ALLOWED_PLATFORMS = {"WIN", "AND"}


class PlatformChoice(BaseModel):
    platform: str = Field(min_length=3, max_length=10)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        v = v.upper()
        if v not in ALLOWED_PLATFORMS:
            raise ValueError(f"Platforma turi būti viena iš: {sorted(ALLOWED_PLATFORMS)}")
        return v


class AnswerSubmission(BaseModel):
    question_id: int = Field(gt=0)
    answer_ids: list[int] = Field(min_length=1, max_length=10)

    @field_validator("answer_ids")
    @classmethod
    def unique_answers(cls, v: list[int]) -> list[int]:
        if len(set(v)) != len(v):
            raise ValueError("Atsakymai turi būti unikalūs")
        if any(a <= 0 for a in v):
            raise ValueError("Atsakymo ID turi būti teigiamas skaičius")
        return v
