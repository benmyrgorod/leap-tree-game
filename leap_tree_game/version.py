"""Version metadata and git-derived build information."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import tomllib

try:
    from packaging.version import Version
except ModuleNotFoundError:  # pragma: no cover - allows startup on older installs.
    Version = None

FALLBACK_VERSION = "*"


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_pyproject_version() -> str | None:
    pyproject_path = _resolve_repo_root() / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    try:
        with pyproject_path.open("rb") as handle:
            data: dict[str, Any] = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    version = data.get("project", {}).get("version") if isinstance(data, dict) else None
    if isinstance(version, str):
        return version.strip() or None
    if version is not None:
        return str(version).strip() or None
    return None


_raw_version = _read_pyproject_version() or FALLBACK_VERSION
if Version is None:
    RELEASE_VERSION = _raw_version
else:
    RELEASE_VERSION = Version(_raw_version)

BASE_VERSION = str(RELEASE_VERSION)
VERSION = BASE_VERSION
VERSION_INFO = RELEASE_VERSION


def _git_version() -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "-C", str(_resolve_repo_root()), "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        ) or None
    except (OSError, subprocess.CalledProcessError):
        return None


GIT_VERSION = _git_version()

if GIT_VERSION:
    __version__ = f"{VERSION}+g{GIT_VERSION}"
else:
    __version__ = VERSION

__all__ = ["VERSION", "VERSION_INFO", "GIT_VERSION", "__version__"]
