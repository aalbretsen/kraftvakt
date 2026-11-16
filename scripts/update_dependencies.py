"""Update every pinned dependency of Kraftvakt to its newest compatible version.

Home Assistant decides most of the versions, so they follow one chain:

- pytest-homeassistant-custom-component, newest release: Home Assistant and the
  pytest packages it pins,
- that Home Assistant release: the Home Assistant frontend, ruff, mypy, the
  lowest Python and the Python versions it supports,
- that Home Assistant frontend release: Node, Lit, TypeScript and @mdi/js.

The other build tools of the panel and the GitHub actions get their newest
release. Run from the repository root, with Node active:

    uv run scripts/update_dependencies.py

The script asks before it changes the Python used for development to the
newest Home Assistant supports, which also makes .venv again, and before it
changes Node to the one the Home Assistant frontend uses. It tells when a newer
Node LTS release exists. Everything else is updated without asking. At the end
it prints what changed, and asks whether to run scripts/build.py, which installs
and checks the result. When Node changed, activate the new one with nvm first.
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

import build

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
FRONTEND_FILE = "https://raw.githubusercontent.com/home-assistant/frontend/{version}/{path}"
PYPI = "https://pypi.org/pypi/{name}/json"
PYPI_RELEASE = "https://pypi.org/pypi/{name}/{version}/json"
NPM_LATEST = "https://registry.npmjs.org/{name}/latest"
GITHUB_RELEASE = "https://api.github.com/repos/{repository}/releases/latest"
FRONTEND_MANIFEST = "homeassistant/components/frontend/manifest.json"
NODE_RELEASES = "https://nodejs.org/dist/index.json"
ACTION_PIN = re.compile(r"(uses: )([\w.-]+/[\w.-]+)@(v[\d.]+)")
# Where the minor version of the Python used for development is written, as the
# first group of each pattern.
DEVELOPMENT_PYTHON = (
    (PYPROJECT, r'^python_version = "3\.(\d+)"$'),
    (PYPROJECT, r'^target-version = "py3(\d+)"$'),
    (WORKFLOWS / "ci.yml", r'python-version: "3\.(\d+)"'),
    (ROOT / "README.md", r"uv venv --python 3\.(\d+)"),
    (ROOT / ".claude" / "skills" / "kraftvakt-testing" / "SKILL.md", r"uv venv --python 3\.(\d+)"),
)


def main() -> None:
    """Update the dependencies and print what changed."""
    changes: list[str] = []
    pins = update_python(changes)
    update_python_version(pins["homeassistant"], changes)
    update_node(pins["home-assistant-frontend"], changes)
    update_panel(pins["home-assistant-frontend"], changes)
    update_actions(changes)
    print("\n".join(dict.fromkeys(changes)) or "Everything is up to date.")
    if ask("Build and run the checks now?"):
        build.main()


def update_python(changes: list[str]) -> dict[str, str]:
    """Update the Python development dependencies, and return their new pins."""
    harness = fetch_json(PYPI.format(name=TEST_HARNESS))["info"]
    pins = {TEST_HARNESS: harness["version"]}
    harness_pins = requirement_pins(harness["requires_dist"])
    pins |= {name: harness_pins[name] for name in FROM_TEST_HARNESS}
    ha_version = pins["homeassistant"]
    pins["home-assistant-frontend"] = pinned(read_core(ha_version, FRONTEND_MANIFEST), "home-assistant-frontend")
    pins["ruff"] = pinned(read_core(ha_version, "requirements_test_pre_commit.txt"), "ruff")
    pins["mypy"] = pinned(read_core(ha_version, "requirements_test.txt"), "mypy")

    text = REQUIREMENTS.read_text()
    for name, version in pins.items():
        text = replace_version(text, rf"^{re.escape(name)}==(\S+)$", name, version, changes)
    REQUIREMENTS.write_text(text)
    return pins


def update_python_version(ha_version: str, changes: list[str]) -> None:
    """Follow the lowest Python of Home Assistant, and offer its newest.

    The newest Python minor version the Home Assistant release supports is
    offered for development. Accepting it updates the files that name it, and
    makes .venv again with it.
    """
    ha_release = fetch_json(PYPI_RELEASE.format(name="homeassistant", version=ha_version))["info"]
    PYPROJECT.write_text(
        replace_version(
            PYPROJECT.read_text(),
            r'^requires-python = "(\S+)"$',
            "Lowest Python",
            ha_release["requires_python"],
            changes,
        )
    )
    supported = (re.fullmatch(r"Programming Language :: Python :: 3\.(\d+)", classifier) for classifier in ha_release["classifiers"])
    newest = max(int(match.group(1)) for match in supported if match)
    written = [re.findall(pattern, path.read_text(), flags=re.MULTILINE) for path, pattern in DEVELOPMENT_PYTHON]
    if not all(written) or len({version for versions in written for version in versions}) != 1:
        raise ValueError("The Python used for development is not the same in every file that names it")
    current = int(written[0][0])
    if newest == current or not ask(f"Home Assistant {ha_version} supports Python 3.{newest}, development uses 3.{current}. Change to 3.{newest} and make .venv again?"):
        return
    for path, pattern in DEVELOPMENT_PYTHON:
        path.write_text(re.sub(pattern, partial(replace_group, str(newest)), path.read_text(), flags=re.MULTILINE))
    note_change(changes, "Python for development", f"3.{current}", f"3.{newest}")
    subprocess.run(["uv", "venv", "--clear", "--python", f"3.{newest}"], cwd=ROOT, check=True)


def update_node(frontend_version: str, changes: list[str]) -> None:
    """Offer the Node the Home Assistant frontend uses, and tell of a newer LTS."""
    current = NVMRC.read_text().strip()
    node = fetch_text(FRONTEND_FILE.format(version=frontend_version, path=".nvmrc")).strip()
    lts = next(release["version"] for release in fetch_json(NODE_RELEASES) if release["lts"])
    if major(lts) > major(node):
        print(f"Node {lts.removeprefix('v')} is the newest LTS release. Kraftvakt follows the Home Assistant frontend, which uses Node {node}.")
    if node != current and ask(f"The Home Assistant frontend uses Node {node}, development uses {current}. Change to {node}?"):
        note_change(changes, "Node", current, node)
        NVMRC.write_text(f"{node}\n")


def update_panel(frontend_version: str, changes: list[str]) -> None:
    """Update the panel's packages, and refresh the lock file."""
    ha_frontend = json.loads(fetch_text(FRONTEND_FILE.format(version=frontend_version, path="package.json")))
    ha_packages = {**ha_frontend["dependencies"], **ha_frontend["devDependencies"]}
    package = json.loads(PACKAGE_JSON.read_text())
    for section in ("dependencies", "devDependencies"):
        for name, current in package[section].items():
            newest = ha_packages[name].lstrip("^~") if name in FROM_HA_FRONTEND else fetch_json(NPM_LATEST.format(name=name))["version"]
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


