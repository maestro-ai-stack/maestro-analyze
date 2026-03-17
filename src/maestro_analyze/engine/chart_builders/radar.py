"""Radar chart for multi-dimensional comparison."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class RadarBuilder(BaseChartBuilder):
    name = "radar"
    description = "雷达图 (categories, values)"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        cats = df[x].tolist()
        vals = df[y].tolist()
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", name=y or "value",
        ))
        fig.update_layout(title=title or "Radar Chart",
                          polar=dict(radialaxis=dict(visible=True)))
        return fig
