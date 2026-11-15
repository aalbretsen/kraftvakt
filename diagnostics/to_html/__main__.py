"""Write a diagnostics file as a self-contained HTML document that is easier to read than the JSON.

uv run python -m diagnostics.to_html <diagnostics file> [--output <HTML file>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..diagnostics_file import NotADiagnosticsFileError, read_diagnostics_file
from .document import html_document


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m diagnostics.to_html", description=(__doc__ or "").splitlines()[0])
    parser.add_argument("file", type=Path, help="the JSON file from Download diagnostics")
    parser.add_argument("--output", type=Path, help="the HTML file to write (default: the diagnostics file with .html)")
    options = parser.parse_args(arguments)
    try:
        diagnostics = read_diagnostics_file(options.file)
    except NotADiagnosticsFileError as error:
        print(error, file=sys.stderr)
        return 1
    output: Path = options.output or options.file.with_suffix(".html")
    output.write_text(html_document(diagnostics, options.file.name), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
