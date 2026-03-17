"""基础图表构建器: bar, line, scatter, histogram, pie, box, table。"""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class BarBuilder:
    name = "bar"
    description = "柱状图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.bar(df, x=x, y=y, color=color, title=title)


class LineBuilder:
    name = "line"
    description = "折线图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.line(df, x=x, y=y, color=color, title=title)


class ScatterBuilder:
    name = "scatter"
    description = "散点图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              text: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.scatter(df, x=x, y=y, color=color, text=text, title=title)


class HistogramBuilder:
    name = "histogram"
    description = "直方图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.histogram(df, x=x, title=title)


class PieBuilder:
    name = "pie"
    description = "饼图"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              values: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.pie(df, names=names, values=values, title=title or "Pie Chart")


class BoxBuilder:
    name = "box"
    description = "箱线图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.box(df, x=x, y=y, title=title)


class TableBuilder:
    name = "table"
    description = "数据表格"

    def build(self, *, df: pd.DataFrame, title: str = "", **kw: Any) -> go.Figure:
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df.columns)),
            cells=dict(values=[df[c].tolist() for c in df.columns]),
        )])
        fig.update_layout(title=title)
        return fig


__all_charts__ = [
    BarBuilder, LineBuilder, ScatterBuilder, HistogramBuilder,
    PieBuilder, BoxBuilder, TableBuilder,
]
