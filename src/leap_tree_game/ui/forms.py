"""Interactive form helpers for the CLI."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

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
        raise ValueError("Please enter a selection.")

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
) -> str:
    render_menu(title, options, console=console)
    while True:
        raw = Prompt.ask(title, console=console)
        try:
            selected = resolve_menu_choice(raw, options, custom_value="__placeholder__")
        except ValueError as exc:
            console.print(f"[yellow]{exc}[/yellow]")
            continue

        if selected == "__placeholder__":
            custom = Prompt.ask("Custom value", console=console)
            try:
                return resolve_menu_choice(raw, options, custom_value=custom)
            except ValueError as exc:
                console.print(f"[yellow]{exc}[/yellow]")
                continue

        return selected


def ask_choice_command(*, console: Console) -> str:
    return Prompt.ask(
        "Choose",
        choices=["a", "b", "r", "q"],
        default="a",
        show_choices=True,
        console=console,
    ).lower()


def render_menu(title: str, options: list[str], *, console: Console) -> None:
    table = Table(title=title, show_header=False, box=None, padding=(0, 1))
    table.add_column("Number", justify="right", style="dim", no_wrap=True)
    table.add_column("Option", style="white")
    for index, option in enumerate(options, start=1):
        table.add_row(str(index), option)
    console.print(table)
