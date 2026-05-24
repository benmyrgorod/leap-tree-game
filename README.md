# Leap Tree Game

A small Python 3.12+ CLI story game. Pick a genre and setting, choose from AI-generated openings, then choose between two AI-generated continuation branches.

## Install

### Via Homebrew

```bash
brew tap benmyrgorod/leaptreegame
brew install leaptreegame
```

### Via pipx

```bash
pipx install leaptreegame
```

### From PyPI

```bash
python3 -m pip install leaptreegame
```

### From Source

```bash
git clone git@github.com:benmyrgorod/leaptreegame.git
cd leaptreegame
python3 -m pip install -r requirements.txt
```

## Play

```bash
leaptreegame
```

or when running from source:

```bash
python -m leap_tree_game.app
```

## Config

By default, the setup wizard writes configuration to `~/.leaptreegame/.env` and the app reads from there on launch. Configuration is stored in  `~/.leaptreegame/.env` with one of the supported providers:

- `openai`
- `anthropic`
- `ollama`

Local Ollama does not require an API key when using `http://localhost:11434/v1`.

## Commands

* `leaptreegame --help` - display help
* `leaptreegame --version` - display version
* `leaptreegame doctor` - validate Python, dependencies, and provider configuration
* `leaptreegame setup` - regenerate `.env` provider configuration
* `leaptreegame play` - start the normal play flow

## Test

```bash
python -m pytest
```

The unit tests do not make live AI requests. Live provider smoke tests are intentionally left out of the MVP test path.

## Release

To create a release:

1. Update version in `pyproject.toml`
2. Commit and push
3. Tag the same version (i.e. `v0.3.1`)
