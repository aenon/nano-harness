"""State management with SQLite checkpointing."""
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TaskRecord:
    """A task execution record."""
    id: int
    task: str
    round: int
    prompt: str
    response: str
    tool_calls: str  # JSON
    timestamp: str


class State:
    """SQLite-backed state management."""

    def __init__(self, db_path: str = "nano_harness.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                round INTEGER DEFAULT 0,
                prompt TEXT NOT NULL,
                response TEXT,
                tool_calls TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_round(
        self,
        task: str,
        round_num: int,
        prompt: str,
        response: str,
        tool_calls: list[dict],
    ) -> None:
        """Save a round of execution."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO tasks (task, round, prompt, response, tool_calls, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task,
                round_num,
                prompt,
                response,
                json.dumps(tool_calls),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def get_history(self, task: str, limit: int = 10) -> list[TaskRecord]:
        """Get task execution history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT id, task, round, prompt, response, tool_calls, timestamp
            FROM tasks
            WHERE task = ?
            ORDER BY round DESC
            LIMIT ?
            """,
            (task, limit),
        )
        records = [TaskRecord(**dict(row)) for row in cursor.fetchall()]
        conn.close()
        return records

    def clear(self, task: Optional[str] = None) -> None:
        """Clear task history."""
        conn = sqlite3.connect(self.db_path)
        if task:
            conn.execute("DELETE FROM tasks WHERE task = ?", (task,))
        else:
            conn.execute("DELETE FROM tasks")
        conn.commit()
        conn.close()


# Default state instance
_state: Optional[State] = None


def get_state(db_path: str = "nano_harness.db") -> State:
    """Get the default state instance."""
    global _state
    if _state is None:
        _state = State(db_path)
    return _state