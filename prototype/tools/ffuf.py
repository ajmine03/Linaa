from typing import Any

from tools.common import normalize_url


DEFAULT_WORDLIST = (
    "/usr/share/wordlists/"
    "dirb/common.txt"
)


def build_command(
    target: str,
    arguments: dict[str, Any],
) -> list[str]:
    base_url = normalize_url(
        arguments.get(
            "url",
            target,
        )
    )

    wordlist = arguments.get(
        "wordlist",
        DEFAULT_WORDLIST,
    )

    if not isinstance(
        wordlist,
        str,
    ):
        raise ValueError(
            "Invalid wordlist."
        )

    # Wordlist paths are deliberately
    # constrained to normal filesystem paths.
    if "\x00" in wordlist:
        raise ValueError(
            "Invalid wordlist path."
        )

    fuzz_url = (
        base_url.rstrip("/")
        + "/FUZZ"
    )

    return [
        "ffuf",
        "-u",
        fuzz_url,
        "-w",
        wordlist,
        "-mc",
        "200,204,301,302,307,401,403",
        "-ac",
        "-s",
    ]