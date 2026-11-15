"""Draft a charger profile and its test for each charger filled in by hand in a diagnostics file.

uv run python -m diagnostics.charger_profile <diagnostics file> [--output <folder>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

from ..diagnostics_file import NotADiagnosticsFileError, read_diagnostics_file
from .draft import ProfileDraft, draft_profiles
from .source import profile_source, profile_test_source

REPOSITORY: Final = Path(__file__).resolve().parents[2]
PROFILES: Final = Path("custom_components/kraftvakt/charger_profiles/profiles")
PROFILE_TESTS: Final = Path("tests/charger_profiles/profiles")


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m diagnostics.charger_profile", description=(__doc__ or "").splitlines()[0])
    parser.add_argument("file", type=Path, help="the JSON file from Download diagnostics")
    parser.add_argument("--output", type=Path, default=REPOSITORY, help="the folder to write into, where the repository's folders are made (default: this repository)")
    options = parser.parse_args(arguments)
    try:
        drafts = draft_profiles(read_diagnostics_file(options.file))
    except NotADiagnosticsFileError as error:
        print(error, file=sys.stderr)
        return 1
    for skipped in drafts.skipped:
        print(skipped)
    for draft in drafts.profiles:
        _write(draft, options.output)
    if drafts.profiles:
        print(f"Review each draft, run ruff format, and add the profiles to PROFILES in {PROFILES / '__init__.py'}.")
    else:
        print("No charger in the file is filled in by hand.")
    return 0


def _write(draft: ProfileDraft, output: Path) -> None:
    files = {PROFILES / f"{draft.module}.py": profile_source(draft), PROFILE_TESTS / f"test_{draft.module}.py": profile_test_source(draft)}
    existing = [path for path in files if (output / path).exists()]
    print(f"\nCharger {draft.charger_id}: {draft.profile.name}")
    for note in draft.notes:
        print(f"  - {note}")
    if existing:
        print(f"  Not written, since {', '.join(map(str, existing))} exists.")
        return
    for path, source in files.items():
        (output / path).parent.mkdir(parents=True, exist_ok=True)
        (output / path).write_text(source, encoding="utf-8")
        print(f"  Wrote {path}")


if __name__ == "__main__":
    sys.exit(main())
