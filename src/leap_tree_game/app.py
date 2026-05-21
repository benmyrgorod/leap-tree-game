"""Typer CLI entrypoint for Leap Tree Game."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from leap_tree_game import __version__
from leap_tree_game.config.settings import ConfigError, MissingConfigError, load_settings
from leap_tree_game.config.setup_wizard import run_setup_wizard
from leap_tree_game.game.engine import GameEngine
from leap_tree_game.ui.console import render_error, render_success, render_title, render_warning

app = typer.Typer(add_completion=False, invoke_without_command=True, no_args_is_help=False)
console = Console()


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

    render_title(console)
    settings = _load_or_setup()
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

    for module_name in ["pydantic", "typer", "rich", "dotenv", "pydantic_ai"]:
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


def _load_or_setup():
    try:
        return load_settings(Path(".env"))
    except MissingConfigError:
        render_warning("No `.env` found. Starting setup.", active_console=console)
        return run_setup_wizard(Path(".env"), console=console)
    except ConfigError as exc:
        render_warning(f"Configuration needs attention: {exc}", active_console=console)
        return run_setup_wizard(Path(".env"), console=console)


def _status(condition: bool, detail: str) -> str:
    color = "green" if condition else "red"
    label = "ok" if condition else "fail"
    return f"[{color}]{label}[/{color}] [dim]{detail}[/dim]"


def main() -> None:
    app()


if __name__ == "__main__":
    main()
