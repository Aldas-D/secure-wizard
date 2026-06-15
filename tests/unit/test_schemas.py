"""Pydantic schemų testai."""

import pytest
from pydantic import ValidationError

from app.schemas.quiz import AnswerSubmission, PlatformChoice


class TestPlatformChoice:
    def test_valid_windows(self):
        choice = PlatformChoice(platform="WIN")
        assert choice.platform == "WIN"

    def test_valid_android_lowercase(self):
        choice = PlatformChoice(platform="and")
        assert choice.platform == "AND"

    def test_invalid_platform(self):
        with pytest.raises(ValidationError):
            PlatformChoice(platform="LINUX")

    def test_empty_platform(self):
        with pytest.raises(ValidationError):
            PlatformChoice(platform="")


class TestAnswerSubmission:
    def test_valid_single_answer(self):
        s = AnswerSubmission(question_id=1, answer_ids=[5])
        assert s.question_id == 1
        assert s.answer_ids == [5]

    def test_valid_multiple_answers(self):
        s = AnswerSubmission(question_id=1, answer_ids=[5, 7, 9])
        assert len(s.answer_ids) == 3

    def test_empty_answers_rejected(self):
        with pytest.raises(ValidationError):
            AnswerSubmission(question_id=1, answer_ids=[])

    def test_duplicate_answers_rejected(self):
        with pytest.raises(ValidationError):
            AnswerSubmission(question_id=1, answer_ids=[5, 5])

    def test_negative_answer_id_rejected(self):
        with pytest.raises(ValidationError):
            AnswerSubmission(question_id=1, answer_ids=[-1])

    def test_too_many_answers_rejected(self):
        with pytest.raises(ValidationError):
            AnswerSubmission(question_id=1, answer_ids=list(range(1, 20)))

    def test_invalid_question_id(self):
        with pytest.raises(ValidationError):
            AnswerSubmission(question_id=0, answer_ids=[5])
