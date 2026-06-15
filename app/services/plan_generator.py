"""Patikros plano generavimas pagal rizikos profilį ir atsakymų derinį."""

from datetime import UTC, datetime

from app.models import ChecklistItem, SessionAnswer
from app.repositories import ChecklistRepository
from app.schemas.result import PlanItemSchema, PlanResultSchema, RiskLevel, RiskProfileSchema

AREA_THRESHOLD = 2.5
HIGH_LEVELS = {RiskLevel.HIGH, RiskLevel.CRITICAL}


def _is_applicable(
    item: ChecklistItem,
    selected_answer_ids: set[int],
    weak_areas: set[str],
    profile_level: RiskLevel,
) -> bool:
    triggers = set(item.trigger_answer_ids)
    if triggers:
        return bool(selected_answer_ids & triggers)
    if item.risk_area in weak_areas:
        return True
    if profile_level in HIGH_LEVELS and item.priority <= 2:
        return True
    return False


class PlanGenerator:
    def generate(
        self,
        platform_id: int,
        profile: RiskProfileSchema,
        session_answers: list[SessionAnswer],
    ) -> PlanResultSchema:
        all_items = ChecklistRepository.find_by_platform(platform_id)
        selected_answer_ids = {sa.answer_id for sa in session_answers}
        weak_areas = {a for a, s in profile.areas.items() if s >= AREA_THRESHOLD}

        applicable = [
            i
            for i in all_items
            if _is_applicable(i, selected_answer_ids, weak_areas, profile.level)
        ]

        if not applicable:
            applicable = [i for i in all_items if i.priority <= 2][:3]

        applicable.sort(key=lambda i: (i.priority, i.risk_area))

        items = [
            PlanItemSchema(
                id=i.id,
                title=i.title,
                description=i.description,
                priority=i.priority,
                risk_area=i.risk_area,
                when_specialist=i.when_specialist,
            )
            for i in applicable
        ]

        return PlanResultSchema(
            profile=profile,
            items=items,
            generated_at=datetime.now(UTC).isoformat(),
        )
