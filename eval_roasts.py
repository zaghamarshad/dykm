"""
Offline evaluation script: generates quizzes for 3 sample creators and prints
every question with both roast lines so you can judge the humor.

Tweak SYSTEM_PROMPT in ai.py and re-run to iterate on the tone.
"""

from ai import SYSTEM_PROMPT, generate_quiz  # noqa: F401 — imported so you remember where to edit

SAMPLE_CREATORS = [
    {
        "name": "Marcus",
        "answers": [
            "I wake up at 5 AM to hit the gym every single day — no exceptions",
            "Chicken breast, rice, and broccoli. Every. Meal.",
            "My biggest fear is skipping leg day",
            "I own more protein powder than actual food",
            "My idea of a cheat day is extra avocado on my salad",
            "I've turned down birthday cake at least six times this year",
            "My love language is spotting someone at the squat rack",
        ],
    },
    {
        "name": "Priya",
        "answers": [
            "I've read over 80 books this year — I track them all in a spreadsheet",
            "My ideal Friday night is hot tea, a blanket, and a 600-page novel",
            "I have three library cards in different boroughs",
            "I start getting anxious if I'm more than 20 pages from the end of a chapter before bed",
            "My cat is named after a Jane Austen character",
            "I've cancelled plans to finish a book at least a dozen times",
            "I genuinely don't understand people who say they don't like reading",
        ],
    },
    {
        "name": "Diego",
        "answers": [
            "I will drive 45 minutes for a good taco and I have no regrets",
            "I've eaten at 34 different ramen spots in the city — I keep a notes app ranking",
            "My camera roll is 90% food photos",
            "I once changed my flight layover specifically to eat at an airport restaurant I'd seen on YouTube",
            "I learned basic Mandarin so I could order off the untranslated menu",
            "My friends text me before any restaurant decision — I'm the Yelp they actually trust",
            "I have a strong opinion about the correct order to eat a tasting menu",
        ],
    },
]


def _print_quiz(creator_name: str, questions: list[dict]) -> None:
    width = 72
    print("=" * width)
    print(f"  Quiz for: {creator_name}")
    print("=" * width)
    for i, q in enumerate(questions, 1):
        print(f"\nQ{i}: {q['text']}")
        for j, opt in enumerate(q["options"]):
            marker = "✓" if j == q["correct_index"] else " "
            print(f"  [{marker}] {j}. {opt}")
        print(f"  quip_right → {q['quip_right']}")
        print(f"  quip_wrong → {q['quip_wrong']}")
    print()


def main() -> None:
    print(f"\nUsing SYSTEM_PROMPT from ai.py (first 120 chars):\n  {SYSTEM_PROMPT[:120].strip()}...\n")
    for creator in SAMPLE_CREATORS:
        print(f"Generating quiz for {creator['name']}…")
        try:
            questions = generate_quiz(creator["name"], creator["answers"])
            _print_quiz(creator["name"], questions)
        except Exception as e:
            print(f"  ERROR for {creator['name']}: {e}\n")


if __name__ == "__main__":
    main()
