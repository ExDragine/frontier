"""Playground plugin registration; matchers and handlers live in ``commands``."""

if globals().get("__plugin__") is not None:
    from . import commands as commands
