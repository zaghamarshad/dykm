import json
import re

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are a comedy writer for a "Do You Know Me?" roast quiz. Write exactly 7 multiple-choice questions about the person.

QUESTION STYLE — this is the most important rule:
Do NOT write generic "What is X's favorite Y?" questions. Instead write specific, scenario-based questions that only a close friend would know the answer to. Put the person IN a situation and ask what happens next.

BAD (too generic): "What is Zagham's favorite food?"
GOOD (specific scenario): "It's Friday night and Zagham gets to pick dinner. What are they ordering without even looking at the menu?"

BAD: "Is Zagham a morning person or night owl?"
GOOD: "Zagham texts you at 2am saying 'you up?'. What are they doing?"

BAD: "What's Zagham's favorite season?"
GOOD: "Zagham has a free weekend with no plans. What does the weather look like outside?"

Make the questions feel like something only someone who has actually spent time with this person would know. Reference habits, patterns, embarrassing tendencies, obsessions — not just preferences.

CRITICAL SCHEMA — use exactly these keys, no others:
  "text"          - the question string
  "options"       - array of exactly 4 strings (the answer choices)
  "correct_index" - integer 0-3 (which option is correct)
  "quips"         - array of exactly 4 strings

DO NOT use "quip_right" or "quip_wrong". Use "quips" only.

HOW TO WRITE "quips":
quips[i] is shown to a player who picked options[i].
- quips[correct_index]: mock them for knowing this embarrassing detail about their friend.
- quips[any other index]: name the wrong option they picked, explain why it's wrong, make it sting.

TONE: Kevin Hart roasting a friend at their birthday — bold, specific, a little mean, punching with love. No softening. No "nice try". No "close". Every quip must reference what they picked or what's actually true.

Return ONLY a JSON array. No prose. No markdown fences. No explanation. Just the array.

EXAMPLE — follow this STRUCTURE and TONE, not the content:
[
  {
    "text": "It's Friday night and Alex gets to pick dinner. What are they ordering without even opening the menu?",
    "options": ["Tacos", "Mac and cheese", "Sushi", "Pizza"],
    "correct_index": 1,
    "quips": [
      "Tacos? Alex has a complicated history with tacos they refuse to discuss publicly. The answer is mac and cheese — the humble, beige cornerstone of their entire emotional life.",
      "You knew it was mac and cheese. You've watched Alex order it in situations where a normal person would branch out. You've accepted it. You're complicit.",
      "Sushi is aspirational. Alex respects sushi but would never commit to it on a Friday. The answer is mac and cheese, four dollars a box, every time, no regrets.",
      "Pizza would be correct for someone who doesn't really know Alex. The answer is mac and cheese. You've never been at the table when it counts."
    ]
  }
]
"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _clean_json(text: str) -> str:
    # Remove trailing commas before ] or } — models sometimes generate these
    return re.sub(r",\s*([}\]])", r"\1", text)


def parse_quiz_json(raw: str) -> list[dict]:
    """Strip stray code fences, clean trailing commas, then parse JSON."""
    return json.loads(_clean_json(_strip_fences(raw)))


def generate_quiz(creator_name: str, answers: list[str], theme: str = "", pinned: list[str] | None = None) -> list[dict]:
    """Make exactly one Anthropic API call and return 7 question dicts."""
    pinned_set = set(pinned or [])
    numbered = "\n".join(
        f"{i+1}. {a}{' ← MUST generate a question from this fact' if a in pinned_set else ''}"
        for i, a in enumerate(answers)
    )
    theme_line = f"Quiz theme: {theme}\n\n" if theme else ""
    user_message = (
        f"Creator name: {creator_name}\n\n"
        f"{theme_line}"
        f"Their answers about themselves:\n{numbered}\n\n"
        "Generate the quiz now."
    )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text
    questions = parse_quiz_json(raw)

    if not isinstance(questions, list) or len(questions) != 7:
        raise ValueError(f"Expected 7 questions, got {len(questions) if isinstance(questions, list) else type(questions)}")

    for i, q in enumerate(questions):
        if not isinstance(q.get("quips"), list) or len(q["quips"]) != 4:
            raise ValueError(f"Question {i} must have exactly 4 quips")
        if not isinstance(q.get("correct_index"), int) or not (0 <= q["correct_index"] <= 3):
            raise ValueError(f"Question {i} correct_index must be 0–3")
        if not isinstance(q.get("options"), list) or len(q["options"]) != 4:
            raise ValueError(f"Question {i} must have exactly 4 options")

    return questions
