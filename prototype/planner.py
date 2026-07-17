import json
from typing import Any

from config import settings
from llm import llm
from memory import (
    add_message,
    add_tool_run,
    get_messages,
)
from models import PlannerAction
from tool_runner import run_tool


SYSTEM_PROMPT = """
You are a local AI assistant for AUTHORIZED
penetration-testing labs, CTFs, and systems for
which the user has explicit permission.

Your job is to orchestrate reconnaissance and
vulnerability-scanning tools.

AVAILABLE TOOLS:

1. nmap

Purpose:
- Discover open ports.
- Identify network services.

Arguments:

{
  "scan_type": "quick" | "service" | "full",
  "ports": optional string
}


2. httpx

Purpose:
- Confirm HTTP/HTTPS services.
- Obtain HTTP status.
- Obtain page title.
- Detect web technologies.

Arguments:

{
  "url": optional URL
}


3. whatweb

Purpose:
- Fingerprint web technologies.

Arguments:

{
  "url": optional URL
}


4. nuclei

Purpose:
- Run vulnerability templates against the
  authorized web target.

Arguments:

{
  "url": optional URL,
  "severity": optional comma-separated severity
}


5. ffuf

Purpose:
- Discover web content on the authorized target.

Arguments:

{
  "url": optional URL,
  "wordlist": optional filesystem path
}


IMPORTANT RULES:

- Use only the authorized target.
- Never invent another target.
- Never escape the authorized target.
- Never generate arbitrary shell commands.
- Never request arbitrary command execution.
- Do not attempt exploitation.
- Do not attempt persistence.
- Do not attempt credential theft.
- Use only the provided tools.
- Analyze actual tool output before choosing
  another tool.
- Never repeat an identical tool action that has
  already been executed.
- If a tool failed, analyze why before deciding
  whether another tool is appropriate.
- If an HTTP URL contains an explicit port,
  preserve that port.
- Do not repeatedly run Nmap after the target
  service has already been identified.
- Finish when enough evidence exists to answer
  the user's request.


YOU MUST RETURN EXACTLY ONE JSON OBJECT.

DO NOT return:
- a list
- a "steps" object
- multiple actions
- Markdown around the JSON


To execute ONE tool:

{
  "action": "tool",
  "tool": "nmap",
  "arguments": {
    "scan_type": "service"
  },
  "reasoning": "Need to identify exposed services.",
  "response": ""
}


To finish:

{
  "action": "finish",
  "tool": null,
  "arguments": {},
  "reasoning": "Enough evidence has been collected.",
  "response": "Final analysis for the user."
}
""".strip()


def build_planner_messages(
    session_id: str,
    target: str,
    user_message: str,
    execution_history: list[dict[str, Any]],
) -> list[dict[str, str]]:

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "system",
            "content": (
                "AUTHORIZED TARGET FOR THIS "
                f"SESSION:\n{target}\n\n"
                "All tool actions must remain "
                "within this target.\n\n"
                "When using web tools, preserve "
                "the complete URL including any "
                "explicit port."
            ),
        },
    ]

    conversation = get_messages(
        session_id,
        limit=20,
    )

    messages.extend(conversation)

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    if execution_history:
        messages.append(
            {
                "role": "system",
                "content": (
                    "TOOL EXECUTION HISTORY:\n\n"
                    + json.dumps(
                        execution_history,
                        indent=2,
                    )
                    + "\n\n"
                    "IMPORTANT: Do not repeat an "
                    "identical tool action already "
                    "present in this history."
                ),
            }
        )

    return messages


