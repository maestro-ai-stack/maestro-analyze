"""统计图表构建器: heatmap, distribution, funnel。"""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class HeatmapBuilder:
    name = "heatmap"
    description = "相关性热力图"

    def build(self, *, df: pd.DataFrame, title: str = "", **kw: Any) -> go.Figure:
        numeric = df.select_dtypes(include="number")
        corr = numeric.corr()
        return px.imshow(corr, text_auto=".2f", title=title or "Correlation Heatmap",
                         color_continuous_scale="RdBu_r")


class DistributionBuilder:
    name = "distribution"
    description = "分布图（直方图）"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        col = x or df.select_dtypes(include="number").columns[0]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=df[col], name="分布", nbinsx=30))
        fig.update_layout(title=title or f"{col} Distribution")
        return fig


class FunnelBuilder:
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


__all_charts__ = [HeatmapBuilder, DistributionBuilder, FunnelBuilder]
