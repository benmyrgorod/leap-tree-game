"""Story response model returned by the AI provider."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class StoryResponse(BaseModel):
    """Validated continuation payload rendered by the CLI."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    story: str
    option_a: str
    option_b: str

    @field_validator("story", "option_a", "option_b")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()


def parse_story_response(raw: Any) -> StoryResponse:
    """Parse provider output into the story response contract."""

    if isinstance(raw, StoryResponse):
        return raw

    if isinstance(raw, dict):
        return StoryResponse.model_validate(raw)

    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise ValueError("The model returned an empty response.")
        try:
            return StoryResponse.model_validate_json(text)
        except ValidationError:
            json_text = _extract_first_json_object(text)
            if json_text is None:
                raise
            return StoryResponse.model_validate_json(json_text)
        except json.JSONDecodeError:
            json_text = _extract_first_json_object(text)
            if json_text is None:
                raise
            return StoryResponse.model_validate_json(json_text)

    return StoryResponse.model_validate(raw)


def _extract_first_json_object(text: str) -> str | None:
    """Best-effort recovery for models that wrap JSON in prose or fences."""

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced_match:
        return fenced_match.group(1)

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None
