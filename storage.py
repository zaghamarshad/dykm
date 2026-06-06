import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class StorageBackend(ABC):
    @abstractmethod
    def create_quiz(self, id: str, creator_name: str, questions: list[dict]) -> None:
        ...

    @abstractmethod
    def get_quiz(self, id: str) -> dict | None:
        ...

    @abstractmethod
    def increment_play_count(self, id: str) -> None:
        ...

    @abstractmethod
    def save_play(self, id: str, quiz_id: str, player_name: str, score: int) -> None:
        ...

    @abstractmethod
    def get_leaderboard(self, quiz_id: str) -> list[dict]:
        ...


class SQLiteBackend(StorageBackend):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS quizzes (
                    id TEXT PRIMARY KEY,
                    creator_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    play_count INTEGER DEFAULT 0,
                    questions TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plays (
                    id TEXT PRIMARY KEY,
                    quiz_id TEXT NOT NULL,
                    player_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    def create_quiz(self, id: str, creator_name: str, questions: list[dict]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO quizzes (id, creator_name, created_at, play_count, questions) VALUES (?, ?, ?, 0, ?)",
                (id, creator_name, datetime.now(timezone.utc).isoformat(), json.dumps(questions)),
            )

    def get_quiz(self, id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM quizzes WHERE id = ?", (id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["questions"] = json.loads(data["questions"])
        return data

    def increment_play_count(self, id: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE quizzes SET play_count = play_count + 1 WHERE id = ?", (id,))

    def save_play(self, id: str, quiz_id: str, player_name: str, score: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO plays (id, quiz_id, player_name, score, created_at) VALUES (?, ?, ?, ?, ?)",
                (id, quiz_id, player_name, score, datetime.now(timezone.utc).isoformat()),
            )

    def get_leaderboard(self, quiz_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT player_name, score FROM plays WHERE quiz_id = ? ORDER BY score DESC",
                (quiz_id,),
            ).fetchall()
        return [dict(r) for r in rows]
