"""Box plot for distribution summary."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class BoxBuilder(BaseChartBuilder):
    name = "box"
    description = "箱线图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.box(df, x=x, y=y, title=title)
