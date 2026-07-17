import ipaddress
import re
from urllib.parse import urlparse


HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?:"
    r"[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}"
    r"[a-zA-Z0-9])?"
    r"\.)*"
    r"[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}"
    r"[a-zA-Z0-9])?$"
)


def normalize_host(
    target: str,
) -> str:
    target = target.strip()

    if not target:
        raise ValueError(
            "Target cannot be empty."
        )

    if "://" in target:
        parsed = urlparse(target)
        host = parsed.hostname

        if not host:
            raise ValueError(
                "Invalid target URL."
            )

        return host

    # Remove a simple :port suffix.
    if (
        target.count(":") == 1
        and target.rsplit(":", 1)[1].isdigit()
    ):
        target = target.rsplit(
            ":",
            1,
        )[0]

    return target


def validate_host(
    target: str,
) -> str:
    host = normalize_host(target)

    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    if not HOSTNAME_RE.match(host):
        raise ValueError(
            f"Invalid hostname: {host}"
        )

    return host


def normalize_url(
    target: str,
) -> str:
    target = target.strip()

    if target.startswith(
        ("http://", "https://")
    ):
        parsed = urlparse(target)

        if not parsed.hostname:
            raise ValueError(
                "Invalid URL."
            )

        validate_host(parsed.hostname)

        return target.rstrip("/")

    host = validate_host(target)

    return f"http://{host}"