"""Stacked area chart for composition over time."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class StackedAreaBuilder(BaseChartBuilder):
    """Stacked area chart for composition over time.

    Shows how category shares evolve, common for crop mix, sectoral GDP,
    or energy source decomposition.
    """

    name = "stacked_area"
    description = "Stacked area chart for composition over time"

    def build(
        self,
        *,
        df: pd.DataFrame,
        time_col: str = "year",
        category_col: str = "category",
        value_col: str = "value",
        title: str = "",
        normalize: bool = False,
        **kw: Any,
    ) -> go.Figure:
        groupmode = "relative"
        if normalize:
            pivot = df.pivot_table(
                index=time_col, columns=category_col, values=value_col, aggfunc="sum"
            ).fillna(0)
            totals = pivot.sum(axis=1)
            pivot = pivot.div(totals, axis=0) * 100
            df_plot = pivot.reset_index().melt(
                id_vars=time_col, var_name=category_col, value_name=value_col
            )
        else:
            df_plot = df

        fig = px.area(
            df_plot, x=time_col, y=value_col, color=category_col,
            title=title or "Stacked Area",
            groupnorm="percent" if normalize else None,
        )
        fig.update_layout(hovermode="x unified")
        return fig
