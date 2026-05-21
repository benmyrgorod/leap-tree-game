"""Interactive `.env` setup wizard."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.text import Text
from rich.prompt import Prompt

from leap_tree_game.config.settings import (
    DEFAULT_MODELS,
    DEFAULT_OLLAMA_BASE_URL,
    ProviderSettings,
    SUPPORTED_PROVIDERS,
    write_env_file,
)
from leap_tree_game.ui.forms import resolve_menu_choice
from leap_tree_game.ui.console import render_framed_screen


def run_setup_wizard(
    env_path: Path | str = ".env",
    *,
    console: Console | None = None,
) -> ProviderSettings:
    active_console = console or Console()

    render_framed_screen(
        "Leap Tree Game",
        Text("Configure your environment", style="bold"),
        Text(""),
        "",
        "Choose a provider and model. You can rerun this any time.",
        active_console=active_console,
    )

    provider = _ask_provider(active_console)
    provider_name = provider.lower()
    model = _ask_model(provider_name, active_console)

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url = DEFAULT_OLLAMA_BASE_URL
    ollama_api_key: str | None = None

    if provider_name == "openai":
        openai_api_key = _ask_api_key(
            "OpenAI API key",
            active_console=active_console,
            subtitle="setup 3/3",
            required=True,
        )
    elif provider_name == "anthropic":
        anthropic_api_key = _ask_api_key(
            "Anthropic API key",
            active_console=active_console,
            subtitle="setup 3/3",
            required=True,
        )
    else:
        ollama_base_url = _ask_ollama_base_url(active_console)
        if "ollama.com" in ollama_base_url.lower():
            ollama_api_key = _ask_api_key(
                "Ollama API key",
                active_console=active_console,
                subtitle="setup 4/4",
                required=True,
            )

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


def _ask_provider(active_console: Console) -> str:
    options = list(SUPPORTED_PROVIDERS)
    last_error: str | None = None

    while True:
        lines = [
            Text("Provider", style="bold"),
            Text(""),
            Text("Select an option by number or name.", style="dim"),
            Text(""),
            Text("1. openai"),
            Text("2. anthropic"),
            Text("3. ollama"),
        ]
        if last_error:
            lines.append(Text(last_error, style="yellow"))

        render_framed_screen(
            "Leap Tree Game",
            *lines,
            active_console=active_console,
            subtitle="setup 1/3",
        )

        value = Prompt.ask(
            "Provider",
            default="1",
            console=active_console,
        )
        try:
            return resolve_menu_choice(value, options)
        except ValueError:
            last_error = "Please choose one of the listed options."


def _ask_model(provider_name: str, active_console: Console) -> str:
    render_framed_screen(
        "Leap Tree Game",
        Text("Model", style="bold"),
        Text(""),
        Text("Enter a model name to use with the selected provider.", style="dim"),
        active_console=active_console,
        subtitle="setup 2/3",
    )
    return Prompt.ask(
        "Model",
        default=DEFAULT_MODELS[provider_name],
        console=active_console,
    )


def _ask_api_key(
    prompt_label: str,
    *,
    active_console: Console,
    subtitle: str,
    required: bool = False,
) -> str | None:
    last_error: str | None = None
    while True:
        lines = [
            Text(prompt_label, style="bold"),
            Text(""),
            Text("Enter the API key used by the selected provider.", style="dim"),
        ]
        if last_error:
            lines.append(Text(last_error, style="yellow"))

        render_framed_screen(
            "Leap Tree Game",
            *lines,
            active_console=active_console,
            subtitle=subtitle,
        )
        value = Prompt.ask(prompt_label, password=True, console=active_console).strip()
        if value:
            return value
        if not required:
            return None
        last_error = "An API key is required for this provider."


def _ask_ollama_base_url(active_console: Console) -> str:
    render_framed_screen(
        "Leap Tree Game",
        Text("Ollama Base URL", style="bold"),
        Text(""),
        Text("Enter the Ollama base URL endpoint.", style="dim"),
        active_console=active_console,
        subtitle="setup 3/4",
    )
    return Prompt.ask(
        "Ollama base URL",
        default=DEFAULT_OLLAMA_BASE_URL,
        console=active_console,
    )
