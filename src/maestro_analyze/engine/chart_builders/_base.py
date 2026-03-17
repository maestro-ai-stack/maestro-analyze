"""Base class for all chart builders."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import plotly.graph_objects as go


class BaseChartBuilder(ABC):
    """Abstract base for chart builders.

    Subclasses must define:
        name: str           -- registry key (e.g. "bar", "bump")
        description: str    -- one-line description
        build(**kwargs)     -- returns go.Figure (Plotly) or str (SVG)
    """

    name: str
    description: str

    @abstractmethod
    def build(self, **kwargs: Any) -> go.Figure | str:
        ...
