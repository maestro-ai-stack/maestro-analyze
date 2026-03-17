"""Data table rendered as a Plotly Table."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class TableBuilder(BaseChartBuilder):
    name = "table"
    description = "数据表格"

    def build(self, *, df: pd.DataFrame, title: str = "", **kw: Any) -> go.Figure:
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df.columns)),
            cells=dict(values=[df[c].tolist() for c in df.columns]),
        )])
        fig.update_layout(title=title)
        return fig
