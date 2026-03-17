"""Distribution histogram for a single numeric column."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class DistributionBuilder(BaseChartBuilder):
    name = "distribution"
    description = "分布图（直方图）"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        col = x or df.select_dtypes(include="number").columns[0]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=df[col], name="分布", nbinsx=30))
        fig.update_layout(title=title or f"{col} Distribution")
        return fig