def parse_action(
    data: dict[str, Any],
) -> PlannerAction:
    """
    Validate the LLM planner response.

    The planner must return exactly one
    PlannerAction object.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Planner response must be "
            "a JSON object."
        )

    if "action" not in data:
        raise ValueError(
            "Planner response is missing "
            "the 'action' field."
        )

    return PlannerAction.model_validate(
        data
    )


def create_action_key(
    tool: str,
    arguments: dict[str, Any],
) -> str:
    """
    Create a stable identifier for a tool action.

    This prevents the LLM from repeatedly
    executing the exact same tool request.
    """

    return json.dumps(
        {
            "tool": tool,
            "arguments": arguments,
        },
        sort_keys=True,
    )


def get_planner_action(
    messages: list[dict[str, str]],
) -> PlannerAction:
    """
    Ask the LLM for a planner action.

    If the model returns an invalid schema,
    retry once with an explicit correction.
    """

    try:
        raw_action = llm.chat_json(
            messages
        )

        return parse_action(
            raw_action
        )

    except Exception as first_error:

        retry_messages = list(
            messages
        )

        retry_messages.append(
            {
                "role": "system",
                "content": (
                    "Your previous response did "
                    "not match the required JSON "
                    "schema.\n\n"
                    "Return exactly ONE object "
                    "with an 'action' field.\n\n"
                    "Valid actions are:\n"
                    '"action": "tool"\n'
                    "or\n"
                    '"action": "finish"\n\n'
                    "Do not return a 'steps' "
                    "object or an array."
                ),
            }
        )

        try:
            raw_action = llm.chat_json(
                retry_messages
            )

            return parse_action(
                raw_action
            )

        except Exception as second_error:
            raise RuntimeError(
                "Planner returned invalid JSON "
                "schema after retry.\n"
                f"First error: {first_error}\n"
                f"Second error: {second_error}"
            ) from second_error


def run_agent(
    session_id: str,
    target: str,
    user_message: str,
) -> tuple[
    str,
    list[dict[str, Any]],
]:

    add_message(
        session_id,
        "user",
        user_message,
    )

    execution_history: list[
        dict[str, Any]
    ] = []

    executed_actions: set[str] = set()

    final_response = ""

    for step_number in range(
        1,
        settings.max_agent_steps + 1,
    ):

        messages = build_planner_messages(
            session_id=session_id,
            target=target,
            user_message=user_message,
            execution_history=(
                execution_history
            ),
        )

        try:
            action = get_planner_action(
                messages
            )

        except Exception as exc:
            final_response = (
                "The planning model could not "
                "produce a valid next action.\n\n"
                f"Error: {exc}"
            )

            break

        # ---------------------------------
        # Agent finished
        # ---------------------------------

        if action.action == "finish":

            final_response = (
                action.response
                or
                "Reconnaissance completed."
            )

            break

        # ---------------------------------
        # Validate tool action
        # ---------------------------------

        if not action.tool:

            final_response = (
                "The planner requested a tool "
                "action without specifying "
                "a tool."
            )

            break

        # ---------------------------------
        # Duplicate action protection
        # ---------------------------------

        action_key = create_action_key(
            action.tool,
            action.arguments,
        )

        if action_key in executed_actions:

            execution_history.append(
                {
                    "step": step_number,
                    "reasoning": (
                        action.reasoning
                    ),
                    "duplicate_action": True,
                    "message": (
                        "This exact tool action "
                        "was already executed. "
                        "Choose another tool, "
                        "change the arguments, "
                        "or finish."
                    ),
                }
            )

            continue

        executed_actions.add(
            action_key
        )

        # ---------------------------------
        # Execute tool
        # ---------------------------------

        result = run_tool(
            tool_name=action.tool,
            target=target,
            arguments=action.arguments,
        )

        result_data = (
            result.model_dump()
        )

        # ---------------------------------
        # Store result
        # ---------------------------------

        add_tool_run(
            session_id=session_id,
            target=target,
            result=result_data,
        )

        execution_history.append(
            {
                "step": step_number,
                "reasoning": (
                    action.reasoning
                ),
                "tool": action.tool,
                "arguments": (
                    action.arguments
                ),
                "tool_result": (
                    result_data
                ),
            }
        )

    else:

        final_response = (
            "The maximum number of agent "
            "steps was reached.\n\n"
            "The reconnaissance results were "
            "collected, but the planner did "
            "not produce a final response."
        )

    if not final_response:

        final_response = (
            "The task ended without a "
            "final model response."
        )

    add_message(
        session_id,
        "assistant",
        final_response,
    )

    return (
        final_response,
        execution_history,
    )
