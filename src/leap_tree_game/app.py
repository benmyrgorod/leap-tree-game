"""Typer CLI entrypoint for Leap Tree Game."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.text import Text
from rich.table import Table

from leap_tree_game import __version__
from leap_tree_game.config.settings import (
    ConfigError,
    MissingConfigError,
    ProviderSettings,
    load_settings,
)
from leap_tree_game.config.setup_wizard import run_setup_wizard
from leap_tree_game.game.engine import GameEngine
from leap_tree_game.game.state import GameSetup
from leap_tree_game.providers.agent import StoryClient, StoryGenerationError
from leap_tree_game.ui.console import (
    render_error,
    render_framed_screen,
    render_success,
    render_title,
    render_warning,
)

app = typer.Typer(add_completion=False, invoke_without_command=True, no_args_is_help=False)
console = Console()

REQUIRED_RUNTIME_MODULES = ("pydantic", "typer", "rich", "dotenv", "pydantic_ai")


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    """Play an AI-powered branching story game."""

    if version:
        console.print(f"Leap Tree Game {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        play()


@app.command()
def play() -> None:
    """Start the normal play flow."""

    _ensure_runtime_dependencies()
    render_title(console)
    settings = _load_or_setup()
    _verify_llm_connection(settings)
    GameEngine(settings, console=console).play()


@app.command()
def setup() -> None:
    """Regenerate `.env` provider configuration."""

    try:
        run_setup_wizard(Path(".env"), console=console)
    except ValueError as exc:
        render_error(str(exc), active_console=console)
        raise typer.Exit(1) from exc


@app.command()
def doctor() -> None:
    """Validate Python, dependencies, and provider configuration."""

    table = Table(title="Leap Tree Doctor")
    table.add_column("Check")
    table.add_column("Status")

    ok = True
    python_ok = sys.version_info >= (3, 12)
    ok = ok and python_ok
    table.add_row("Python 3.12+", _status(python_ok, sys.version.split()[0]))

    for module_name in REQUIRED_RUNTIME_MODULES:
        present = importlib.util.find_spec(module_name) is not None
        ok = ok and present
        table.add_row(module_name, _status(present, "installed" if present else "missing"))

    try:
        settings = load_settings(Path(".env"))
    except MissingConfigError:
        ok = False
        table.add_row(".env", "[yellow]missing[/yellow]")
    except ConfigError as exc:
        ok = False
        table.add_row(".env", f"[red]{exc}[/red]")
    else:
        table.add_row(".env", f"[green]{settings.summary()}[/green]")

    console.print(table)
    if not ok:
        raise typer.Exit(1)
    render_success("Everything looks ready.", active_console=console)


def _load_or_setup() -> ProviderSettings:
    try:
        return load_settings(Path(".env"))
    except MissingConfigError:
        render_framed_screen(
            "Leap Tree Game",
            Text("No `.env` found. Starting setup.", style="yellow"),
            active_console=console,
        )
        return run_setup_wizard(Path(".env"), console=console)
    except ConfigError as exc:
        render_framed_screen(
            "Leap Tree Game",
            Text(f"Configuration needs attention: {exc}", style="yellow"),
            active_console=console,
        )
        return run_setup_wizard(Path(".env"), console=console)


def _verify_llm_connection(settings: ProviderSettings) -> None:
    test_setup = GameSetup(
        genre="Mystery",
        setting="Modern Day",
        opening="On a perfectly ordinary impossible day",
    )
    try:
        with console.status("[dim]Verifying provider connection...[/dim]"):
            StoryClient(settings).generate_initial(test_setup)
    except StoryGenerationError as exc:
        _clear_provider_env_file()
        render_framed_screen(
            "Leap Tree Game",
            Text("Unable to generate a response from the configured LLM.", style="red"),
            Text(""),
            Text("Verify your API key, model, and network connection."),
            Text("Your `.env` file was removed so setup will run again on the next launch."),
            active_console=console,
        )
        render_error(str(exc), active_console=console)
        raise typer.Exit(1) from exc


def _clear_provider_env_file() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        env_path.unlink()
    except OSError as exc:
        render_warning(
            f"Could not remove `.env`: {exc}. Fix it manually before rerunning setup.",
            active_console=console,
        )


def _status(condition: bool, detail: str) -> str:
    color = "green" if condition else "red"
    label = "ok" if condition else "fail"
    return f"[{color}]{label}[/{color}] [dim]{detail}[/dim]"


def _ensure_runtime_dependencies() -> None:
    missing = _missing_runtime_dependencies()
    if not missing:
        return
    render_error("Missing runtime dependencies detected.", active_console=console)
    render_error(
        f"Install requirements and retry: python3 -m pip install -r requirements.txt",
        active_console=console,
    )
    render_warning(f"Missing modules: {', '.join(missing)}", active_console=console)
    raise typer.Exit(1)


def _missing_runtime_dependencies() -> list[str]:
    missing = []
    for module_name in REQUIRED_RUNTIME_MODULES:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def main() -> None:
    app()


if __name__ == "__main__":
    main()
