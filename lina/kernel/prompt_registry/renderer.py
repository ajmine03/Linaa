"""Safe template rendering: strict variable substitution with validation.

Uses Python's built-in string.Template (not str.format / f-strings) to
avoid accidental code-injection surface from user-controlled variable
content, and to give predictable ${var} syntax across all plugin prompts.
"""

from __future__ import annotations

from string import Template
from typing import Any

from kernel.ports.prompt_registry import PromptTemplate


class PromptRenderError(Exception):
    """Raised when required template variables are missing or malformed."""


class TemplateRenderer:
    def render(self, template: PromptTemplate, variables: dict[str, Any]) -> str:
        missing = [v for v in template.input_variables if v not in variables]
        if missing:
            raise PromptRenderError(
                f"Missing required variables for prompt '{template.key}' "
                f"v{template.version}: {missing}"
            )
        try:
            return Template(template.template).substitute(
                {k: str(v) for k, v in variables.items()}
            )
        except KeyError as exc:
            raise PromptRenderError(
                f"Template references undeclared variable {exc} in prompt '{template.key}'."
            ) from exc