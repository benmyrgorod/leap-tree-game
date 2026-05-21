from __future__ import annotations

import pytest

from leap_tree_game.ui.forms import resolve_menu_choice


def test_resolve_menu_choice_by_number() -> None:
    assert resolve_menu_choice("2", ["A", "B", "Other"]) == "B"


def test_resolve_menu_choice_other_uses_custom_value() -> None:
    assert resolve_menu_choice("Other", ["A", "Other"], custom_value="Custom story") == "Custom story"


def test_resolve_menu_choice_rejects_blank_custom_value() -> None:
    with pytest.raises(ValueError):
        resolve_menu_choice("Other", ["A", "Other"], custom_value=" ")
