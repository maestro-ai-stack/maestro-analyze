"""Chart builder registry with auto-discovery.

Built-in charts are auto-imported from this package.
External plugins loaded from ~/.maestro/analyst/plugins/charts/.
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from maestro_analyze.core.registry import Registry

# Create the chart registry
charts = Registry("charts")

# Auto-discover all built-in chart modules in this package.
# Any class with name + build attributes gets registered.
_pkg_path = Path(__file__).parent
for _finder, _name, _ispkg in pkgutil.iter_modules([str(_pkg_path)]):
    if _name.startswith("_"):
        continue
    _mod = importlib.import_module(f".{_name}", __package__)
    for _attr in dir(_mod):
        _obj = getattr(_mod, _attr)
        if (isinstance(_obj, type)
                and hasattr(_obj, "name")
                and hasattr(_obj, "build")
                and _obj.__module__ == _mod.__name__):
            charts.register(_obj)

# Load external plugins
charts.load_plugins(Path.home() / ".maestro" / "analyst" / "plugins" / "charts")

# Public API
REGISTRY = charts._items  # backward compat


def get_builder(name: str):
    """Return an instantiated builder by chart type name."""
    return charts.get(name)()


def list_builders() -> list[str]:
    """List all registered chart type names."""
    return charts.names()


__all__ = ["charts", "REGISTRY", "get_builder", "list_builders"]
