# Agent Guidelines

## Engineering Practice

- Read the surrounding code before changing behavior. Prefer existing project patterns, helpers, tests, and module boundaries over introducing a new style.
- Keep code Pythonic: clear names, direct control flow, cohesive functions, idiomatic standard library use, and explicit data structures where they improve readability.
- Do not create many tiny one-off helper functions. Add a helper only when it is reused, isolates real complexity, represents a meaningful domain boundary, or materially improves testability.
- Prefer keeping straightforward logic inline when extracting it would force readers to jump around without reducing complexity.
- Keep changes scoped to the requested behavior. Avoid unrelated refactors, formatting churn, or API changes unless they are necessary to make the work correct.
- Preserve user or teammate changes already present in the worktree. Never revert unrelated changes without an explicit request.

## Verification

- Add or update focused tests when behavior changes, especially for shared utilities, agent wiring, tool registration, and user-facing workflows.
- Run the narrowest useful lint and test commands before reporting completion. Mention any commands that could not be run.
- Treat warnings and flaky failures as evidence to investigate, not as noise to hide.
