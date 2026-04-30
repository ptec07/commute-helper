# AGENTS.md

## Design System
Always read `DESIGN.md` before making visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
In QA mode, flag UI code that does not match `DESIGN.md`.

## Coding workflow
When the task is coding, implementation, bug fixing, or vibe-coding:

1. Write or update the test first.
2. Run the targeted test and confirm it fails for the expected reason.
3. Only then write the implementation code.
4. Re-run the targeted test to confirm it passes.
5. Run a broader relevant test command before claiming completion.
6. In the final report, state which tests failed first and which tests passed after the change.

Do not skip the failing-test step unless the user explicitly says not to use TDD.
