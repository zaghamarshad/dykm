# DYKM — "Do You Know Me?" Quiz App · Phase 1 Backend

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run the server

```bash
flask --app app run
# Listening on http://127.0.0.1:5000
```

---

## End-to-end curl flow

### 1. Create a quiz

```bash
curl -s -X POST http://localhost:5000/quizzes \
  -H "Content-Type: application/json" \
  -d '{
    "creator_name": "Alex",
    "answers": [
      "Coffee — always black, never decaf",
      "Cats (two of them, both chaotic)",
      "Italy is my dream destination",
      "I stress-bake bread when anxious",
      "Parks and Recreation, rewatched four times",
      "I cannot sleep past 7 AM even on weekends",
      "My love language is sending memes at 2 AM"
    ]
  }'
```

**Response:**
```json
{"id": "abc123", "share_path": "/q/abc123"}
```

---

### 2. Fetch a quiz for playing (no answers exposed)

```bash
curl -s http://localhost:5000/quizzes/abc123 | python -m json.tool
```

**Response:** returns `questions` with only `text` and `options` — no correct answers.

---

### 3. Submit answers and get scored

```bash
curl -s -X POST http://localhost:5000/quizzes/abc123/plays \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "Jordan",
    "answers": [0, 2, 1, 3, 0, 1, 2]
  }'
```

`answers` is a list of 7 integers (0–3), one per question, in order.

**Response:**
```json
{
  "score": 4,
  "total": 7,
  "summary": "Pretty solid! They've been paying attention.",
  "results": [
    {"question": "...", "chosen": 0, "correct": 0, "quip": "You clearly know them well!"},
    ...
  ],
  "leaderboard": [
    {"player_name": "Jordan", "score": 4}
  ]
}
```

---

## Evaluate roast quality

```bash
python eval_roasts.py
```

Generates quizzes for 3 sample creators and prints all questions + both roast
lines (quip_right and quip_wrong). Edit `SYSTEM_PROMPT` in `ai.py` and re-run
to tune the humor.

---

## Run tests

```bash
pytest tests/ -v
```

Tests cover:
- Scoring logic (all-correct, all-wrong, mixed, edge cases)
- Safe JSON parsing and code-fence stripping

---

## Switch to Sonnet

In `ai.py`, change the top-of-file constant:

```python
MODEL = "claude-sonnet-4-6"
```

No other changes needed.
