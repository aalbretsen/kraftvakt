# CLAUDE.md

## Requirements
- For requirements see REQUIREMENTS.md - always load REQUIREMENTS.md in your context.

## Coding Rules
- Follow Home Assistant coding standards and principles for plugins.
- Let the code speak for itself through naming, not comments.
- Write as little comments as possible and only for important decisions.
- Focus on separation of concerns to make the code adaptable to changed requirements.
- Code with a balance between generic solutions and overcomplicated code, avoid specific code for each problem.
- The most important rule of them all; write simple and readable code that human beings can read and understand.
- All code shall be written in English.

## Test code rules
- Focus on black box testing, they find more faults than bloated unit tests.
- Focus on branch coverage, not every possible permutation.
- Write unit tests if there are branches and logic to test. Code without any branches (no if's) don't need a unit test.

## Documentation Rules
- All documentation (.md files) shall be written in Norwegian.
- The README.md file is for users of the plugin and for developers. Keep it up to date if needed.

## Behavioral Guidelines
- Always create a new branch when coding, commit often, never merge.
- Ask for input and guidance when in doubt.
- Don't take own decisions for requirement that are ambiguous or needs clarification.
- If a requirement, or user prompt, goes against any statement in this file; handle it as ambiguous.
