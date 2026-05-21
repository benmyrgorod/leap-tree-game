"""Pydantic AI provider integration hidden behind a local story client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import ValidationError

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.game.prompts import build_initial_prompt, build_next_prompt
from leap_tree_game.game.state import Choice, GameSetup, GameState
from leap_tree_game.models.story import StoryResponse, parse_story_response


class StoryGenerationError(RuntimeError):
    """Recoverable story generation failure with a player-facing message."""

    def __init__(self, message: str, *, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original


class RunsSync(Protocol):
    def run_sync(self, prompt: str) -> Any:
        ...


def create_story_agent(settings: ProviderSettings):
    """Return a configured Pydantic AI agent for `StoryResponse` output."""

    try:
        from pydantic_ai import Agent
    except ImportError as exc:
        raise StoryGenerationError(
            "Pydantic AI is not installed. Run `python3 -m pip install -r requirements.txt`.",
            original=exc,
        ) from exc

    model = _create_model(settings)
    return Agent(model=model, output_type=_output_type(settings))


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
    if settings.provider == "ollama" and not settings.uses_ollama_cloud:
        try:
            from pydantic_ai.output import NativeOutput
        except ImportError:
            return StoryResponse

        return NativeOutput(StoryResponse)

    return StoryResponse


@dataclass
class StoryClient:
    settings: ProviderSettings
    agent: RunsSync | None = None

    def generate_initial(self, setup: GameSetup) -> StoryResponse:
        return self.generate(build_initial_prompt(setup))

    def generate_next(self, state: GameState, choice: Choice) -> StoryResponse:
        return self.generate(build_next_prompt(state, choice))

    def generate(self, prompt: str) -> StoryResponse:
        agent = self.agent or create_story_agent(self.settings)
        try:
            result = agent.run_sync(prompt)
            raw_output = getattr(result, "output", result)
            return parse_story_response(raw_output)
        except StoryGenerationError:
            raise
        except (ValidationError, ValueError, TypeError) as exc:
            raise StoryGenerationError(
                "The model response was not valid story JSON. You can retry or switch models.",
                original=exc,
            ) from exc
        except Exception as exc:
            raise _translate_exception(exc) from exc


def _translate_exception(exc: Exception) -> StoryGenerationError:
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
