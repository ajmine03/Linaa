from typing import Any

from tools.common import normalize_url


def build_command(
    target: str,
    arguments: dict[str, Any],
) -> list[str]:
    """
    Build an httpx command while preserving
    the target URL scheme and explicit port.

    Example:
        http://127.0.0.1:3000

    remains:
        http://127.0.0.1:3000
    """

    url = arguments.get(
        "url",
        target,
    )

    url = normalize_url(url)

    return [
    "/home/ajmine/go/bin/httpx",
        "-u",
        url,
        "-silent",
        "-status-code",
        "-title",
        "-tech-detect",
        "-server",
        "-follow-redirects",
    ]
