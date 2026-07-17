from typing import Any, Literal

from pydantic import BaseModel, Field


ToolName = Literal[
    "nmap",
    "httpx",
    "whatweb",
    "nuclei",
    "ffuf",
]


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    target: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    target: str
    response: str
    steps: list[dict[str, Any]] = Field(default_factory=list)


class PlannerAction(BaseModel):
    action: Literal["tool", "finish"]

    tool: ToolName | None = None

    arguments: dict[str, Any] = Field(
        default_factory=dict
    )

    reasoning: str = ""

    response: str = ""


class ToolResult(BaseModel):
    tool: str
    command: list[str]

    success: bool

    return_code: int | None = None

    stdout: str = ""
    stderr: str = ""

    error: str | None = None

    duration: float = 0.0


class ReportRequest(BaseModel):
    session_id: str
    target: str