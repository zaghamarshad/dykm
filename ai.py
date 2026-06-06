import json
import re

import anthropic

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are a comedy writer for a "Do You Know Me?" roast quiz. Write exactly 7 multiple-choice questions about the person.

CRITICAL SCHEMA — you MUST use exactly these keys, no others:
  "text"          - the question string
  "options"       - array of exactly 4 strings (the answer choices)
  "correct_index" - integer 0-3 (which option is correct)
  "quips"         - array of exactly 4 strings

DO NOT use "quip_right" or "quip_wrong". Those keys are wrong. Use "quips" only.

HOW TO WRITE "quips":
quips is an array of 4 strings. quips[i] is shown to a player who picked options[i].
- quips[correct_index]: shown when they got it right. Mock them for knowing this embarrassing detail.
- quips[any other index]: shown when they picked THAT specific wrong option. Name the wrong option. Roast them for it. Tell them the correct answer. Make it sting.

TONE: think Kevin Hart roasting a friend at their birthday — bold, specific, a little mean, but punching with love. No softening. No "nice try". No "close". No "not quite". Every quip must name what they picked or what's actually true.

Return ONLY a JSON array. No prose. No markdown fences. No explanation. Just the array.

EXAMPLE — follow this structure exactly:
[
  {
    "text": "What is Alex's go-to comfort food?",
    "options": ["Tacos", "Mac and cheese", "Sushi", "Pizza"],
    "correct_index": 1,
    "quips": [
      "Tacos? Alex hasn't touched a taco since the Incident of 2019 and will not explain why. The answer is mac and cheese — the humble, beige cornerstone of their entire emotional life.",
      "You knew it was mac and cheese. You've sat with Alex at 1am while they stress-ate an entire pot and cried about something they couldn't name. You witnessed it. You said nothing. Now you're profiting.",
      "Sushi is a very aspirational guess from someone who has clearly never seen Alex's fridge. The answer is mac and cheese — the box kind — and you would know that if you'd ever been there for the hard times.",
      "Pizza would be a great answer for someone who doesn't know Alex at all. The answer is mac and cheese. Four dollars a box. Eaten alone. You've never been close enough to witness it."
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


def generate_quiz(creator_name: str, answers: list[str]) -> list[dict]:
    """Make exactly one Anthropic API call and return 7 question dicts."""
    numbered = "\n".join(f"{i+1}. {a}" for i, a in enumerate(answers))
    user_message = (
        f"Creator name: {creator_name}\n\n"
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

    return questions
