"""Treemap for hierarchical proportions."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class TreemapBuilder(BaseChartBuilder):
    name = "treemap"
    description = "树图 (names, parents, values)"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              parents: str | None = None, values: str | None = None,
              color: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        kwargs: dict[str, Any] = {"title": title or "Treemap"}
        if names:
            kwargs["names"] = names
        if parents and parents in df.columns:
            kwargs["parents"] = parents
        if values and values in df.columns:
            kwargs["values"] = values
        if color and color in df.columns:
            kwargs["color"] = color
        return px.treemap(df, **kwargs)
