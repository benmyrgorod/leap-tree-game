"""Rich rendering helpers."""

from __future__ import annotations

import random

from rich import box
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from leap_tree_game import __version__
from leap_tree_game.models.story import StoryResponse
from leap_tree_game.i18n import t


console = Console()
FRAME_STYLE = "bright_black"


def render_choices(response: StoryResponse, *, active_console: Console = console) -> None:
    active_console.print(build_choices_table(response))


def build_choices_table(response: StoryResponse) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Label", style="bold magenta", no_wrap=True)
    table.add_column("Option", style="white")
    table.add_row("", "")
    table.add_row("A.", response.option_a)
    table.add_row("B.", response.option_b)
    return table


def render_framed_screen(
    title: str,
    *renderables,
    active_console: Console = console,
    subtitle: str | None = None,
    clear: bool = True,
) -> None:
    if clear:
        active_console.clear()
    active_console.print(build_screen_frame(title, *renderables, subtitle=subtitle))


def render_turn_screen(
    response: StoryResponse,
    *,
    active_console: Console = console,
    subtitle: str | None = None,
    language: str = "en",
    ascii_art: str | None = None,
) -> None:
    frame_width = max(40, (active_console.width or 100) - 4)
    renderables = []
    if ascii_art:
        for line in ascii_art.splitlines():
            renderables.append(Text(line, no_wrap=True))
        renderables.append(Text(""))
    story = Panel(
        response.story,
        title=f"[dim]{t(language, 'turn.current_story')}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
        width=frame_width,
    )
    commands = Text(
        f"\n{t(language, 'turn.command_help')}",
        style="dim",
    )
    render_framed_screen(
        t(language, "app.title"),
        *renderables,
        story,
        build_choices_table(response),
        commands,
        active_console=active_console,
        subtitle=subtitle,
    )


def render_full_story_screen(
    story: str,
    *,
    active_console: Console = console,
    subtitle: str | None = None,
    language: str = "en",
    command_text: str | None = None,
    status_message: str | None = None,
    status_message_style: str = "green",
) -> None:
    frame_width = max(40, (active_console.width or 100) - 4)
    full_story = Panel(
        story,
        title=f"[dim]{t(language, 'turn.full_story')}[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
        width=frame_width,
    )
    status = Text("")
    if status_message:
        status = Text.from_markup(
            f"[{status_message_style}]{status_message}[/{status_message_style}]"
        )
    commands = Text(
        f"\n{command_text or t(language, 'turn.storybook_command_help')}",
        style="dim",
    )
    render_framed_screen(
        t(language, "app.title"),
        full_story,
        status,
        commands,
        active_console=active_console,
        subtitle=subtitle,
    )


def build_screen_frame(title: str, *renderables, subtitle: str | None = None) -> Panel:
    version = f"v{__version__}"
    if subtitle is None or not str(subtitle).strip():
        framed_subtitle = version
    elif version in subtitle:
        framed_subtitle = subtitle
    else:
        framed_subtitle = f"{subtitle} | {version}"
    return Panel(
        Group(*renderables),
        title=f"[bold cyan]{title}[/bold cyan]",
        subtitle=framed_subtitle,
        border_style=FRAME_STYLE,
        box=box.ROUNDED,
        padding=(1, 2),
        expand=True,
    )


def render_error(message: str, *, active_console: Console = console) -> None:
    active_console.print(f"[bold red]Error:[/bold red] {message}")


def render_warning(message: str, *, active_console: Console = console) -> None:
    active_console.print(f"[yellow]{message}[/yellow]")


def render_success(message: str, *, active_console: Console = console) -> None:
    active_console.print(f"[green]{message}[/green]")


def render_title(*, active_console: Console = console, version: str | None = None) -> None:
    # `version` is intentionally kept for compatibility with existing call sites.
    _ = version
    title = Text("Leap Tree Game", style="bold cyan")
    greeting = random.choice(_WELCOME_GREETINGS)
    renderables = [title, Text(greeting, style="yellow")]
    subtitle = "branching AI stories"
    render_framed_screen(
        "Leap Tree Game",
        *renderables,
        active_console=active_console,
        subtitle=subtitle,
    )

_WELCOME_GREETINGS = [
    "Welcome back, storyteller! The branches are waiting.",
    "Welcome! A warm fire, a cool breeze, and a new story path ahead.",
    "Welcome! May your next choice change the world in the best way.",
    "Welcome, friend. Pull up a chair and make the next turn memorable.",
]
