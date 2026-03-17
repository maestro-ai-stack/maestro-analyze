"""Funnel chart for staged conversion data."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class FunnelBuilder(BaseChartBuilder):
    name = "funnel"
    description = "漏斗图"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              values: str | None = None, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        n_col = names or x
        v_col = values or y
        fig = go.Figure(go.Funnel(
            y=df[n_col].tolist(),
            x=df[v_col].tolist(),
            textinfo="value+percent previous",
        ))
        fig.update_layout(title=title or "Funnel")
        return fig
