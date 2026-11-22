# Kraftvakt diagnostics tools

The diagnostics tools read the file that **Download diagnostics** on Kraftvakt's integration page gives, for example one attached to a bug report.
They are in `diagnostics/`, with their tests in `tests/diagnostics/` and `tests/unit/diagnostics/`. They are for developers, run from the repository root,
and are not part of a release.

The file is Home Assistant's wrapper, with its own system information, the custom integrations and Kraftvakt's manifest,
and Kraftvakt's diagnostics under `data`. The tools take the whole file as it is downloaded.

Both tools run in the development environment, see [Development](README.md#development).

## HTML document

```bash
uv run python -m diagnostics.to_html kraftvakt-diagnostics.json
```

writes `kraftvakt-diagnostics.html` next to the file, or where `--output` says. The document has no external resources, so it can be opened in any browser and passed on.

- The header links to each section of Kraftvakt's diagnostics and of Home Assistant's wrapper. **Expand all** and **Collapse all** open and close everything.
- Every object and list can be expanded and collapsed. The summary tells how many keys or items it holds, and the items of a list are named by their name, id,
  entity ID or time. The first levels are open when the document opens.
- A list of objects with plain values, such as the recent decisions or the entities of a device, is a table with a column for each key.
  In a cell, each item of a list or object is on a line of its own.
- Strings are shown as they are. Numbers, booleans, `null` and empty strings are shown as in JSON, in a monospace font.

Every section is shown by the same rules, so a section that is added to the diagnostics shows up without a change in the tool.

## Charger profile extractor

```bash
uv run python -m diagnostics.charger_profile kraftvakt-diagnostics.json
```

drafts a charger profile from each EV charger that the user has filled in by hand, that is an EV charger whose device has no charger profile.
It writes the profile module to `custom_components/kraftvakt/charger_profiles/profiles/` and its test to `tests/charger_profiles/profiles/`,
named after the manufacturer and model. `--output <folder>` writes them under another folder instead, in the same subfolders. An existing file is never written over.

The draft is a starting point, never a finished profile. For each draft:

1. Read the notes the tool prints under the EV charger. They tell what a profile cannot carry over, for example an entity from another device, an entity that is not
   the only one of its kind on the device, a disabled entity, or a field that is not set. The profile leaves such a field out or empty.
2. Check the profile against the integration's source, as the other profiles do: the name, the integration and devices it is for,
   and that the entities are found by translation keys the integration does not change.
3. Check that the test registers the device as the integration does. It lists the entities of the device in the file, with the names they had there,
   which follow the language of that Home Assistant when the integration translates them.
4. Run `uv run ruff format` and `uv run ruff check --fix` on the two files, add the profile to `PROFILES` in `charger_profiles/profiles/__init__.py`, and run the tests.

What the tool carries over:

- The device: the integration of the device, and also its manufacturer and model ID when the integration serves devices of many makers, such as MQTT or ZHA.
- Each entity: by its translation key, or by the name the integration gives it when there is no translation key, or as the main entity of the device when it has neither.
- How charging is turned on and off: the on/off entity, the actions to activate and deactivate, or **the charging current**.
- Actions: the default action of an entity of the device, and script steps. In script steps, the charger's own device is given by
  the variable `device_id`, so the profile works for every EV charger of its kind.
- Conditions: an entity or a power sensor of the device, or a template, with each entity of the device in the template as a `$name` placeholder.
- **Cloud-controlled EV charger**, and the **Start delay** when it differs from the default profile's.

EV chargers with the same kind of device give one draft, from the first of them.
