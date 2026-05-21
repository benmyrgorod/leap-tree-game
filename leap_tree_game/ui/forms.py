"""Interactive form helpers for the CLI."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from leap_tree_game.ui.console import render_framed_screen

APP_FRAME_TITLE = "Leap Tree Game"
OTHER_LABEL = "Other"


def resolve_menu_choice(
    selection: str,
    options: list[str],
    *,
    custom_value: str | None = None,
) -> str:
    """Resolve a numbered or label-based selection to its final value."""

    normalized = selection.strip()
    if not normalized:
        raise ValueError("Please choose one of the listed options.")

    selected: str | None = None
    if normalized.isdigit():
        index = int(normalized)
        if 1 <= index <= len(options):
            selected = options[index - 1]
    else:
        selected = next(
            (option for option in options if option.lower() == normalized.lower()),
            None,
        )

    if selected is None:
        raise ValueError("Please choose one of the listed options.")

    if selected == OTHER_LABEL:
        if custom_value is None or not custom_value.strip():
            raise ValueError("Custom value is required for Other.")
        return custom_value.strip()

    return selected


def ask_menu_choice(
    title: str,
    options: list[str],
    *,
    console: Console,
    subtitle: str | None = None,
) -> str:
    error: str | None = None
    while True:
        render_menu_screen(title, options, console=console, subtitle=subtitle, error=error)
        raw = Prompt.ask(title, console=console)
        try:
            selected = resolve_menu_choice(raw, options, custom_value="__placeholder__")
        except ValueError as exc:
            error = str(exc)
            continue

        if selected == "__placeholder__":
            custom_error: str | None = None
            while True:
                render_custom_value_screen(title, console=console, subtitle=subtitle, error=custom_error)
                custom = Prompt.ask("Other", console=console)
                try:
                    return resolve_menu_choice(raw, options, custom_value=custom)
                except ValueError as exc:
                    custom_error = str(exc)
                    continue

        return selected


def ask_choice_command(*, console: Console) -> str:
    return Prompt.ask(
        "Choose",
        choices=["a", "b", "g", "r", "q"],
        default="a",
        show_choices=True,
        console=console,
    ).lower()


def render_menu_screen(
    title: str,
    options: list[str],
    *,
    console: Console,
    subtitle: str | None = None,
    error: str | None = None,
) -> None:
    renderables = [
        Text(title, style="bold"),
        Text(""),
        Text("Select an option by number or name.", style="dim"),
        Text(""),
        build_menu_table(title, options),
    ]
    if error:
        renderables.append(Text(error, style="yellow"))
    render_framed_screen(APP_FRAME_TITLE, *renderables, active_console=console, subtitle=subtitle)


def render_custom_value_screen(
    title: str,
    *,
    console: Console,
    subtitle: str | None = None,
    error: str | None = None,
) -> None:
    renderables = [
        Text(f"Enter a custom value for {title}.", style="dim"),
    ]
    if error:
        renderables.append(Text(error, style="yellow"))
    render_framed_screen(APP_FRAME_TITLE, *renderables, active_console=console, subtitle=subtitle)


def build_menu_table(title: str, options: list[str]) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Number", justify="right", style="dim", no_wrap=True)
    table.add_column("Option", style="white")
    for index, option in enumerate(options, start=1):
        table.add_row(str(index), option)
    return table
