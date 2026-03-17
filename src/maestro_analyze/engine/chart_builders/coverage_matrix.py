"""Coverage/completeness heatmap (entity x time)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class CoverageMatrixBuilder(BaseChartBuilder):
    """Heatmap for data completeness (entity x time period).

    Reveals gaps in panel datasets: which entities have data in which
    years. Dark = missing, bright = dense coverage.
    """

    name = "coverage_matrix"
    description = "Coverage/completeness heatmap (entity x time)"

    def build(
        self,
        *,
        df: pd.DataFrame,
        entity: str = "entity",
        time_col: str = "year",
        count_col: str | None = None,
        title: str = "",
        **kw: Any,
    ) -> go.Figure:
        if count_col and count_col in df.columns:
            pivot = df.pivot_table(
                index=entity, columns=time_col, values=count_col, aggfunc="sum"
            ).fillna(0)
        else:
            pivot = df.pivot_table(
                index=entity, columns=time_col, values=df.columns[0], aggfunc="count"
            ).fillna(0)

        # sort by total coverage descending
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

        colorscale = [
            [0.0, "#1a1a2e"],
            [0.01, "#16213e"],
            [0.3, "#0f3460"],
            [0.6, "#4e79a7"],
            [1.0, "#76b7b2"],
        ]

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[str(c) for c in pivot.columns],
            y=[str(r) for r in pivot.index],
            colorscale=colorscale,
            hoverongaps=False,
            colorbar=dict(title="Count"),
        ))

        fig.update_layout(
            title=title or "Data Coverage Matrix",
            xaxis_title=str(time_col),
            yaxis=dict(autorange="reversed"),
            height=max(300, len(pivot) * 16 + 100),
        )
        return fig
