"""Histogram for frequency distribution."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class HistogramBuilder(BaseChartBuilder):
    name = "histogram"
    description = "直方图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.histogram(df, x=x, title=title)
