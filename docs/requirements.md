# Requirements

Leap Tree Game is a terminal-first branching-story experience.  
Players choose `genre`, `setting`, and `opening`, then choose between two AI-generated continuations each turn.

The system keeps the canonical story path, renders each state in framed screens, and continues until the player quits or restarts.

## Product Requirements

- **Game loop**
  - Ask for setup:
    - genre
    - setting
    - opening
  - Show exactly two continuation options.
  - Advance with `a` or `b`, regenerate with `g`, restart with `r`, quit with `q`.
- **Story contract**
  - The AI must return JSON:
    - `story`
    - `option_a`
    - `option_b`
  - `story` is canonical and must be preserved as:
    - opening on turn 1,
    - then previous canonical story + selected continuation.
  - `option_a`/`option_b` are appendee text only, never labels.
- **Continuation shape (token-level style control)**
  - Each turn uses either:
    - `continue_sentence` (no terminal punctuation enforcement),
    - `end_sentence` (enforced terminal punctuation).
  - First call should be 50/50 by picker; later calls alternate for balance.
  - Regeneration of a turn preserves the existing continuation shape.
- **Sentence start behavior**
  - If the current story ends with sentence punctuation, options should begin a new sentence.
  - If it does not, options should continue the current sentence.
- **ASCII scene rendering**
  - Render an image-only ASCII scene above each story turn.
  - Scene should be requested from model with full story context and last completed sentence.
  - ASCII output must be pure visual text: no prose, no markdown, no labels, no preamble.

## Runtime and Error Behavior

- Missing or invalid dependencies should block startup with clear guidance.
- Missing/invalid `.env` should trigger setup wizard.
- Gracefully report and recover from:
  - API key/auth errors,
  - model-unavailable (404) errors,
  - malformed AI responses,
  - network/timeout issues,
  - rate limits.
- Footer status must always render as:
  - `turn <N> | <provider> / <model> | tokens used: <count>`
  - provider/model labels are lower-case in output.
- Provider key/shape decisions are tested with unit prompts and fake providers.

## UI Requirements

- Every setup step and every turn is shown in a fresh, framed Rich screen.
- Setup wizard is segmented:
  - provider step,
  - model step,
  - API key / endpoint step.
- Predefined options include `Other` with custom input support.
- Use muted styling and section labels to keep the interface readable and compact.

## Scope

**In scope (MVP)**
- Local gameplay only
- One active story session per run
- No persistence

**Out of scope (MVP)**
- Save/load or resume files
- Moderation/accounting
- Multiplayer
- AI policy enforcement controls
- Story summarization

## Technical Stack

- Python 3.12+
- Typer (CLI)
- Rich (UI)
- Pydantic + Pydantic AI (model contracts and providers)
- pytest (offline unit tests)

## Project Layout

- `leap_tree_game/`:
  - `app.py` entrypoint and commands
  - `game/`: prompts, state, engine, layout, logic
  - `providers/`: provider clients, response normalization, token tracking
  - `ui/`: framed prompts and screens
  - `config/`: `.env` loading, validation, setup wizard
  - `models/`: response schema
- `prompts/`: `initial.md`, `next.md`, `ascii_art.md`
- `tests/`: prompt, state, provider, and engine behavior tests
- `.env.example`, `requirements.txt`, `README.md`

## Run

```bash
python -m leap_tree_game.app
```
