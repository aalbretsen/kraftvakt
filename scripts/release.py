"""Prepare a release of Kraftvakt: set the version, commit, tag and push.

Run on an up-to-date main branch with a clean working tree and Node active:

    uv run scripts/release.py 0.2.0

The version is SemVer. The script runs every check, sets the version in the
files that carry it, commits, makes the tag `v<version>`, and asks before it
pushes main and the tag. The pushed tag starts the release workflow, which
creates a draft GitHub release for the release notes to be written by hand.
A version with a pre-release part, like `0.2.0-beta.1`, gives a GitHub
pre-release, which HACS offers only to users who turned on pre-releases.

The simulator is for development only and keeps its own version.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "custom_components" / "kraftvakt" / "manifest.json"
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_JSON = ROOT / "frontend" / "package.json"
PACKAGE_LOCK = ROOT / "frontend" / "package-lock.json"
BRANCH = "main"
REMOTE = "origin"

SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][\dA-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][\dA-Za-z-]*))*))?"
)
PYPROJECT_VERSION = re.compile(r'^version = "([^"]+)"$', re.MULTILINE)
# Where the version is in each JSON file of the release, as paths of keys, in
# the order they come in the file.
JSON_VERSIONS = {
    MANIFEST: (("version",),),
    PACKAGE_JSON: (("version",),),
    PACKAGE_LOCK: (("version",), ("packages", "", "version")),
}

CHECKS = (
    (".venv/bin/python", "-m", "pytest", "-q"),
    (".venv/bin/ruff", "check", "."),
    (".venv/bin/ruff", "format", "--check", "."),
    ("npm", "--prefix", "frontend", "run", "typecheck"),
    ("npm", "--prefix", "frontend", "run", "build"),
)


class ReleaseError(Exception):
    """A reason the release cannot be made."""


def main() -> None:
    """Prepare the release given on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="the new version, SemVer, like 0.2.0")
    version = parser.parse_args().version
    try:
        release(version)
    except (ReleaseError, subprocess.CalledProcessError) as error:
        sys.exit(f"Release stopped: {error}")


def release(version: str) -> None:
    """Check, set the version, commit, tag and push after confirmation."""
    tag = f"v{version}"
    check_version(version, current_version())
    check_repository(tag)
    print("Running the checks …")
    for check in CHECKS:
        run(*check)
    if git("status", "--porcelain"):
        raise ReleaseError("the checks changed files; is the panel bundle built?")

    set_version(version)
    if git("status", "--porcelain"):
        git("commit", "--all", "--message", f"Release {tag}")
    git("tag", "--annotate", tag, "--message", f"Kraftvakt {version}")
    print(git("log", "-1", "--stat", "--decorate"))

    answer = input(f"Push {BRANCH} and {tag} to {REMOTE}? [y/N] ")
    if answer.strip().lower() != "y":
        print(
            f"Not pushed. Push later with: git push --atomic {REMOTE} {BRANCH} {tag}\n"
            f"Or undo with: git tag -d {tag}, and git reset --hard HEAD~1 if a "
            "release commit was made."
        )
        return
    git("push", "--atomic", REMOTE, BRANCH, tag)
    print(
        f"Pushed. The release workflow creates a draft release for {tag} on "
        "GitHub: write the release notes and publish it."
    )


def check_version(version: str, current: str) -> None:
    """Raise ReleaseError unless the version is SemVer and not below the current."""
    if SEMVER.fullmatch(version) is None:
        raise ReleaseError(f"{version} is not a SemVer version like 0.2.0")
    if precedence(version) < precedence(current):
        raise ReleaseError(f"{version} is lower than the current version {current}")


def check_repository(tag: str) -> None:
    """Raise ReleaseError unless main is clean, up to date and the tag is new."""
    if git("branch", "--show-current") != BRANCH:
        raise ReleaseError(f"releases are made from {BRANCH}")
    if git("status", "--porcelain"):
        raise ReleaseError("the working tree has uncommitted changes")
    git("fetch", REMOTE, BRANCH, "--tags")
    if not run_ok("git", "merge-base", "--is-ancestor", f"{REMOTE}/{BRANCH}", "HEAD"):
        raise ReleaseError(f"{BRANCH} is behind {REMOTE}/{BRANCH}; pull first")
    if git("tag", "--list", tag):
        raise ReleaseError(f"the tag {tag} already exists")


def current_version() -> str:
    """Return the version in the manifest, which every release file follows."""
    return json.loads(MANIFEST.read_text())["version"]


def set_version(version: str) -> None:
    """Set the version in every file of the release that carries one.

    Only the version text is replaced, so the files keep their format.
    """
    for path, locations in JSON_VERSIONS.items():
        text = re.sub(
            r'("version": ")[^"]*(")',
            rf"\g<1>{version}\g<2>",
            path.read_text(),
            count=len(locations),
        )
        data = json.loads(text)
        for location in locations:
            if value_at(data, location) != version:
                raise ReleaseError(f"the version in {path.name} was not where expected")
        path.write_text(text)
    text = PYPROJECT.read_text()
    PYPROJECT.write_text(PYPROJECT_VERSION.sub(f'version = "{version}"', text, 1))


def value_at(data: dict, location: tuple[str, ...]) -> object:
    """Return the value at a path of keys in JSON data."""
    for key in location:
        data = data[key]
    return data


def precedence(version: str) -> tuple:
    """Return a key that orders SemVer versions by precedence.

    A version without a pre-release part comes after its pre-releases, and
    numeric identifiers come before and compare as numbers.
    """
    match = SEMVER.fullmatch(version)
    if match is None:
        raise ReleaseError(f"{version} is not a SemVer version")
    major, minor, patch, prerelease = match.groups()
    identifiers = (
        ()
        if prerelease is None
        else tuple(
            (0, int(part), "") if part.isdigit() else (1, 0, part)
            for part in prerelease.split(".")
        )
    )
    return (int(major), int(minor), int(patch), prerelease is None, identifiers)


def git(*args: str) -> str:
    """Run git in the repository and return its output."""
    return run("git", *args, capture=True)


def run(*command: str, capture: bool = False) -> str:
    """Run a command in the repository, and stop the release if it fails."""
    result = subprocess.run(
        command, cwd=ROOT, check=True, text=True, capture_output=capture
    )
    return result.stdout.strip() if capture else ""


def run_ok(*command: str) -> bool:
    """Return whether a command succeeds."""
    return subprocess.run(command, cwd=ROOT, capture_output=True).returncode == 0


if __name__ == "__main__":
    main()
