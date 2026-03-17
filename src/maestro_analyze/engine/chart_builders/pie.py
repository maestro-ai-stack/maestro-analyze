"""Pie chart for proportional composition."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class PieBuilder(BaseChartBuilder):
    name = "pie"
    description = "饼图"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              values: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.pie(df, names=names, values=values, title=title or "Pie Chart")
