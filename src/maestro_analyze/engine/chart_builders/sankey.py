"""Sankey diagram for flow visualization."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class SankeyBuilder(BaseChartBuilder):
    name = "sankey"
    description = "桑基图 (source, target, value)"

    def build(self, *, df: pd.DataFrame, source: str | None = None,
              target: str | None = None, values: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        src_col = source or "source"
        tgt_col = target or "target"
        val_col = values or "value"

        all_labels = list(dict.fromkeys(
            df[src_col].tolist() + df[tgt_col].tolist()
        ))
        idx = {label: i for i, label in enumerate(all_labels)}
        vals = df[val_col].tolist() if val_col in df.columns else [1] * len(df)

        fig = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, label=all_labels),
            link=dict(
                source=[idx[s] for s in df[src_col]],
                target=[idx[t] for t in df[tgt_col]],
                value=vals,
            ),
        ))
        fig.update_layout(title=title or "Sankey Diagram")
        return fig
