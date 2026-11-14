"""Update every pinned dependency of Kraftvakt to its newest compatible version.

Home Assistant decides most of the versions, so they follow one chain:

- pytest-homeassistant-custom-component, newest release: Home Assistant and the
  pytest packages it pins,
- that Home Assistant release: the Home Assistant frontend, ruff, mypy and Python,
- that Home Assistant frontend release: Node, Lit, TypeScript and @mdi/js.

The other build tools of the panel and the GitHub actions get their newest
release. Run from the repository root, with Node active:

    uv run scripts/update_dependencies.py

The script updates the files and the panel's lock file, and prints what
changed. Install and check the result as the README describes.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from functools import partial
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements_dev.txt"
PYPROJECT = ROOT / "pyproject.toml"
NVMRC = ROOT / ".nvmrc"
FRONTEND = ROOT / "frontend"
PACKAGE_JSON = FRONTEND / "package.json"
WORKFLOWS = ROOT / ".github" / "workflows"

TEST_HARNESS = "pytest-homeassistant-custom-component"
FROM_TEST_HARNESS = ("homeassistant", "pytest", "pytest-asyncio")
FROM_HA_FRONTEND = ("lit", "typescript", "@mdi/js")

CORE_FILE = "https://raw.githubusercontent.com/home-assistant/core/{version}/{path}"
FRONTEND_FILE = ("https://raw.githubusercontent.com/home-assistant/frontend/{version}/{path}")
PYPI = "https://pypi.org/pypi/{name}/json"
PYPI_RELEASE = "https://pypi.org/pypi/{name}/{version}/json"
NPM_LATEST = "https://registry.npmjs.org/{name}/latest"
GITHUB_RELEASE = "https://api.github.com/repos/{repository}/releases/latest"
FRONTEND_MANIFEST = "homeassistant/components/frontend/manifest.json"
ACTION_PIN = re.compile(r"(uses: )([\w.-]+/[\w.-]+)@(v[\d.]+)")


def main() -> None:
    """Update the dependencies and print what changed."""
    changes: list[str] = []
    frontend_version = update_python(changes)
    update_panel(frontend_version, changes)
    update_actions(changes)
    print("\n".join(dict.fromkeys(changes)) or "Everything is up to date.")


def update_python(changes: list[str]) -> str:
    """Update the Python development dependencies.

    Returns the version of the Home Assistant frontend the new Home Assistant
    release uses.
    """
    harness = fetch_json(PYPI.format(name=TEST_HARNESS))["info"]
    pins = {TEST_HARNESS: harness["version"]}
    harness_pins = requirement_pins(harness["requires_dist"])
    pins |= {name: harness_pins[name] for name in FROM_TEST_HARNESS}
    ha_version = pins["homeassistant"]
    pins["home-assistant-frontend"] = pinned(
        read_core(ha_version, FRONTEND_MANIFEST), "home-assistant-frontend"
    )
    pins["ruff"] = pinned(
        read_core(ha_version, "requirements_test_pre_commit.txt"), "ruff"
    )
    pins["mypy"] = pinned(read_core(ha_version, "requirements_test.txt"), "mypy")

    text = REQUIREMENTS.read_text()
    for name, version in pins.items():
        text = replace_version(
            text, rf"^{re.escape(name)}==(\S+)$", name, version, changes
        )
    REQUIREMENTS.write_text(text)

    ha_release = fetch_json(
        PYPI_RELEASE.format(name="homeassistant", version=ha_version)
    )
    python = ha_release["info"]["requires_python"]
    PYPROJECT.write_text(
        replace_version(
            PYPROJECT.read_text(),
            r'^requires-python = "(\S+)"$',
            "Python",
            python,
            changes,
        )
    )
    return pins["home-assistant-frontend"]


def update_panel(frontend_version: str, changes: list[str]) -> None:
    """Update Node and the panel's packages, and refresh the lock file."""
    node = fetch_text(FRONTEND_FILE.format(version=frontend_version, path=".nvmrc"))
    note_change(changes, "Node", NVMRC.read_text().strip(), node.strip())
    NVMRC.write_text(f"{node.strip()}\n")

    ha_frontend = json.loads(
        fetch_text(FRONTEND_FILE.format(version=frontend_version, path="package.json"))
    )
    ha_packages = {**ha_frontend["dependencies"], **ha_frontend["devDependencies"]}
    package = json.loads(PACKAGE_JSON.read_text())
    for section in ("dependencies", "devDependencies"):
        for name, current in package[section].items():
            if name in FROM_HA_FRONTEND:
                newest = ha_packages[name].lstrip("^~")
            else:
                newest = fetch_json(NPM_LATEST.format(name=name))["version"]
            note_change(changes, name, current, newest)
            package[section][name] = newest
    PACKAGE_JSON.write_text(json.dumps(package, indent=2) + "\n")

    for command in (["npm", "install"], ["npm", "update"]):
        subprocess.run(command, cwd=FRONTEND, check=True)


def update_actions(changes: list[str]) -> None:
    """Update the GitHub actions that are pinned to a version.

    A pin keeps its precision: `v7` follows the major version, `v10.3.3` the
    whole version. Actions on a branch are left as they are.
    """
    newest: dict[str, str] = {}
    update = partial(update_action_pin, newest, changes)
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        workflow.write_text(ACTION_PIN.sub(update, workflow.read_text()))


def update_action_pin(
    newest: dict[str, str], changes: list[str], match: re.Match[str]
) -> str:
    """Return the pin of an action with its newest release, at the same precision.

    `newest` keeps the releases already looked up.
    """
    repository, current = match.group(2), match.group(3)
    if repository not in newest:
        release = fetch_json(GITHUB_RELEASE.format(repository=repository))
        newest[repository] = release["tag_name"]
    parts = current.count(".") + 1
    version = ".".join(newest[repository].split(".")[:parts])
    note_change(changes, repository, current, version)
    return f"{match.group(1)}{repository}@{version}"


def requirement_pins(requirements: list[str]) -> dict[str, str]:
    """Return the exact pins in a list of requirements, by package name."""
    return {
        match.group(1).lower(): match.group(2)
        for requirement in requirements
        if (match := re.match(r"([\w.-]+)==([^\s;]+)", requirement))
    }


def pinned(text: str, name: str) -> str:
    """Return the version `name` is pinned to in a text."""
    match = re.search(rf"{re.escape(name)}==([\w.]+)", text)
    if match is None:
        raise ValueError(f"No pin for {name}")
    return match.group(1)


def replace_version(
    text: str, pattern: str, name: str, version: str, changes: list[str]
) -> str:
    """Replace the version in the line that matches `pattern`, and note it.

    The first group of `pattern` is the version.
    """
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"No line for {name}")
    note_change(changes, name, match.group(1), version)
    return text[: match.start(1)] + version + text[match.end(1) :]


def note_change(changes: list[str], name: str, current: str, newest: str) -> None:
    if current != newest:
        changes.append(f"{name}: {current} → {newest}")


def read_core(version: str, path: str) -> str:
    return fetch_text(CORE_FILE.format(version=version, path=path))


def fetch_json(url: str) -> Any:
    return json.loads(fetch_text(url))


def fetch_text(url: str) -> str:
    """Return the text at the URL, with the GitHub token when one is set."""
    request = urllib.request.Request(url)
    if url.startswith("https://api.github.com") and (
        token := os.environ.get("GITHUB_TOKEN")
    ):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


if __name__ == "__main__":
    main()
