import shutil
import subprocess
import time
from typing import Any

from config import settings
from models import ToolResult
from tools import TOOL_BUILDERS


MAX_OUTPUT_CHARS = 30_000


def truncate(
    text: str,
    limit: int = MAX_OUTPUT_CHARS,
) -> str:
    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + "\n\n[OUTPUT TRUNCATED]"
    )


def run_tool(
    tool_name: str,
    target: str,
    arguments: dict[str, Any] | None = None,
) -> ToolResult:
    arguments = arguments or {}

    builder = TOOL_BUILDERS.get(
        tool_name
    )

    if builder is None:
        return ToolResult(
            tool=tool_name,
            command=[],
            success=False,
            error=(
                f"Unsupported tool: "
                f"{tool_name}"
            ),
        )

    try:
        command = builder(
            target,
            arguments,
        )

    except Exception as exc:
        return ToolResult(
            tool=tool_name,
            command=[],
            success=False,
            error=str(exc),
        )

    executable = command[0]

    if shutil.which(executable) is None:
        return ToolResult(
            tool=tool_name,
            command=command,
            success=False,
            error=(
                f"Executable not found: "
                f"{executable}"
            ),
        )

    started = time.monotonic()

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=settings.tool_timeout,
            shell=False,
        )

        duration = (
            time.monotonic()
            - started
        )

        return ToolResult(
            tool=tool_name,
            command=command,
            success=(
                process.returncode == 0
            ),
            return_code=process.returncode,
            stdout=truncate(
                process.stdout
            ),
            stderr=truncate(
                process.stderr
            ),
            duration=duration,
        )

    except subprocess.TimeoutExpired as exc:
        duration = (
            time.monotonic()
            - started
        )

        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode(
                errors="replace"
            )

        if isinstance(stderr, bytes):
            stderr = stderr.decode(
                errors="replace"
            )

        return ToolResult(
            tool=tool_name,
            command=command,
            success=False,
            stdout=truncate(stdout),
            stderr=truncate(stderr),
            error=(
                "Tool execution timed out."
            ),
            duration=duration,
        )

    except Exception as exc:
        duration = (
            time.monotonic()
            - started
        )

        return ToolResult(
            tool=tool_name,
            command=command,
            success=False,
            error=str(exc),
            duration=duration,
        )
