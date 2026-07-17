from contextlib import asynccontextmanager

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from rich.console import Console

from config import settings
from llm import llm
from memory import (
    clear_session,
    init_db,
)
from models import (
    ChatRequest,
    ChatResponse,
    ReportRequest,
)
from planner import run_agent
from report import save_report


cli = typer.Typer(
    help=(
        "Local AI security testing "
        "prototype."
    )
)

console = Console()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    init_db()
    yield


app = FastAPI(
    title="Local Pentest AI Prototype",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "ollama": llm.is_available(),
        "model": settings.ollama_model,
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
) -> ChatResponse:
    try:
        response, steps = run_agent(
            session_id=(
                request.session_id
            ),
            target=request.target,
            user_message=(
                request.message
            ),
        )

        return ChatResponse(
            session_id=(
                request.session_id
            ),
            target=request.target,
            response=response,
            steps=steps,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post("/report")
def create_report(
    request: ReportRequest,
) -> dict:
    try:
        path = save_report(
            session_id=(
                request.session_id
            ),
            target=request.target,
        )

        return {
            "report": str(path)
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.delete(
    "/session/{session_id}"
)
def delete_session(
    session_id: str,
) -> dict:
    clear_session(
        session_id
    )

    return {
        "status": "cleared",
        "session_id": session_id,
    }


@cli.command()
def serve(
    host: str = settings.api_host,
    port: int = settings.api_port,
):
    """Start the FastAPI server."""

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
    )


@cli.command()
def chat_cli(
    target: str = typer.Option(
        ...,
        help="Authorized target.",
    ),
    session: str = typer.Option(
        "cli-session",
        help="Conversation session ID.",
    ),
):
    """
    Start an interactive terminal
    conversation.
    """

    console.print(
        "[bold]Local Pentest AI Prototype[/bold]"
    )

    console.print(
        f"Authorized target: {target}"
    )

    console.print(
        "Type 'exit' to quit."
    )

    while True:
        message = console.input(
            "\n[bold cyan]You > [/bold cyan]"
        ).strip()

        if message.lower() in {
            "exit",
            "quit",
        }:
            break

        if not message:
            continue

        try:
            response, steps = run_agent(
                session_id=session,
                target=target,
                user_message=message,
            )

            for step in steps:
                result = step[
                    "tool_result"
                ]

                console.print(
                    "\n[dim]"
                    f"Tool: "
                    f"{result['tool']}"
                    "[/dim]"
                )

            console.print(
                "\n[bold green]"
                "Assistant >"
                "[/bold green]"
            )

            console.print(
                response
            )

        except Exception as exc:
            console.print(
                f"[red]Error: "
                f"{exc}[/red]"
            )


@cli.command()
def report(
    target: str = typer.Option(
        ...,
        help="Authorized target.",
    ),
    session: str = typer.Option(
        "cli-session",
    ),
):
    """Generate a Markdown report."""

    path = save_report(
        session_id=session,
        target=target,
    )

    console.print(
        f"Report saved to: {path}"
    )


@cli.command()
def check():
    """Check local dependencies."""

    console.print(
        f"Ollama URL: "
        f"{settings.ollama_base_url}"
    )

    console.print(
        f"Model: "
        f"{settings.ollama_model}"
    )

    if llm.is_available():
        console.print(
            "[green]Ollama is available."
            "[/green]"
        )
    else:
        console.print(
            "[red]Ollama is unavailable."
            "[/red]"
        )


if __name__ == "__main__":
    cli()