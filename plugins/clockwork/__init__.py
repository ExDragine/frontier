"""Clockwork plugin registration.

Runtime wiring lives in ``runtime``: it builds the scheduler manager, imports the
command handlers and registers the lifecycle hooks.  Importing this package
without the NoneBot plugin loader therefore has no side effects, while the
``task_manager`` re-exports below keep the established
``from plugins.clockwork import task_manager`` call sites working.
"""

if globals().get("__plugin__") is not None:
    from . import runtime as runtime
    from .runtime import engine as engine
    from .runtime import task_executor as task_executor
    from .runtime import task_manager as task_manager
    from .runtime import task_manager_instance as task_manager_instance
