"""Print how often each appliance and EV charger, and each entity the regulation reads, changed in the recorded history of a diagnostics file.

uv run python -m diagnostics.switching <diagnostics file>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..diagnostics_file import NotADiagnosticsFileError, read_diagnostics_file
from .changes import history_changes
from .report import report_text


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m diagnostics.switching", description=(__doc__ or "").splitlines()[0])
    parser.add_argument("file", type=Path, help="the JSON file from Download diagnostics")
    options = parser.parse_args(arguments)
    try:
        changes = history_changes(read_diagnostics_file(options.file))
    except NotADiagnosticsFileError as error:
        print(error, file=sys.stderr)
        return 1
    print(report_text(changes), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
