"""Rich rendering helpers."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from leap_tree_game.models.story import StoryResponse


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
        title="[dim]Current story[/dim]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
        width=frame_width,
    )
    commands = Text(
        "\nChoose: a (first option), b (second option), g (regenerate), r (restart), q (quit)",
        style="dim",
    )
    render_framed_screen(
        "Leap Tree Game",
        *renderables,
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
    title = Text("Leap Tree Game", style="bold cyan")
    render_framed_screen(
        "Leap Tree Game",
        title,
        active_console=active_console,
        subtitle="branching AI stories",
    )
