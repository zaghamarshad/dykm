# DYKM — Claude Code Context

## What this project is
A viral "Do You Know Me?" quiz app. Phase 1 is the backend only (Python/Flask).
The goal is to prove AI roasts are funny and the create/play/score flow works end-to-end.

## Phase 1 status: complete
All files are built and 15 tests pass. Run `python eval_roasts.py` to judge roast quality.

## File map
| File | Role |
|---|---|
| `app.py` | Flask app + 3 route handlers |
| `storage.py` | `StorageBackend` ABC + `SQLiteBackend` — all DB access lives here |
| `ai.py` | The ONE AI call. `MODEL` and `SYSTEM_PROMPT` are constants at the top |
| `eval_roasts.py` | Offline roast evaluator — 3 sample creators, prints questions + quips |
| `tests/test_core.py` | Scoring logic + JSON fence-stripping tests |

## Hard rules — do not break
1. **One AI call total.** Only `generate_quiz()` in `ai.py` touches the Anthropic API. Fetch, play, and scoring do zero AI calls.
2. **Scoring is plain Python.** Compare `player_answer == correct_index`. Never score via AI.
3. **Never leak answers.** `GET /quizzes/<id>` must strip `correct_index`, `quip_right`, and `quip_wrong` before responding.
4. **All DB access behind StorageBackend.** No raw `sqlite3` calls in `app.py`.

## Swapping the AI model
In `ai.py`, change the top-of-file constant:
```python
MODEL = "claude-sonnet-4-6"   # default is claude-haiku-4-5-20251001
```

## Swapping the database (SQLite → Firestore)
Add a `FirestoreBackend(StorageBackend)` class in `storage.py` and pass it to `app.py` at startup. No route handler changes needed.

## Running locally
```bash
source .venv/bin/activate
export ANTHROPIC_API_KEY=sk-ant-...
flask --app app run
```

## Running tests
```bash
pytest tests/ -v
```

## Evaluating roast quality
```bash
python eval_roasts.py
```
Edit `SYSTEM_PROMPT` in `ai.py`, then re-run to iterate on humor tone.

## Phase 2 (not started)
iOS app or web frontend. The backend API is the contract — don't change endpoint shapes without updating the client.
