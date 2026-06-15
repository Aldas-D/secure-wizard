"""Pydantic schemos rezultato atvaizdavimui ir API atsakymams."""

from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def display_name(self) -> str:
        return {
            "LOW": "Žemas",
            "MEDIUM": "Vidutinis",
            "HIGH": "Aukštas",
            "CRITICAL": "Kritinis",
        }[self.value]

    @property
    def color_class(self) -> str:
        return {
            "LOW": "bg-green-500",
            "MEDIUM": "bg-yellow-500",
            "HIGH": "bg-orange-500",
            "CRITICAL": "bg-red-600",
        }[self.value]


class RiskProfileSchema(BaseModel):
    total_score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    level: RiskLevel
    areas: dict[str, float] = Field(default_factory=dict)

    @property
    def percentage(self) -> int:
        return round((self.total_score / self.max_score) * 100) if self.max_score else 0


class PlanItemSchema(BaseModel):
    id: int
    title: str
    description: str
    priority: int = Field(ge=1, le=5)
    risk_area: str
    when_specialist: str | None = None


class PlanResultSchema(BaseModel):
    profile: RiskProfileSchema
    items: list[PlanItemSchema]
    generated_at: str
