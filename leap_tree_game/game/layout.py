"""Pure UI layout helpers for computing turn rendering dimensions."""

from __future__ import annotations

import textwrap
from rich.console import Console


class TurnLayout:
    """Small layout helper used by the game loop when reserving space for art."""

    COMMAND_HELP = "Choose: a (first option), b (second option), r (regenerate), s (restart), q (quit)"

    def __init__(self, console: Console) -> None:
        self.console = console

    def turn_status_label(
        self,
        turn_number: int,
        provider_summary: str,
        tokens_used: int,
        *,
        language: str = "en",
        status_label: str = "turn {turn_number} | {provider_summary} | tokens used: {tokens_used}",
    ) -> str:
        return status_label.format(
            turn_number=turn_number,
            provider_summary=provider_summary,
            tokens_used=tokens_used,
        )

    def art_width(self) -> int:
        return max(40, (self.console.width or 100) - 4)

    def art_height(
        self,
        story: str,
        option_a: str,
        option_b: str,
        *,
        language: str | None = None,
        command_text: str | None = None,
    ) -> int:
        total_lines = self.console.height or 24
        non_art_lines = self.estimated_non_art_line_count(
            story,
            option_a,
            option_b,
            language=language,
            command_text=command_text,
        )
        available = total_lines - non_art_lines
        return max(3, available - 4)

    def estimated_non_art_line_count(
        self,
        story: str,
        option_a: str,
        option_b: str,
        width: int | None = None,
        language: str | None = None,
        command_text: str | None = None,
    ) -> int:
        if width is None:
            width = self.art_width()
        return self._estimated_non_art_line_count_at_width(
            story,
            option_a,
            option_b,
            width=width,
            language=language,
            command_text=command_text,
        )

    def _estimated_non_art_line_count_at_width(
        self,
        story: str,
        option_a: str,
        option_b: str,
        *,
        width: int,
        language: str | None = None,
        command_text: str | None = None,
    ) -> int:
        outer_lines = 4
        story_panel_lines = self._estimate_wrapped_lines(story, max(24, width - 6)) + 4
        option_width = max(24, width - 14)
        option_lines = max(
            self._estimate_wrapped_lines(option_a, option_width),
            self._estimate_wrapped_lines(option_b, option_width),
        )
        choices_lines = (option_lines * 2) + 1
        command_lines = 1 + self._command_lines(width=width, command_text=command_text)

        return outer_lines + story_panel_lines + choices_lines + command_lines

    def _command_lines(
        self,
        width: int | None = None,
        command_text: str | None = None,
    ) -> int:
        command_width = max(1, (width or self.art_width()) - 4)
        wrapped = textwrap.wrap(
            command_text or self.COMMAND_HELP,
            width=command_width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        return max(1, len(wrapped))

    @staticmethod
    def _estimate_wrapped_lines(text: str, width: int) -> int:
        wrapped = textwrap.wrap(text, width=max(1, width), break_long_words=False, break_on_hyphens=False)
        return max(1, len(wrapped))
