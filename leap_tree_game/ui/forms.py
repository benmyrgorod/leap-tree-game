"""Interactive form helpers for the CLI."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from leap_tree_game.ui.console import render_framed_screen
from leap_tree_game.i18n import t


def resolve_menu_choice(
    selection: str,
    options: list[str],
    *,
    custom_value: str | None = None,
    other_label: str = "Other",
    language: str = "en",
) -> str:
    """Resolve a numbered or label-based selection to its final value."""

    normalized = selection.strip()
    if not normalized:
        raise ValueError(t(language, "forms.selection_error"))

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
        raise ValueError(t(language, "forms.selection_error"))

    if selected == other_label:
        if custom_value is None or not custom_value.strip():
            raise ValueError(
                t(language, "forms.custom_value_error", other_label=other_label)
            )
        return custom_value.strip()

    return selected


def ask_menu_choice(
    title: str,
    options: list[str],
    *,
    console: Console,
    subtitle: str | None = None,
    language: str = "en",
    other_label: str | None = None,
) -> str:
    resolved_other_label = other_label or t(language, "forms.other_label")
    error: str | None = None
    while True:
        render_menu_screen(
            title,
            options,
            console=console,
            subtitle=subtitle,
            error=error,
            language=language,
            other_label=resolved_other_label,
        )
        raw = Prompt.ask(title, console=console)
        try:
            selected = resolve_menu_choice(
                raw,
                options,
                custom_value="__placeholder__",
                other_label=resolved_other_label,
                language=language,
            )
        except ValueError as exc:
            error = str(exc)
            continue

        if selected == "__placeholder__":
            custom_error: str | None = None
            while True:
                render_custom_value_screen(
                    title,
                    console=console,
                    subtitle=subtitle,
                    error=custom_error,
                    language=language,
                )
                custom = Prompt.ask(
                    resolved_other_label,
                    console=console,
                )
                try:
                    return resolve_menu_choice(
                        raw,
                        options,
                        custom_value=custom,
                        language=language,
                        other_label=resolved_other_label,
                    )
                except ValueError as exc:
                    custom_error = str(exc)
                    continue

        return selected


def ask_choice_command(
    *,
    console: Console,
    language: str = "en",
) -> str:
    return Prompt.ask(
        t(language, "forms.choice_prompt"),
        choices=["a", "b", "r", "s", "q"],
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
    language: str = "en",
    error: str | None = None,
    other_label: str | None = None,
) -> None:
    renderables = [
        Text(title, style="bold"),
        Text(""),
        Text(
            t(language, "forms.select_option"),
            style="dim",
        ),
        Text(""),
        build_menu_table(
            options,
            language=language,
            other_label=other_label,
        ),
    ]
    if error:
        renderables.append(Text(error, style="yellow"))
    render_framed_screen(
        t(language, "app.title"),
        *renderables,
        active_console=console,
        subtitle=subtitle,
    )


def render_custom_value_screen(
    title: str,
    *,
    console: Console,
    subtitle: str | None = None,
    language: str = "en",
    error: str | None = None,
) -> None:
    renderables = [
        Text(
            t(language, "forms.custom_value_prompt", field=title),
            style="dim",
        ),
    ]
    if error:
        renderables.append(Text(error, style="yellow"))
    render_framed_screen(
        t(language, "app.title"),
        *renderables,
        active_console=console,
        subtitle=subtitle,
    )


def build_menu_table(
    options: list[str],
    *,
    language: str = "en",
    other_label: str | None = None,
) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(t(language, "forms.number_header"), justify="right", style="dim", no_wrap=True)
    table.add_column(t(language, "forms.option_header"), style="white")
    for index, option in enumerate(options, start=1):
        translated_option = option
        if other_label and option == other_label:
            translated_option = t(language, "forms.other_label")
        table.add_row(str(index), translated_option)
    return table
