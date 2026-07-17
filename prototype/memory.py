import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                target TEXT NOT NULL,
                tool TEXT NOT NULL,
                command TEXT NOT NULL,
                success INTEGER NOT NULL,
                return_code INTEGER,
                stdout TEXT,
                stderr TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.commit()


def add_message(
    session_id: str,
    role: str,
    content: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (
                session_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                utc_now(),
            ),
        )

        conn.commit()


def get_messages(
    session_id: str,
    limit: int = 30,
) -> list[dict[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                session_id,
                limit,
            ),
        ).fetchall()

    rows = list(reversed(rows))

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows
    ]


def add_tool_run(
    session_id: str,
    target: str,
    result: dict[str, Any],
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tool_runs (
                session_id,
                target,
                tool,
                command,
                success,
                return_code,
                stdout,
                stderr,
                error,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                target,
                result["tool"],
                json.dumps(result["command"]),
                int(result["success"]),
                result.get("return_code"),
                result.get("stdout", ""),
                result.get("stderr", ""),
                result.get("error"),
                utc_now(),
            ),
        )

        conn.commit()


def get_tool_runs(
    session_id: str,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM tool_runs
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    results = []

    for row in rows:
        item = dict(row)

        try:
            item["command"] = json.loads(
                item["command"]
            )
        except json.JSONDecodeError:
            pass

        item["success"] = bool(
            item["success"]
        )

        results.append(item)

    return results


def clear_session(
    session_id: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM messages
            WHERE session_id = ?
            """,
            (session_id,),
        )

        conn.execute(
            """
            DELETE FROM tool_runs
            WHERE session_id = ?
            """,
            (session_id,),
        )

        conn.commit()


init_db()