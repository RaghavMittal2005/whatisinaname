# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

"""
Hoja Traffic Signal Control Environment.

Supporting lazy-loading of submodules to prevent circular dependencies
and ensure compatibility with beartype initialization hooks.
"""

__version__ = "0.1.0"

def __getattr__(name: str):
    """Lazy-load modules on access to avoid circular imports."""
    if name in ("HojaAction", "HojaObservation", "HojaState"):
        from .app.models import HojaAction, HojaObservation, HojaState
        objs = {
            "HojaAction": HojaAction, 
            "HojaObservation": HojaObservation, 
            "HojaState": HojaState
        }
        return objs[name]
        
    if name == "HojaEnv":
        from .client import HojaEnv
        return HojaEnv
        
    if name == "HojaEnvironment":
        from .app.environment import HojaEnvironment
        return HojaEnvironment

    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = ["HojaAction", "HojaObservation", "HojaState", "HojaEnv", "HojaEnvironment"]
