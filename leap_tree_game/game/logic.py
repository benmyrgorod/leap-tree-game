"""Pure game logic helpers that are independent of UI and networking."""

from __future__ import annotations

def responses_match(
    baseline_a: str,
    baseline_b: str,
    candidate_a: str,
    candidate_b: str,
) -> bool:
    """Return True when two option pairs are the same ignoring order/case.

    This keeps regeneration from accepting duplicates while remaining resilient
    to pair-order flips.
    """

    return {
        baseline_a.strip().casefold(),
        baseline_b.strip().casefold(),
    } == {
        candidate_a.strip().casefold(),
        candidate_b.strip().casefold(),
    }
