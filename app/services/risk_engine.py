"""Rizikos profilio skaičiavimas."""

from collections import defaultdict
from dataclasses import dataclass

from app.models import SessionAnswer
from app.schemas.result import RiskLevel, RiskProfileSchema


@dataclass(frozen=True)
class RiskThresholds:
    medium: float = 2.5
    high: float = 5.0
    critical: float = 7.5


class RiskEngine:
    MAX_WEIGHT_PER_ANSWER = 10
    thresholds = RiskThresholds()

    _LEVEL_ORDER = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }

    def calculate(self, answers: list[SessionAnswer]) -> RiskProfileSchema:
        if not answers:
            return RiskProfileSchema(total_score=0, max_score=1, level=RiskLevel.LOW, areas={})

        question_scores = self._calculate_question_scores(answers)
        n_questions = len(question_scores)
        total_score = sum(question_scores.values())
        max_score = n_questions * self.MAX_WEIGHT_PER_ANSWER

        avg_per_question = total_score / n_questions
        avg_level = self._classify_level(avg_per_question)

        areas = self._calculate_area_scores(answers)

        worst_area_score = max(areas.values()) if areas else 0
        worst_level = self._classify_level(worst_area_score)

        final_level = self._max_level(avg_level, worst_level)

        return RiskProfileSchema(
            total_score=total_score,
            max_score=max_score,
            level=final_level,
            areas=areas,
        )

    def _classify_level(self, score: float) -> RiskLevel:
        if score >= self.thresholds.critical:
            return RiskLevel.CRITICAL
        if score >= self.thresholds.high:
            return RiskLevel.HIGH
        if score >= self.thresholds.medium:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _max_level(self, a: RiskLevel, b: RiskLevel) -> RiskLevel:
        return a if self._LEVEL_ORDER[a] >= self._LEVEL_ORDER[b] else b

    def _calculate_area_scores(self, answers: list[SessionAnswer]) -> dict[str, float]:
        area_totals: dict[str, list[int]] = defaultdict(list)
        answers_by_question: dict[int, list[SessionAnswer]] = defaultdict(list)
        for answer in answers:
            answers_by_question[answer.question_id].append(answer)

        for question_answers in answers_by_question.values():
            weight = min(
                self.MAX_WEIGHT_PER_ANSWER,
                sum(answer.answer.risk_weight for answer in question_answers),
            )
            for area in question_answers[0].question.risk_areas:
                area_totals[area].append(weight)
        return {
            area: round(sum(weights) / len(weights), 2)
            for area, weights in area_totals.items()
            if weights
        }

    def _calculate_question_scores(self, answers: list[SessionAnswer]) -> dict[int, int]:
        scores: dict[int, int] = defaultdict(int)
        for answer in answers:
            scores[answer.question_id] = min(
                self.MAX_WEIGHT_PER_ANSWER,
                scores[answer.question_id] + answer.answer.risk_weight,
            )
        return dict(scores)
