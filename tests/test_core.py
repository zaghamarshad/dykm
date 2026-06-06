import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai import parse_quiz_json, _strip_fences


# ---------------------------------------------------------------------------
# Helpers mirroring the scoring logic in app.py
# ---------------------------------------------------------------------------

def score_play(questions: list[dict], chosen: list[int]) -> tuple[int, list[str]]:
    """Return (score, [quip_per_question])."""
    score = 0
    quips = []
    for q, answer in zip(questions, chosen):
        correct = answer == q["correct_index"]
        score += int(correct)
        quips.append(q["quips"][answer])
    return score, quips


QUESTIONS = [
    {"text": "Q1", "options": ["A","B","C","D"], "correct_index": 0, "quips": ["r0","w0a","w0b","w0c"]},
    {"text": "Q2", "options": ["A","B","C","D"], "correct_index": 1, "quips": ["w1a","r1","w1b","w1c"]},
    {"text": "Q3", "options": ["A","B","C","D"], "correct_index": 2, "quips": ["w2a","w2b","r2","w2c"]},
    {"text": "Q4", "options": ["A","B","C","D"], "correct_index": 3, "quips": ["w3a","w3b","w3c","r3"]},
    {"text": "Q5", "options": ["A","B","C","D"], "correct_index": 0, "quips": ["r4","w4a","w4b","w4c"]},
    {"text": "Q6", "options": ["A","B","C","D"], "correct_index": 1, "quips": ["w5a","r5","w5b","w5c"]},
    {"text": "Q7", "options": ["A","B","C","D"], "correct_index": 2, "quips": ["w6a","w6b","r6","w6c"]},
]

CORRECT_ANSWERS = [q["correct_index"] for q in QUESTIONS]


class TestScoringLogic:
    def test_all_correct(self):
        score, quips = score_play(QUESTIONS, CORRECT_ANSWERS)
        assert score == 7
        assert quips == ["r0", "r1", "r2", "r3", "r4", "r5", "r6"]

    def test_all_wrong(self):
        # everyone picks option 1 (wrong for Q1, Q3, Q4, Q5, Q7; right for Q2, Q6)
        chosen = [1, 1, 1, 1, 1, 1, 1]
        score, quips = score_play(QUESTIONS, chosen)
        assert score == 2  # Q2 and Q6 correct
        assert quips[0] == "w0a"   # Q1: correct=0, chose 1 → wrong
        assert quips[1] == "r1"    # Q2: correct=1, chose 1 → right
        assert quips[2] == "w2b"   # Q3: correct=2, chose 1 → wrong
        assert quips[5] == "r5"    # Q6: correct=1, chose 1 → right

    def test_mixed(self):
        # Q1 correct_index=0 chose 0→right, Q2 correct_index=1 chose 0→wrong,
        # Q3 correct_index=2 chose 2→right, Q4 correct_index=3 chose 0→wrong,
        # Q5 correct_index=0 chose 3→wrong, Q6 correct_index=1 chose 1→right,
        # Q7 correct_index=2 chose 0→wrong  ⇒ score 3
        chosen = [0, 0, 2, 0, 3, 1, 0]
        score, quips = score_play(QUESTIONS, chosen)
        assert score == 3
        assert quips[0] == "r0"    # correct
        assert quips[1] == "w1a"   # wrong, chose option 0
        assert quips[2] == "r2"    # correct
        assert quips[3] == "w3a"   # wrong, chose option 0
        assert quips[4] == "w4c"   # wrong, chose option 3
        assert quips[5] == "r5"    # correct
        assert quips[6] == "w6a"   # wrong, chose option 0

    def test_score_zero(self):
        all_wrong = [3, 3, 3, 2, 3, 3, 3]
        score, _ = score_play(QUESTIONS, all_wrong)
        assert score == 0

    def test_score_seven(self):
        score, _ = score_play(QUESTIONS, CORRECT_ANSWERS)
        assert score == 7

    def test_quip_selection_per_question(self):
        chosen = [0, 0, 0, 0, 0, 0, 0]  # only Q1 and Q5 are correct (correct_index 0)
        _, quips = score_play(QUESTIONS, chosen)
        assert quips[0] == "r0"    # correct_index 0, chose 0 → right
        assert quips[1] == "w1a"   # correct_index 1, chose 0 → wrong (option 0 quip)
        assert quips[4] == "r4"    # correct_index 0, chose 0 → right

    def test_specific_wrong_option_quip(self):
        # Q3 correct=2: picking option 0 gives w2a, picking option 1 gives w2b, option 3 gives w2c
        _, quips = score_play(QUESTIONS, [0, 0, 0, 0, 0, 0, 0])
        assert quips[2] == "w2a"   # chose option 0 for Q3
        _, quips = score_play(QUESTIONS, [0, 0, 3, 0, 0, 0, 0])
        assert quips[2] == "w2c"   # chose option 3 for Q3


# ---------------------------------------------------------------------------
# JSON parsing / fence stripping
# ---------------------------------------------------------------------------

VALID_ARRAY = [{"text": "Q", "options": ["A","B","C","D"], "correct_index": 0,
                "quips": ["right quip", "wrong quip 1", "wrong quip 2", "wrong quip 3"]}]
VALID_JSON = json.dumps(VALID_ARRAY)


class TestParseQuizJson:
    def test_clean_json(self):
        result = parse_quiz_json(VALID_JSON)
        assert result == VALID_ARRAY

    def test_json_fenced_with_json_tag(self):
        fenced = f"```json\n{VALID_JSON}\n```"
        result = parse_quiz_json(fenced)
        assert result == VALID_ARRAY

    def test_json_fenced_no_tag(self):
        fenced = f"```\n{VALID_JSON}\n```"
        result = parse_quiz_json(fenced)
        assert result == VALID_ARRAY

    def test_json_with_leading_trailing_whitespace(self):
        result = parse_quiz_json(f"  \n{VALID_JSON}\n  ")
        assert result == VALID_ARRAY

    def test_malformed_json_raises(self):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parse_quiz_json("this is not json at all")

    def test_malformed_fenced_raises(self):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            parse_quiz_json("```json\n{broken\n```")

    def test_strip_fences_idempotent_on_plain(self):
        assert _strip_fences(VALID_JSON) == VALID_JSON

    def test_strip_fences_removes_json_tag(self):
        result = _strip_fences(f"```json\n{VALID_JSON}\n```")
        assert result == VALID_JSON

    def test_strip_fences_removes_plain_tag(self):
        result = _strip_fences(f"```\n{VALID_JSON}\n```")
        assert result == VALID_JSON
