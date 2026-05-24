# Implementation Plan (Rebuild View)

This document describes the same product as the current codebase, written as a clean restart plan after the refactor.

## 1) Architecture First

Keep the app thin and move behavior into four layers:

1. **App shell** (`leap_tree_game/app.py`)
   - dependency checks,
   - setup/config loading,
   - command entrypoints (`play`, `setup`, `doctor`).

2. **Engine orchestration** (`leap_tree_game/game/engine.py`)
   - loop control (`play`, `a`/`b`/`r`/`s`/`q`),
   - generation retry handling,
   - turn append/replace state flow.

3. **Pure game/prompt logic**
   - `leap_tree_game/game/state.py`: typed state model (`GameSetup`, `GameState`, `StoryTurn`, `Choice`).
   - `leap_tree_game/game/logic.py`: continuation-shape helpers and regeneration matching.
   - `leap_tree_game/game/layout.py`: deterministic turn rendering/height calculation.
   - `leap_tree_game/game/prompts.py`: prompt builders and constants.

4. **Provider + UI services**
   - `leap_tree_game/providers/agent.py`: provider factory, generation, parsing, ASCII prompt/query, token usage.
   - `leap_tree_game/ui/`: framed prompts, story rendering, command input.

## 2) Contracts and Data Flow

- Add/confirm response contract:
  - `story`, `option_a`, `option_b` from the provider.
- Keep `story` canonical at engine/state level; model is allowed to propose but final story is always normalized by state context.
- Persist per-turn continuation shape (`continue_sentence` / `end_sentence`) with each turn.
- On regeneration, send:
  - prior turn options as `avoid_continuations`,
  - prior turn continuation shape as fixed for retry flow.

## 3) Setup and Configuration

- Keep `.env` support and startup validation.
- Setup wizard:
  - provider screen,
  - model screen,
  - API key / base URL screen,
  - confirmation message and file write.
- On load, validate provider requirements and fail fast with clear next steps.

## 4) Gameplay Loop Build

Build around deterministic phases:

1. Ask setup form.
2. Generate initial turn.
3. Render framed turn + ASCII scene.
4. Ask for command:
   - `a`/`b`: apply choice, generate next turn.
   - `r`: regenerate current turn with duplicate avoidance and same continuation shape.
   - `s`: restart.
   - `q`: quit.
5. Repeat from step 3 until termination.

## 5) Rendering and Layout

- For each turn:
  - generate ASCII prompt using story context, genre, setting, and last complete sentence,
  - compute remaining terminal lines via `TurnLayout`,
  - render one frame containing ASCII scene, story panel, options, and status footer.
- Footer format is always:
  - `turn <N> | <provider> / <model> | tokens used: <count>`.

## 6) Error Handling and Robustness

- Centralize `StoryGenerationError` mapping in provider layer.
- Retry path in engine with user prompt on transient generation failures.
- Show friendly framed messages for:
  - missing dependencies,
  - bad config,
  - invalid JSON/prose,
  - API/network/rate-limit failures,
  - unavailable model.

## 7) Validation and Test Plan

- Unit tests for:
  - prompt builders,
  - story parsing and validation,
  - state helpers,
  - regeneration behavior,
  - UI rendering snapshots,
  - provider normalization and token accounting.
- Keep tests provider-agnostic with fake clients.
- Maintain `pytest`-only core CI path; no mandatory live LLM calls.

## 8) Delivery Checklist

- `pytest -q` passes.
- Gameplay commands are readable and stable in tests and manual runs.
- No stale legacy coupling: each layer owns one responsibility.
- Documentation (`docs/requirements.md`, `README.md`) reflects actual behavior and module boundaries.
