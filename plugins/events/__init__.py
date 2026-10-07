"""Milky request event inbox; plain imports do not register matchers."""

if globals().get("__plugin__") is not None:
    from . import runtime as runtime
