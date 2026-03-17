"""Bubble chart (scatter with size encoding)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class BubbleBuilder(BaseChartBuilder):
    name = "bubble"
    description = "气泡图 (x, y, size, color)"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, size: str | None = None,
              color: str | None = None, text: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        if size is None:
            numeric = [c for c in df.select_dtypes(include="number").columns
                       if c not in (x, y)]
            size = numeric[0] if numeric else None
        return px.scatter(df, x=x, y=y, size=size, color=color, text=text,
                          title=title or "Bubble Chart", size_max=60)
