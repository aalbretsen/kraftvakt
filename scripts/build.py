"""Install, check and build all of Kraftvakt.

Run from the repository root, with the Node from .nvmrc active:

    uv run scripts/build.py

The script installs the development dependencies of the integration and the
panel, runs the tests with coverage, ruff and mypy, checks the format of,
type checks, tests and builds the panel, and tells when the panel bundle
differs from the committed one. It stops at the first step that fails.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NVMRC = ROOT / ".nvmrc"
BUNDLE = ROOT / "custom_components" / "kraftvakt" / "frontend"

STEPS = (
    ("uv", "pip", "install", "--quiet", "-r", "requirements_dev.txt"),
    ("npm", "--prefix", "frontend", "ci"),
    (
        ".venv/bin/python",
        "-m",
        "pytest",
        "-q",
        "--cov=custom_components/kraftvakt",
        "--cov=simulator/custom_components/kraftvakt_simulator",
        "--cov=diagnostics",
        "--cov-report=term-missing:skip-covered",
        "--cov-fail-under=100",
    ),
    (".venv/bin/ruff", "check", "."),
    (".venv/bin/ruff", "format", "--check", "."),
    (".venv/bin/mypy",),
    ("npm", "--prefix", "frontend", "run", "format:check"),
    ("npm", "--prefix", "frontend", "run", "typecheck"),
    ("npm", "--prefix", "frontend", "test"),
    ("npm", "--prefix", "frontend", "run", "build"),
)


class BuildError(Exception):
    """A reason the build cannot run."""


def main() -> None:
    try:
        build()
    except (BuildError, subprocess.CalledProcessError) as error:
        sys.exit(f"Build stopped: {error}")
    if run("git", "status", "--porcelain", str(BUNDLE), capture=True):
        print("The panel bundle changed: commit it together with the source in frontend/.")
    print("Build done.")


def build() -> None:
    check_node()
    for step in STEPS:
        print(f"\n→ {' '.join(step)}", flush=True)
        run(*step)


def check_node() -> None:
    """Raise BuildError unless the Node from .nvmrc is active.

    nvm is a shell function, so the script cannot activate Node itself.
    """
    wanted = NVMRC.read_text().strip().removeprefix("v")
    try:
        active = run("node", "--version", capture=True).removeprefix("v")
    except FileNotFoundError:
        active = None
    if active != wanted:
        found = f"Node {active} is active" if active else "Node is not active"
        raise BuildError(f"{found}, but .nvmrc wants {wanted}. Run nvm install, and build again.")


def run(*command: str, capture: bool = False) -> str:
    """Run a command in the repository, and raise CalledProcessError if it fails."""
    result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else ""


if __name__ == "__main__":
    main()
