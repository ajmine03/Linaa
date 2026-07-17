from typing import Any

from tools.common import normalize_url


ALLOWED_SEVERITIES = {
    "info",
    "low",
    "medium",
    "high",
    "critical",
}


def build_command(
    target: str,
    arguments: dict[str, Any],
) -> list[str]:
    url = normalize_url(
        arguments.get(
            "url",
            target,
        )
    )

    severity = arguments.get(
        "severity",
        "low,medium,high,critical",
    )

    values = {
        item.strip().lower()
        for item in str(
            severity
        ).split(",")
    }

    if not values:
        raise ValueError(
            "Severity cannot be empty."
        )

    if not values <= ALLOWED_SEVERITIES:
        raise ValueError(
            "Invalid nuclei severity."
        )

    severity_string = ",".join(
        sorted(values)
    )

    return [
        "nuclei",
        "-u",
        url,
        "-severity",
        severity_string,
        "-silent",
    ]