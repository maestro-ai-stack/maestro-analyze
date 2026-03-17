"""Correlation heatmap for numeric columns."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class HeatmapBuilder(BaseChartBuilder):
    name = "heatmap"
    description = "相关性热力图"

    def build(self, *, df: pd.DataFrame, title: str = "", **kw: Any) -> go.Figure:
        numeric = df.select_dtypes(include="number")
        corr = numeric.corr()
        return px.imshow(corr, text_auto=".2f", title=title or "Correlation Heatmap",
                         color_continuous_scale="RdBu_r")
