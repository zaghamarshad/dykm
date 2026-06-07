import secrets
import uuid

from flask import Flask, jsonify, render_template, request

from ai import generate_quiz
from storage import SQLiteBackend

app = Flask(__name__)
storage = SQLiteBackend("dykm.db")

SCORE_SUMMARIES = [
    (7, "They know you like the back of their hand!"),
    (5, "Pretty solid! They've been paying attention."),
    (3, "Half right… did they just guess?"),
    (1, "Yikes. Were they even trying?"),
    (0, "Complete stranger energy. Do they even know your name?"),
]


def _pick_summary(score: int) -> str:
    for threshold, line in SCORE_SUMMARIES:
        if score >= threshold:
            return line
    return SCORE_SUMMARIES[-1][1]


def _new_id() -> str:
    return secrets.token_urlsafe(6)[:6]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/q/<quiz_id>")
def play_quiz(quiz_id: str):
    quiz = storage.get_quiz(quiz_id)
    if quiz is None:
        return render_template("play.html", title="Quiz not found", description="This quiz doesn't exist.")
    theme = quiz.get("theme", "")
    description = f"{theme} · " if theme else ""
    description += f"{quiz['play_count']} people have played. Think you know them?"
    return render_template(
        "play.html",
        title=f"Do you know {quiz['creator_name']}?",
        description=description,
        url=request.url,
    )


@app.post("/quizzes")
def create_quiz():
    body = request.get_json(silent=True) or {}
    creator_name = body.get("creator_name", "").strip()
    answers = body.get("answers", [])
    pinned = body.get("pinned", [])
    theme = body.get("theme", "").strip()

    if not creator_name:
        return jsonify({"error": "creator_name is required"}), 400
    if not answers or not isinstance(answers, list):
        return jsonify({"error": "answers must be a non-empty list"}), 400

    try:
        questions = generate_quiz(creator_name, [str(a) for a in answers], theme, [str(p) for p in pinned])
    except Exception as e:
        return jsonify({"error": f"AI generation failed: {e}"}), 502

    quiz_id = _new_id()
    storage.create_quiz(quiz_id, creator_name, questions, theme)

    return jsonify({"id": quiz_id, "share_path": f"/q/{quiz_id}"}), 201


@app.get("/quizzes/<quiz_id>")
def get_quiz(quiz_id: str):
    quiz = storage.get_quiz(quiz_id)
    if quiz is None:
        return jsonify({"error": "Quiz not found"}), 404

    safe_questions = [
        {"text": q["text"], "options": q["options"]}
        for q in quiz["questions"]
    ]
    # correct_index and quips are intentionally stripped — never sent to players

    top_plays = storage.get_leaderboard(quiz_id)[:3]

    return jsonify({
        "id": quiz["id"],
        "creator_name": quiz["creator_name"],
        "theme": quiz.get("theme", ""),
        "play_count": quiz["play_count"],
        "top_plays": top_plays,
        "questions": safe_questions,
    })


@app.post("/quizzes/<quiz_id>/plays")
def submit_play(quiz_id: str):
    quiz = storage.get_quiz(quiz_id)
    if quiz is None:
        return jsonify({"error": "Quiz not found"}), 404

    body = request.get_json(silent=True) or {}
    player_name = body.get("player_name", "").strip()
    chosen = body.get("answers", [])

    if not player_name:
        return jsonify({"error": "player_name is required"}), 400

    questions = quiz["questions"]
    if not isinstance(chosen, list) or len(chosen) != len(questions):
        return jsonify({"error": f"answers must be a list of {len(questions)} integers"}), 400

    score = 0
    results = []
    for i, q in enumerate(questions):
        try:
            player_answer = int(chosen[i])
        except (TypeError, ValueError):
            return jsonify({"error": f"answers[{i}] must be an integer"}), 400

        if player_answer < 0 or player_answer >= len(q["options"]):
            return jsonify({"error": f"answers[{i}] must be 0–{len(q['options']) - 1}"}), 400

        correct = q["correct_index"]
        is_correct = player_answer == correct
        if is_correct:
            score += 1

        results.append({
            "question": q["text"],
            "chosen": player_answer,
            "correct": correct,
            "quip": q["quips"][player_answer],
        })

    play_id = str(uuid.uuid4())
    storage.save_play(play_id, quiz_id, player_name, score)
    storage.increment_play_count(quiz_id)

    leaderboard = storage.get_leaderboard(quiz_id)

    return jsonify({
        "score": score,
        "total": len(questions),
        "summary": _pick_summary(score),
        "results": results,
        "leaderboard": leaderboard,
    })


if __name__ == "__main__":
    app.run(debug=True)
