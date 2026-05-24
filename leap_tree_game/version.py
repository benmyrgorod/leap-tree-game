"""Version metadata and git-derived build information."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from importlib.metadata import PackageNotFoundError, version as dist_version

import tomllib

try:
    from packaging.version import Version
    from packaging.version import InvalidVersion
except ModuleNotFoundError:  # pragma: no cover - allows startup on older installs.
    Version = None
    InvalidVersion = None

FALLBACK_VERSION = "0.0.0"


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


def _normalize_version(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    return normalized or None


def _read_distribution_version() -> str | None:
    try:
        dist = dist_version("leaptreegame")
    except PackageNotFoundError:
        return None

    return _normalize_version(dist)


_raw_version = _read_pyproject_version() or _read_distribution_version() or FALLBACK_VERSION

if Version is None:
    RELEASE_VERSION = _raw_version
else:
    try:
        RELEASE_VERSION = Version(_raw_version)
    except InvalidVersion:
        RELEASE_VERSION = Version(FALLBACK_VERSION)

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
