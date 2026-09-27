# CLAUDE.md

## Requirements
For requirements see REQUIREMENTS.md

## Coding Rules
- Follow Home Assistand coding standards and principles for plugins
- Follow Martin Fowler's clean code principles and let the code speak for itself through naming not comments.
- Write as little comments as possible and only for important decisions.
- All code shall be written in English

## Test code rules
- Focus on black box testing, they find more faults than bloated unit tests.
- Focus on branch coverage, not every possible permutation.
- Write unit tests if there are branches and logic to test. Code without any branches (no if's) don't need a unit test.

## Documentation Rules
- All documentation (.md files) shall be written in Norwegian
- The README.md file is for users of the plugin and for developers. Keep it up to date if needed.

## Behavioral Guidelines
- Ask for input and guidance when in doubt.
- Don't take own decisions for requirement that are ambiguous or needs clarification.
- If a requirement goes against best practises, handle it as ambiguous.
