"""Rizikos skaičiavimo testai."""

from types import SimpleNamespace

import pytest

from app.schemas.result import RiskLevel
from app.services.risk_engine import RiskEngine


def _make_session_answer(question_id: int, risk_weight: int, risk_areas: list[str]):
    answer = SimpleNamespace(risk_weight=risk_weight)
    question = SimpleNamespace(risk_areas=risk_areas)
    return SimpleNamespace(
        question_id=question_id,
        answer=answer,
        question=question,
    )


class TestRiskEngine:
    def setup_method(self):
        self.engine = RiskEngine()

    def test_empty_answers_returns_low(self):
        profile = self.engine.calculate([])
        assert profile.level == RiskLevel.LOW
        assert profile.total_score == 0

    def test_all_zero_weights_is_low(self):
        answers = [_make_session_answer(i, 0, ["PWD"]) for i in range(1, 11)]
        profile = self.engine.calculate(answers)
        assert profile.level == RiskLevel.LOW
        assert profile.total_score == 0

    def test_all_max_weights_is_critical(self):
        answers = [_make_session_answer(i, 10, ["PWD"]) for i in range(1, 11)]
        profile = self.engine.calculate(answers)
        assert profile.level == RiskLevel.CRITICAL
        assert profile.total_score == 100
        assert profile.max_score == 100

    def test_medium_threshold(self):
        answers = [_make_session_answer(i, 3, ["PWD"]) for i in range(1, 11)]
        profile = self.engine.calculate(answers)
        assert profile.level == RiskLevel.MEDIUM

    def test_high_threshold(self):
        answers = [_make_session_answer(i, 6, ["PWD"]) for i in range(1, 11)]
        profile = self.engine.calculate(answers)
        assert profile.level == RiskLevel.HIGH

    def test_area_scores_normalized(self):
        answers = [
            _make_session_answer(1, 10, ["PWD"]),
            _make_session_answer(2, 0, ["NET"]),
            _make_session_answer(3, 5, ["NET"]),
        ]
        profile = self.engine.calculate(answers)
        assert profile.areas["PWD"] == 10.0
        assert profile.areas["NET"] == 2.5

    def test_multi_area_question(self):
        answers = [_make_session_answer(1, 8, ["PWD", "ACC"])]
        profile = self.engine.calculate(answers)
        assert profile.areas["PWD"] == 8.0
        assert profile.areas["ACC"] == 8.0

    def test_percentage_calculation(self):
        answers = [_make_session_answer(i, 5, ["PWD"]) for i in range(1, 11)]
        profile = self.engine.calculate(answers)
        assert profile.percentage == 50

    def test_multiple_answers_are_capped_per_question(self):
        answers = [
            _make_session_answer(1, 8, ["APP"]),
            _make_session_answer(1, 6, ["APP"]),
        ]
        profile = self.engine.calculate(answers)
        assert profile.total_score == 10
        assert profile.max_score == 10
        assert profile.percentage == 100
        assert profile.areas["APP"] == 10.0


@pytest.mark.parametrize(
    "weight_per_q,expected_level",
    [
        (0, RiskLevel.LOW),
        (2, RiskLevel.LOW),
        (3, RiskLevel.MEDIUM),
        (4, RiskLevel.MEDIUM),
        (5, RiskLevel.HIGH),
        (7, RiskLevel.HIGH),
        (8, RiskLevel.CRITICAL),
        (10, RiskLevel.CRITICAL),
    ],
)
def test_level_thresholds(weight_per_q, expected_level):
    engine = RiskEngine()
    answers = [_make_session_answer(i, weight_per_q, ["PWD"]) for i in range(1, 11)]
    profile = engine.calculate(answers)
    assert profile.level == expected_level
