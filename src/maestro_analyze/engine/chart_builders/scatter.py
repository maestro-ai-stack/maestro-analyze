"""Scatter plot for bivariate relationships."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class ScatterBuilder(BaseChartBuilder):
    name = "scatter"
    description = "散点图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              text: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.scatter(df, x=x, y=y, color=color, text=text, title=title)
