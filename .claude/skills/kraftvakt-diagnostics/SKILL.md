---
name: kraftvakt-diagnostics
description: The diagnostics tools in diagnostics/ - developer tools that read the file from Kraftvakt's Download diagnostics, an HTML document of the file and the charger profile
  extractor that drafts a charger profile and its test. Where they live and why, the concepts they share, how they are coded, tested and documented, and how to add a tool.
  Use before changing or adding anything in diagnostics/, tests/diagnostics/ or tests/unit/diagnostics/, when using the tools on a diagnostics file,
  or before changing the sections of the diagnostics they read.
---

# Kraftvakt diagnostics tools

The tools help a developer read a diagnostics file, for example one from a bug report, and turn it into code. They are for development only and never shipped to users.
`DIAGNOSTICS.md` in the repository root tells developers how to run them; keep it up to date with the code. The README only links to it.

## Where they live

- `diagnostics/` in the repository root is a Python package, outside `custom_components/`, so HACS never installs it and hassfest never reads it.
  A tool runs from the repository root as a module, `uv run python -m diagnostics.<tool>`, so the package and `custom_components` are both importable.
- A tool may import from the integration, for example the charger profile dataclasses and `read_config`, so its output is checked against the real types and rules.
  It uses no dependencies beyond the development environment; ask the owner before adding one.
- `diagnostics` is in mypy's `files` in `pyproject.toml`. `custom_components` is a namespace package both in the root and in `simulator/`,
  so mypy takes module names from those folders (`explicit_package_bases` and `mypy_path`), as the tools import the integration by its full name.
- The tests are in `tests/diagnostics/` (black box) and `tests/unit/diagnostics/`, and are part of the normal test run and its coverage, CI included.

## Concepts

- **Diagnostics file:** what **Download diagnostics** gives. Home Assistant wraps Kraftvakt's diagnostics under `data`, next to its own sections such as `home_assistant`,
  `custom_components`, `integration_manifest`, `setup_times` and `issues`. The tools take the whole file; `diagnostics_file.py` reads it into a `DiagnosticsFile`
  with `data` and `wrapper`, and refuses a file that is not JSON or has no `data` object.
- **What a tool may depend on:** the wrapper, and in `data` only `config` and `charger_devices`. The other sections of `data` change as the backend changes,
  so a tool shows them generically or leaves them alone. A change to `config` or `charger_devices` in `diagnostics.py` must keep the tools working;
  their tests fail when it does not.
- **Filled in by hand:** an EV charger in `config` whose device in `charger_devices` has no `profile`.
- **Draft:** what the charger profile extractor writes. A developer reviews it before it is committed; the tool never edits `PROFILES` or writes over a file.
- **Note:** a line the extractor prints under an EV charger, naming the field and what a profile cannot carry over. Every case the tool cannot map gives a note.

## HTML document (`to_html.py`)

- Every section, of `data` and of the wrapper, is rendered by the same rules, without code for any section. Why: sections added to the diagnostics show up by themselves.
- One expand/collapse mechanism, native `<details>`, for every object and list. A plain value, or an empty object or list, is one line.
  The first levels below a section are open (`OPEN_LEVELS`). The items of a list are labelled by their index and the values of `NAMING_KEYS`.
- A list of objects whose values are flat (plain, or a list or object of plain values) or hold only flat values is a table with a column for every key, in the order first seen.
  In a cell each item of a list or object is a line, and a nested flat value is one line with commas. Other lists are trees.
- One navigation: the sticky header links to each section, grouped as the integration's diagnostics and Home Assistant's wrapper.
  The only script is the inline `onclick` of **Expand all** and **Collapse all**.
- Strings are shown as they are; any other plain value as JSON, marked `literal`, so `"null"` is not taken for `null`. Every key and value is escaped.
- The document is self-contained: inline CSS with system colours, so it follows light and dark mode, and no external resources.

## Charger profile extractor (`charger_profile/`)

- `draft.py` turns each EV charger filled in by hand into a `ChargerProfile` and notes; `source.py` writes the profile module and its test as Python source;
  `__main__.py` writes the files and prints the notes.
- An entity is found as the backend finds it: `DeviceEntities` in `recognition.py` takes any `RegisteredEntity`, so the described entities of the file go through the same code.
  An entity is given by its translation key, else the integration's own name, else as the main entity. One that is not the only fit, or is disabled, is still drafted, with a note.
- EV chargers with the same `DeviceMatch` give one draft, from the first of them.
- `DeviceMatch` names the manufacturer and model ID only for the integrations in `SHARED_INTEGRATIONS`, those that serve devices of many makers.
  The profile's name is the manufacturer and model, with the integration in parentheses for those integrations; the module is its slug.
- Templates: each entity of the device becomes a `$name` placeholder named by its translation key or name, unique and a valid keyword argument,
  and a `$` already in the template becomes `$$`. Quoted entity IDs left in the template are noted as entities from another device.
- Script steps: a `device_id` equal to the charger's device becomes `{{ device_id(entity_id) }}`, and an `entity_id` equal to the charger's entity becomes `{{ entity_id }}`.
  Other devices and entities, and entities of the device inside larger strings, are noted. A domain action becomes the script steps `domain_action_steps` gives.
- A field that is not set, or cannot be found, is written as an empty action (`custom_action()`) or an empty condition (`ProfileCondition(ConditionType.ENTITY)`),
  which fill nothing.
- The drafted test registers the device with every entity of the file, named `TEST_DEVICE_NAME`, and expects the fields `DeviceEntities.fields` gives for the entity IDs
  the test harness makes from the device and entity names. The source is not formatted; the developer runs ruff on it.

## How to write code for the tools

- The coding rules in `CLAUDE.md` apply. Keep the reading of the file in `diagnostics_file.py`, the logic in plain functions and classes, and printing and files in `main`.
- Use the integration's own types and functions rather than copying its rules, and make a small, general change in the integration when a tool needs one.
- Each tool has `main(arguments: list[str] | None = None) -> int`, which prints `NotADiagnosticsFileError` to stderr and returns 1, and ends with `sys.exit(main())`
  under `if __name__ == "__main__"`.

## Testing

- `tests/diagnostics/conftest.py` gives `diagnostics_file`: Kraftvakt in the test harness with an EV charger filled in by hand on a registered device,
  downloaded with Home Assistant's wrapper through `_get_diagnostics_for_config_entry`. Black box tests run the tools on it, so a change of the format breaks them in CI.
  It re-exports the `command` fixture of the charger profile tests.
- The extractor's black box test loads the drafted files as modules of the packages they are drafted for (`drafted.py`), puts the drafted profile in `PROFILES`,
  and runs the drafted test against the real backend.
- Unit tests prove the rules by themselves, with diagnostics built as dictionaries: the notes and placeholders in `test_draft.py`, the written source read back
  as the same profile in `test_source.py`, and the rendering rules in `test_to_html.py`.
- Running a tool as a module is tested with `runpy`, after removing the module from `sys.modules`. Keep the tools at 100 % line coverage.

## How to add a tool

1. Add `diagnostics/<tool>.py`, or a package `diagnostics/<tool>/` with `__main__.py` when it needs several modules, with a module docstring that starts with
   what it does and shows the command.
2. Read the file with `read_diagnostics_file` and depend only on what the concepts above allow.
3. Test it on `diagnostics_file` in `tests/diagnostics/test_<tool>.py`, and its rules in `tests/unit/diagnostics/`.
4. Add a section with the command and what the tool gives to `DIAGNOSTICS.md`, and describe its decisions in this skill.
