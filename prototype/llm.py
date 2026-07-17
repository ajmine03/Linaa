import json
from typing import Any

import requests

from config import settings


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (
            base_url
            or settings.ollama_base_url
        ).rstrip("/")

        self.model = (
            model
            or settings.ollama_model
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        json_mode: bool = False,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        if json_mode:
            payload["format"] = "json"

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=600,
        )

        response.raise_for_status()

        data = response.json()

        return data["message"]["content"]

    def chat_json(
        self,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        content = self.chat(
            messages=messages,
            json_mode=True,
        )

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "LLM returned invalid JSON: "
                f"{content}"
            ) from exc

    def is_available(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )

            return response.ok

        except requests.RequestException:
            return False


llm = OllamaClient()