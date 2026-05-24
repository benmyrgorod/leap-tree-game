# Leap Tree Game

A small Python 3.12+ CLI story game. Pick a genre and setting, choose from AI-generated openings, then choose between two AI-generated continuation branches.

## Install

### From PyPI

```bash
python3 -m pip install leaptreegame
```

Then run:

```bash
leaptreegame --help
```

### From Homebrew

```bash
brew tap benmyrgorod/leaptreegame
brew install leaptreegame
```

Source: [benmyrgorod/homebrew-leaptreegame](https://github.com/benmyrgorod/homebrew-leaptreegame)

If you want to run from source instead of a package install:

```bash
python3 -m pip install -r requirements.txt
```

## Configure

```bash
python -m leap_tree_game.app setup
```

By default, the setup wizard writes configuration to `~/.leaptreegame/.env` and the app reads from there on launch (or the explicit path passed by tests).

Configuration is stored in `.env` format with one of the supported providers:

- `openai`
- `anthropic`
- `ollama`

Local Ollama does not require an API key when using `http://localhost:11434/v1`.

## Play

```bash
leaptreegame
```

or from source:

```bash
python -m leap_tree_game.app
```

Useful commands:

```bash
leaptreegame --help
leaptreegame doctor
leaptreegame setup
leaptreegame play
```

## Test

```bash
python -m pytest
```

The unit tests do not make live AI requests. Live provider smoke tests are intentionally left out of the MVP test path.

## Versioning and Release

- Package version: `0.1`
- Git-augmented build metadata is included in `--version` output when available.

```bash
python -m leap_tree_game.app --version
```

Example: `0.1+g34ad2c6`

To create a release, push a version tag (for example `v0.1.0`) and GitHub Actions will:

- run the test suite,
- generate a source archive,
- publish a GitHub Release artifact.
