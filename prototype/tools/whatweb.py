from typing import Any

from tools.common import normalize_url


def build_command(
    target: str,
    arguments: dict[str, Any],
) -> list[str]:
    url = arguments.get(
        "url",
        target,
    )

    url = normalize_url(url)

    return [
        "whatweb",
        "--color=never",
        url,
    ]