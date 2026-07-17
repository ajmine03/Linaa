from typing import Any
from urllib.parse import urlparse

from tools.common import validate_host


def build_command(
    target: str,
    arguments: dict[str, Any],
) -> list[str]:
    """
    Build a safe Nmap command for the
    authorized target.

    If the target contains an explicit port,
    for example:

        http://127.0.0.1:3000

    Nmap will scan only port 3000 unless the
    planner explicitly supplies another port.
    """

    explicit_port = None

    # Extract host and port from URL.
    if "://" in target:
        parsed = urlparse(target)

        if not parsed.hostname:
            raise ValueError(
                "Invalid target URL."
            )

        host = validate_host(
            parsed.hostname
        )

        explicit_port = parsed.port

    else:
        host = validate_host(target)

    scan_type = arguments.get(
        "scan_type",
        "service",
    )

    requested_ports = arguments.get(
        "ports"
    )

    command = [
        "nmap",
        "-Pn",
    ]

    # Select scan mode.
    if scan_type == "quick":
        command.extend(
            [
                "-T4",
                "--top-ports",
                "100",
            ]
        )

    elif scan_type == "service":
        command.extend(
            [
                "-sV",
                "-T4",
            ]
        )

    elif scan_type == "full":
        command.extend(
            [
                "-sV",
                "-p-",
                "-T4",
            ]
        )

    else:
        command.extend(
            [
                "-sV",
                "-T4",
            ]
        )

    # Planner-supplied ports take priority.
    if requested_ports:
        port_string = str(
            requested_ports
        )

        allowed = set(
            "0123456789,-"
        )

        if not set(
            port_string
        ) <= allowed:
            raise ValueError(
                "Invalid port specification."
            )

        # Avoid conflicting -p- from full scan.
        if "-p-" in command:
            command.remove("-p-")

        command.extend(
            [
                "-p",
                port_string,
            ]
        )

    # Otherwise use explicit URL port.
    elif explicit_port:
        if "-p-" in command:
            command.remove("-p-")

        # Remove --top-ports because the user
        # explicitly supplied a target port.
        if "--top-ports" in command:
            index = command.index(
                "--top-ports"
            )

            del command[
                index:index + 2
            ]

        command.extend(
            [
                "-p",
                str(explicit_port),
            ]
        )

    command.append(host)

    return command
