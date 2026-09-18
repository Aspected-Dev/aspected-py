"""This script validates the package version against the OpenAPI spec version.

The package version is dynamic (derived by hatchling via uv-dynamic-versioning
from git tags), so it can't be read statically from pyproject.toml. Instead,
this script asks hatchling to resolve the actual version that would be used
for the build, and ensures its major.minor matches openapi.json.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from hatchling.metadata.core import ProjectMetadata
from hatchling.plugin.manager import PluginManager

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def _parse_semver(raw: str, source: str) -> SemVer:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", raw.strip())
    if not match:
        raise ValueError(f'Could not parse semantic version "{raw}" from {source}')
    major, minor, patch = match.groups()
    return SemVer(int(major), int(minor), int(patch))


def _fail(message: str) -> None:
    print(f"\n::error::{message}\n")
    sys.exit(1)


def _ok(message: str) -> None:
    print(f"OK: {message}")


def main() -> None:
    openapi_path = ROOT / "openapi.json"

    metadata = ProjectMetadata(str(ROOT), PluginManager())
    package_version = _parse_semver(metadata.version, "hatchling (dynamic version)")

    openapi = json.loads(openapi_path.read_text())
    openapi_version = _parse_semver(
        openapi.get("info", {}).get("version", ""), "openapi.json#info.version"
    )

    print(f"Package version (hatchling): {package_version}")
    print(f"openapi.json version:        {openapi_version}")

    if (
        package_version.major != openapi_version.major
        or package_version.minor != openapi_version.minor
    ):
        _fail(
            f"Package major.minor ({package_version.major}.{package_version.minor}) must "
            f"match openapi.json major.minor ({openapi_version.major}.{openapi_version.minor})."
        )
    _ok("Package major.minor matches openapi.json major.minor.")


if __name__ == "__main__":
    main()
