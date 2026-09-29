# Changelog

## Unreleased

- Added repository maintenance documentation and a local Markdown-link check.
- CI now checks Python formatting, local documentation links, and the bundled
  Markdown renderer in addition to lint, type, and test checks.
- Removed an unused callback payload from the usage accounting path while
  retaining the callback protocol required by LangChain.

Earlier implementation notes live in `docs/` and are retained as design
history. They are not a promise that every historical experiment remains
enabled in the current runtime.
