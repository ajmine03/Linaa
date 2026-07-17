from datetime import datetime, timezone
from pathlib import Path

from config import settings
from llm import llm
from memory import (
    get_messages,
    get_tool_runs,
)


REPORT_SYSTEM_PROMPT = """
You are writing a penetration-testing
reconnaissance report for an authorized
security assessment.

Generate a concise Markdown report.

Use only evidence present in the supplied
conversation and tool outputs.

Do not invent vulnerabilities.

Use this structure:

# Security Assessment Report

## Target

## Executive Summary

## Reconnaissance

## Discovered Services

## Web Technologies

## Findings

For each finding include, when available:

- Title
- Severity
- Evidence
- Description
- Recommendation

## Content Discovery

## Limitations

## Conclusion

If a section has no evidence, state that
no confirmed information was collected.

Return Markdown only.
""".strip()


def build_report(
    session_id: str,
    target: str,
) -> str:
    messages = get_messages(
        session_id,
        limit=100,
    )

    tool_runs = get_tool_runs(
        session_id,
    )

    evidence_parts = [
        f"AUTHORIZED TARGET: {target}",
        "",
        "CONVERSATION:",
    ]

    for message in messages:
        evidence_parts.append(
            f"\n[{message['role'].upper()}]"
        )

        evidence_parts.append(
            message["content"]
        )

    evidence_parts.append(
        "\nTOOL RESULTS:"
    )

    for run in tool_runs:
        evidence_parts.extend(
            [
                "",
                f"Tool: {run['tool']}",
                (
                    "Command: "
                    + " ".join(
                        run["command"]
                        if isinstance(
                            run["command"],
                            list,
                        )
                        else [
                            str(
                                run[
                                    "command"
                                ]
                            )
                        ]
                    )
                ),
                (
                    "Success: "
                    f"{run['success']}"
                ),
                "STDOUT:",
                run.get(
                    "stdout",
                    "",
                ),
                "STDERR:",
                run.get(
                    "stderr",
                    "",
                ),
            ]
        )

    evidence = "\n".join(
        evidence_parts
    )

    markdown = llm.chat(
        [
            {
                "role": "system",
                "content": (
                    REPORT_SYSTEM_PROMPT
                ),
            },
            {
                "role": "user",
                "content": evidence,
            },
        ]
    )

    return markdown


def save_report(
    session_id: str,
    target: str,
) -> Path:
    markdown = build_report(
        session_id,
        target,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    safe_session = "".join(
        char
        if char.isalnum()
        or char in "-_"
        else "_"
        for char in session_id
    )

    filename = (
        f"{safe_session}_"
        f"{timestamp}.md"
    )

    path = (
        Path(settings.report_dir)
        / filename
    )

    path.write_text(
        markdown,
        encoding="utf-8",
    )

    return path