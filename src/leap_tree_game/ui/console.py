"""Rich rendering helpers."""

from __future__ import annotations

import time

from rich import box
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from leap_tree_game.config.settings import ProviderSettings
from leap_tree_game.models.story import StoryResponse


console = Console()
FRAME_STYLE = "bright_black"


def render_header(settings: ProviderSettings, *, active_console: Console = console) -> None:
    active_console.rule("[bold]Leap Tree[/bold]", style="dim")
    active_console.print(f"[dim]Provider:[/dim] {settings.provider}  [dim]Model:[/dim] {settings.model}")
    active_console.print()


def render_story(response: StoryResponse, *, active_console: Console = console) -> None:
    active_console.print(Panel(response.story, title="Story", border_style="cyan", padding=(1, 2)))


def render_streamed_story(
    response: StoryResponse,
    *,
    active_console: Console = console,
    delay: float = 0.005,
) -> None:
    active_console.print("[dim]Story[/dim]")
    for chunk in _chunks(response.story, 14):
        active_console.print(chunk, end="")
        if delay:
            time.sleep(delay)
    active_console.print("\n")


def render_choices(response: StoryResponse, *, active_console: Console = console) -> None:
    active_console.print(build_choices_table(response))


def build_choices_table(response: StoryResponse) -> Table:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Label", style="bold magenta", no_wrap=True)
    table.add_column("Option", style="white")
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
) -> None:
    story = Panel(
        response.story,
        title="[dim]Current story[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    commands = Text("Choose: a, b, r, q", style="dim")
    render_framed_screen(
        "Leap Tree",
        story,
        build_choices_table(response),
        commands,
        active_console=active_console,
        subtitle=subtitle,
    )


def build_screen_frame(title: str, *renderables, subtitle: str | None = None) -> Panel:
    return Panel(
        Group(*renderables),
        title=f"[bold cyan]{title}[/bold cyan]",
        subtitle=subtitle,
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


def render_title(active_console: Console = console) -> None:
    title = Text("Leap Tree", style="bold cyan")
    render_framed_screen(
        "Leap Tree",
        title,
        active_console=active_console,
        subtitle="branching AI stories",
    )


def _chunks(text: str, size: int) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]
