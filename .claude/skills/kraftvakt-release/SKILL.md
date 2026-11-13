---
name: kraftvakt-release
description: How a Kraftvakt release is made - SemVer versions and how to bump them (major, minor, patch, pre-release), the release script that sets the version, commits,
  tags and pushes, the workflow that drafts the GitHub release, release notes, and how HACS offers releases and pre-releases.
  Use when asked to make, prepare or plan a release, to bump the version, or about tags, release notes or HACS versions.
---

# Releasing Kraftvakt

## Versions

- SemVer: `MAJOR.MINOR.PATCH`, optionally with a pre-release part such as `-beta.1`. The tag is `v` and the version, like `v0.2.0`.
- The current version is the one in `custom_components/kraftvakt/manifest.json`. The release script keeps `pyproject.toml`, `frontend/package.json` and its lock file the same.
  The simulator is for development only, is never released and keeps its own version.
- Bumping from the current version:
  - patch: `0.1.0` → `0.1.1`, for fixes only,
  - minor: `0.1.0` → `0.2.0`, for new features or changed behaviour; while the major version is 0, also for changes that break existing setups,
  - major: `0.4.2` → `1.0.0`,
  - a pre-release of the next version: `0.2.0-beta.1`, then `0.2.0-beta.2`,
  - the final release after pre-releases drops the pre-release part: `0.2.0-beta.2` → `0.2.0`.
    Ask the owner when the request does not say which, or when the current version is a pre-release and the request asks for a bump.

## Making a release

1. The work to release is merged into `main` by the owner.
2. Work out the new version, and check that `main` is clean and up to date and that the tag does not exist (`git tag --list`).
3. Draft the release notes for the owner from the changes since the last tag (`git log <last tag>..main`): what users of the integration notice, not how the code changed,
   in English. The owner writes the final notes.
4. Give the owner the command to run on `main`, with Node active:

   ```bash
   uv run scripts/release.py 0.2.0
   ```

   Claude does not run it: it commits and tags on `main` and pushes, which only the owner does.

The script stops unless the version is SemVer and not lower than the current one, the branch is a clean `main` that is not behind `origin/main`, and the tag is new.
It runs every check from the `kraftvakt-testing` skill, sets the version (only the version text, so the files keep their format),
commits "Release v<version>" when the version changed, makes an annotated tag, and asks before it pushes `main` and the tag in one atomic push.
When the answer is no, it prints how to push later or undo.

## On GitHub

The pushed tag starts `.github/workflows/release.yml`.
It checks that every version in the files matches the tag, and creates a draft release named "Kraftvakt <version>" with empty notes. The owner writes the notes and publishes it.
The workflow starts on the tag because a release created by a workflow does not start other workflows.

HACS installs only published GitHub releases, never tags or drafts. It treats a release as a pre-release by GitHub's pre-release flag, not by the version,
so the workflow sets the flag when the version has a pre-release part. HACS offers pre-releases only to users who turn on pre-releases for the repository.