def update_action_pin(newest: dict[str, str], changes: list[str], match: re.Match[str]) -> str:
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
    return {match.group(1).lower(): match.group(2) for requirement in requirements if (match := re.match(r"([\w.-]+)==([^\s;]+)", requirement))}


def pinned(text: str, name: str) -> str:
    """Return the version `name` is pinned to in a text."""
    match = re.search(rf"{re.escape(name)}==([\w.]+)", text)
    if match is None:
        raise ValueError(f"No pin for {name}")
    return match.group(1)


def replace_version(text: str, pattern: str, name: str, version: str, changes: list[str]) -> str:
    """Replace the version in the line that matches `pattern`, and note it.

    The first group of `pattern` is the version.
    """
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"No line for {name}")
    note_change(changes, name, match.group(1), version)
    return text[: match.start(1)] + version + text[match.end(1) :]


def replace_group(value: str, match: re.Match[str]) -> str:
    """Return the text of the match with its first group replaced by `value`."""
    start, end = match.start(1) - match.start(), match.end(1) - match.start()
    return match.group()[:start] + value + match.group()[end:]


def major(version: str) -> int:
    return int(version.removeprefix("v").split(".")[0])


def ask(question: str) -> bool:
    return input(f"{question} [y/N] ").strip().lower() == "y"


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
    if url.startswith("https://api.github.com") and (token := os.environ.get("GITHUB_TOKEN")):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()


if __name__ == "__main__":
    main()
