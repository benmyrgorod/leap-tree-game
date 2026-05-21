"""Version metadata and git-derived build information."""

from __future__ import annotations

import subprocess
from pathlib import Path

from packaging.version import Version

RELEASE_VERSION = Version("0.1.0")
BASE_VERSION = str(RELEASE_VERSION)
VERSION = BASE_VERSION
VERSION_INFO = RELEASE_VERSION


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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
