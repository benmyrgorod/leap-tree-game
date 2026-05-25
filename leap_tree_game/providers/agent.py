"""Pydantic AI provider integration hidden behind a local story client."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, TypeVar

from pydantic import ValidationError

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.prompts import (
    build_ascii_art_prompt,
    build_initial_prompt,
    build_next_prompt,
    build_openings_prompt,
    build_storybook_prompt,
)
from leap_tree_game.game.state import Choice, GameSetup, GameState
from leap_tree_game.models.story import (
    OpeningSuggestions,
    StoryResponse,
    parse_opening_suggestions,
    parse_story_response,
)
from leap_tree_game.telemetry import logfire_event, logfire_span


class StoryGenerationError(RuntimeError):
    """Recoverable story generation failure with a player-facing message."""

    def __init__(self, message: str, *, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original


T = TypeVar("T")


class RunsSync(Protocol):
    def run_sync(self, prompt: str) -> Any:
        ...


@dataclass
class TokenUsage:
    """Normalized token counters tracked across model calls."""

    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def add(self, raw: dict[str, int] | Any) -> None:
        raw_usage = _extract_usage(raw)
        self.requests += raw_usage.get("requests", 0)
        self.input_tokens += raw_usage.get("input_tokens", 0)
        self.output_tokens += raw_usage.get("output_tokens", 0)
        self.cache_read_tokens += raw_usage.get("cache_read_tokens", 0)
        self.cache_write_tokens += raw_usage.get("cache_write_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def summary(self) -> str:
        return (
            f"input={self.input_tokens}, output={self.output_tokens}, total={self.total_tokens}"
        )


_PYDANTIC_AI_NOT_INSTALLED = (
    "Pydantic AI is not installed. Run `python3 -m pip install -r requirements.txt`."
)


def create_story_agent(settings: ProviderSettings):
    """Return a configured Pydantic AI agent for `StoryResponse` output."""

    return _create_agent(settings, output_type=_output_type(settings))


def create_ascii_agent(settings: ProviderSettings):
    """Return a configured Pydantic AI agent for plain-text (ASCII) output."""

    return _create_agent(settings)


def create_openings_agent(settings: ProviderSettings):
    """Return a configured Pydantic AI agent for opening suggestions."""

    return _create_agent(settings, output_type=_openings_output_type(settings))


def _create_agent(settings: ProviderSettings, output_type: Any | None = None):
    agent_factory = _load_pydantic_agent()
    model = _create_model(settings)
    if output_type is None:
        return agent_factory(model=model)
    return agent_factory(model=model, output_type=output_type)


def _load_pydantic_agent():
    try:
        from pydantic_ai import Agent
        return Agent
    except ImportError as exc:
        raise StoryGenerationError(
            _PYDANTIC_AI_NOT_INSTALLED,
            original=exc,
        ) from exc


def _create_model(settings: ProviderSettings):
    if settings.provider == "openai":
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        return OpenAIChatModel(
            settings.model,
            provider=OpenAIProvider(api_key=settings.openai_api_key),
        )

    if settings.provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider
        return AnthropicModel(
            settings.model,
            provider=AnthropicProvider(api_key=settings.anthropic_api_key),
        )

    from pydantic_ai.models.ollama import OllamaModel
    from pydantic_ai.providers.ollama import OllamaProvider
    return OllamaModel(
        settings.model,
        provider=OllamaProvider(
            base_url=settings.ollama_base_url,
            api_key=settings.ollama_api_key,
        ),
    )


def _output_type(settings: ProviderSettings):
    return _structured_output_type(settings, StoryResponse)


def _openings_output_type(settings: ProviderSettings):
    return _structured_output_type(settings, OpeningSuggestions)


def _structured_output_type(settings: ProviderSettings, output_model):
    if settings.provider == "ollama" and not settings.uses_ollama_cloud:
        try:
            from pydantic_ai.output import NativeOutput
        except ImportError:
            return output_model

        return NativeOutput(output_model)

    return output_model


def _minimum_opening_count(count: int) -> int:
    return max(1, min(3, count))


@dataclass
class StoryClient:
    settings: ProviderSettings
    agent: RunsSync | None = None
    ascii_agent: RunsSync | None = None
    openings_agent: RunsSync | None = None
    token_usage: TokenUsage = field(default_factory=TokenUsage)

    def generate_initial(
        self,
        setup: GameSetup,
        *,
        avoid_continuations: tuple[str, str] | None = None,
        language: str | None = None,
    ) -> StoryResponse:
        response = self.generate(
            build_initial_prompt(
                setup,
                avoid_continuations=avoid_continuations,
                language=language,
            )
        )
        return _with_canonical_story(response, setup.opening)

    def generate_next(
        self,
        state: GameState,
        choice: Choice,
        *,
        avoid_continuations: tuple[str, str] | None = None,
        language: str | None = None,
    ) -> StoryResponse:
        response = self.generate(
            build_next_prompt(
                state,
                choice,
                avoid_continuations=avoid_continuations,
                language=language,
            )
        )
        return _with_canonical_story(response, state.current_story())

    def generate_storybook(
        self,
        source_story: str,
        *,
        correction_notes: str | None = None,
        genre: str | None = None,
        setting: str | None = None,
        opening: str | None = None,
        normality_level: str | None = None,
        language_level: str | None = None,
        language: str | None = None,
    ) -> str:
        return self._run_with_generation_errors(
            lambda: _coerce_story_text(
                self._run_sync(
                    build_storybook_prompt(
                        source_story=source_story,
                        correction_notes=correction_notes,
                        genre=genre,
                        setting=setting,
                        opening=opening,
                        normality_level=normality_level,
                        language_level=language_level,
                        language=language,
                    ),
                    output_kind="story_text",
                )
            ),
            "The model did not return usable story text.",
        )

    def generate(
        self,
        prompt: str,
    ) -> StoryResponse:
        return self._run_with_generation_errors(
            lambda: parse_story_response(
                self._run_sync(prompt, output_kind="story")
            ),
            "The model response was not valid story JSON. You can retry or switch models.",
        )

    def verify_connection(self) -> None:
        """Run a small provider request to ensure API access is available."""
        verification_prompt = (
            "Return exactly this JSON object and nothing else:\n"
            '{"story":"ok","option_a":"continue","option_b":"reset"}'
        )
        self._run_with_generation_errors(
            lambda: parse_story_response(
                self._run_sync(
                    verification_prompt,
                    output_kind="connection",
                )
            ),
            "LLM connection check failed. Please verify your API settings and network.",
        )

    def generate_ascii_art(
        self,
        story: str,
        *,
        genre: str | None = None,
        setting: str | None = None,
        language: str | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> str:
        return self._run_with_generation_errors(
            lambda: _coerce_ascii_art(
                self._run_sync(
                    build_ascii_art_prompt(
                        story,
                        genre=genre,
                        setting=setting,
                        language=language,
                        width=width,
                        height=height,
                    ),
                    output_kind="ascii",
                ),
                target_width=width,
                target_height=height,
            ),
            "The model did not return usable ASCII art.",
        )

    def generate_openings(
        self,
        *,
        genre: str,
        setting: str,
        normality_level: str = "Balanced",
        language_level: str = "Conversational",
        count: int = 11,
        language: str | None = None,
    ) -> list[str]:
        raw_output = self._run_with_generation_errors(
            lambda: parse_opening_suggestions(
                self._run_sync(
                    build_openings_prompt(
                        genre=genre,
                        setting=setting,
                        normality_level=normality_level,
                        language_level=language_level,
                        count=count,
                        language=language,
                    ),
                    output_kind="openings",
                )
            ).openings,
            "The model did not return usable opening choices.",
        )
        openings = raw_output
        if len(openings) > count:
            openings = openings[:count]
        if len(openings) < _minimum_opening_count(count):
            raise StoryGenerationError("The model returned too few opening choices.")
        return openings

    @property
    def total_tokens(self) -> int:
        return self.token_usage.total_tokens

    @property
    def total_input_tokens(self) -> int:
        return self.token_usage.input_tokens

    @total_input_tokens.setter
    def total_input_tokens(self, value: int) -> None:
        self.token_usage.input_tokens = value

    @property
    def total_output_tokens(self) -> int:
        return self.token_usage.output_tokens

    @total_output_tokens.setter
    def total_output_tokens(self, value: int) -> None:
        self.token_usage.output_tokens = value

    @property
    def total_cache_read_tokens(self) -> int:
        return self.token_usage.cache_read_tokens

    @total_cache_read_tokens.setter
    def total_cache_read_tokens(self, value: int) -> None:
        self.token_usage.cache_read_tokens = value

    @property
    def total_cache_write_tokens(self) -> int:
        return self.token_usage.cache_write_tokens

    @total_cache_write_tokens.setter
    def total_cache_write_tokens(self, value: int) -> None:
        self.token_usage.cache_write_tokens = value

    @property
    def total_requests(self) -> int:
        return self.token_usage.requests

    @total_requests.setter
    def total_requests(self, value: int) -> None:
        self.token_usage.requests = value

    def token_usage_summary(self) -> str:
        return self.token_usage.summary()

    def _run_sync(
        self,
        prompt: str,
        *,
        output_kind: Literal["story", "ascii", "openings", "story_text", "connection"] = "story",
    ):
        agent = self._agent_for_output(output_kind)
        logfire_event(
            "story_client.request",
            output_kind=output_kind,
            prompt=prompt,
        )
        with logfire_span(f"story_client.run_sync.{output_kind}"):
            result = agent.run_sync(prompt)
        response_object = getattr(result, "output", result)
        response_payload = _serialize_for_log(response_object)
        logfire_event(
            "story_client.response",
            output_kind=output_kind,
            status="ok",
            output_type=type(response_object).__name__,
            response=response_payload,
        )
        self.token_usage.add(result)
        return getattr(result, "output", result)

    def _run_with_generation_errors(
        self,
        operation: Callable[[], T],
        error_message: str,
    ) -> T:
        try:
            return operation()
        except StoryGenerationError:
            raise
        except (ValidationError, ValueError, TypeError) as exc:
            raise StoryGenerationError(
                error_message,
                original=exc,
            ) from exc
        except Exception as exc:
            raise _translate_exception(
                exc,
                provider=self.settings.provider,
                model=self.settings.model,
            ) from exc

    def _agent_for_output(
        self,
        output_kind: Literal["story", "ascii", "openings", "story_text", "connection"],
    ):
        if output_kind == "openings":
            if self.openings_agent is None:
                self.openings_agent = create_openings_agent(self.settings)
            return self.openings_agent

        if output_kind in {"ascii", "story_text"}:
            if self.ascii_agent is None:
                self.ascii_agent = create_ascii_agent(self.settings)
            return self.ascii_agent

        if self.agent is None:
            self.agent = create_story_agent(self.settings)
        return self.agent


def _translate_exception(
    exc: Exception,
    *,
    provider: str | None = None,
    model: str | None = None,
) -> StoryGenerationError:
    message = str(exc)
    lower_message = message.lower()

    if "api key" in lower_message or "authentication" in lower_message or "unauthorized" in lower_message:
        return StoryGenerationError(
            "The provider rejected the API key. Rerun setup or update `.env`.",
            original=exc,
        )
    if "rate limit" in lower_message or "429" in lower_message:
        return StoryGenerationError(
            "The provider rate limit was reached. Wait a moment, retry, or switch models.",
            original=exc,
        )
    if (
        "status_code: 404" in lower_message
        and "model_name" in lower_message
        and ("does not exist" in lower_message or "not found" in lower_message)
    ):
        model_name = _extract_quoted_model_name(message) or model or "configured model"
        provider_name = provider or "provider"
        return StoryGenerationError(
            f"The configured model '{model_name}' is not available for {provider_name} in your account. "
            "Choose a different model in setup and retry.",
            original=exc,
        )
    if (
        "connection" in lower_message
        or "network" in lower_message
        or "timeout" in lower_message
        or "connecterror" in lower_message
    ):
        return StoryGenerationError(
            "The provider could not be reached. Check your network or Ollama server, then retry.",
            original=exc,
        )
    if not message.strip():
        return StoryGenerationError("The provider returned an empty error. Please retry.", original=exc)

    return StoryGenerationError(
        f"Story generation failed: {message}",
        original=exc,
    )


def _extract_usage(result: Any) -> dict[str, int]:
    raw = getattr(result, "usage", None)
    if callable(raw):
        raw = raw()
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {
            "requests": int(raw.get("requests", 0)),
            "input_tokens": int(raw.get("input_tokens", 0)),
            "cache_write_tokens": int(raw.get("cache_write_tokens", 0)),
            "cache_read_tokens": int(raw.get("cache_read_tokens", 0)),
            "output_tokens": int(raw.get("output_tokens", 0)),
        }

    return {
        "requests": int(getattr(raw, "requests", 0)),
        "input_tokens": int(getattr(raw, "input_tokens", 0)),
        "cache_write_tokens": int(getattr(raw, "cache_write_tokens", 0)),
        "cache_read_tokens": int(getattr(raw, "cache_read_tokens", 0)),
        "output_tokens": int(getattr(raw, "output_tokens", 0)),
    }


def _serialize_for_log(value: object) -> object:
    if hasattr(value, "model_dump"):
        model_dump = getattr(value, "model_dump")
        if callable(model_dump):
            return model_dump()

    if hasattr(value, "dict"):
        dict_fn = getattr(value, "dict")
        if callable(dict_fn):
            try:
                return dict_fn()
            except TypeError:
                pass

    if isinstance(value, (dict, list, tuple, str, int, float, bool, type(None))):
        return value

    return str(value)


def _extract_quoted_model_name(message: str) -> str | None:
    match = re.search(r"model_name:\s*([`'\"]?)([^,\s]+)\1", message)
    return match.group(2) if match else None


def _with_canonical_story(response: StoryResponse, story: str) -> StoryResponse:
    return StoryResponse(story=story, option_a=response.option_a, option_b=response.option_b)


def _coerce_story_text(raw_output: object) -> str:
    if _is_story_response_text(raw_output):
        raise ValueError("Story text generation returned structured story JSON instead of plain text.")

    text = str(raw_output).strip()
    if not text:
        raise ValueError("Story text response was empty.")
    return _strip_code_fence(text)


def _coerce_ascii_art(
    raw_output: object,
    target_width: int | None = None,
    target_height: int | None = None,
) -> str:
    if _is_story_response_text(raw_output):
        raise ValueError("LLM returned structured story JSON instead of ASCII art.")
    text = str(raw_output).strip("\n\r")
    text = _strip_code_fence(text)
    if not text:
        raise ValueError("ASCII art response was empty.")
    if _contains_prose_lines(text):
        raise ValueError("ASCII art response contains prose text.")

    lines = text.splitlines()
    if target_width is not None and target_width > 0:
        lines = [line[:target_width].ljust(target_width) for line in lines]
        if target_height is None:
            target_height = 0
        while len(lines) < target_height:
            lines.append(" " * target_width)
        text = "\n".join(lines)

    if target_height is not None and target_height > 0 and len(lines) > target_height:
        lines = lines[:target_height]
        return "\n".join(lines).rstrip()

    return text


def _contains_prose_lines(text: str) -> bool:
    for line in text.splitlines():
        if re.search(r"[A-Za-z]{2,}", line):
            return True
    return False


def _is_story_response_text(raw_output: object) -> bool:
    if isinstance(raw_output, dict):
        keys = set(raw_output.keys())
        return {"story", "option_a", "option_b"} <= keys
    if all(
        hasattr(raw_output, attr)
        for attr in ("story", "option_a", "option_b")
    ):
        return True

    text = str(raw_output)
    return (
        text.startswith("story=")
        and "option_a=" in text
        and "option_b=" in text
    )


def _strip_code_fence(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    if not lines[0].lstrip().startswith("```"):
        return text

    if len(lines) < 3:
        return "\n".join(lines).strip("` \n\r")

    if not lines[-1].lstrip().startswith("```"):
        return "\n".join(lines).strip("` \n\r")

    return "\n".join(lines[1:-1]).strip("\n\r")
