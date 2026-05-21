"""Interactive `.env` setup wizard."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from leap_tree_game.config.settings import (
    DEFAULT_MODELS,
    DEFAULT_OLLAMA_BASE_URL,
    ProviderName,
    ProviderSettings,
    SUPPORTED_PROVIDERS,
    write_env_file,
)
from leap_tree_game.ui.console import render_framed_screen


def run_setup_wizard(
    env_path: Path | str = ".env",
    *,
    console: Console | None = None,
) -> ProviderSettings:
    active_console = console or Console()
    render_framed_screen(
        "Leap Tree Game",
        "[bold]Configure your environment[/bold]",
        "",
        "Choose a provider and model. You can rerun this any time.",
        active_console=active_console,
    )

    provider = Prompt.ask(
        "Provider",
        choices=list(SUPPORTED_PROVIDERS),
        default="openai",
        console=active_console,
    )
    provider_name = provider.lower()
    model = Prompt.ask(
        "Model",
        default=DEFAULT_MODELS[provider_name],
        console=active_console,
    )

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url = DEFAULT_OLLAMA_BASE_URL
    ollama_api_key: str | None = None

    if provider_name == "openai":
        openai_api_key = _optional_secret("OpenAI API key", active_console)
    elif provider_name == "anthropic":
        anthropic_api_key = _optional_secret("Anthropic API key", active_console)
    else:
        ollama_base_url = Prompt.ask(
            "Ollama base URL",
            default=DEFAULT_OLLAMA_BASE_URL,
            console=active_console,
        )
        if "ollama.com" in ollama_base_url.lower():
            ollama_api_key = _optional_secret("Ollama API key", active_console)

    settings = ProviderSettings(
        provider=provider_name,  # type: ignore[arg-type]
        model=model,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        ollama_base_url=ollama_base_url,
        ollama_api_key=ollama_api_key,
    )
    write_env_file(settings, env_path)
    active_console.print(f"[green]Saved configuration to {Path(env_path)}[/green]")
    return settings


def _optional_secret(prompt: str, console: Console) -> str | None:
    value = Prompt.ask(prompt, password=True, console=console)
    value = value.strip()
    return value or None
