"""Line chart for trends over time."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class LineBuilder(BaseChartBuilder):
    name = "line"
    description = "折线图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.line(df, x=x, y=y, color=color, title=title)
