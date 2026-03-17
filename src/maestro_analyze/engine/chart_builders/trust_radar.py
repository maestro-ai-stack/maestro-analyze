"""Multi-axis radar for entity scoring across dimensions."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class TrustRadarBuilder(BaseChartBuilder):
    """Multi-axis radar chart for scoring entities across dimensions.

    Used for composite index visualization (data quality scores,
    institutional ratings, multi-criteria assessments).
    """

    name = "trust_radar"
    description = "Multi-axis radar for entity scoring across dimensions"

    def build(
        self,
        *,
        df: pd.DataFrame,
        entity: str = "entity",
        dimensions: list[str] | None = None,
        title: str = "",
        **kw: Any,
    ) -> go.Figure:
        dims = dimensions or [
            c for c in df.select_dtypes(include="number").columns
            if c != entity
        ]
        if not dims:
            raise ValueError("No numeric dimension columns found")

        fig = go.Figure()
        palette = [
            "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
            "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
        ]

        for i, (_, row) in enumerate(df.iterrows()):
            vals = [float(row[d]) if pd.notna(row.get(d)) else 0 for d in dims]
            vals_closed = vals + [vals[0]]
            theta_closed = list(dims) + [dims[0]]

            fig.add_trace(go.Scatterpolar(
                r=vals_closed,
                theta=theta_closed,
                fill="toself",
                name=str(row.get(entity, f"Entity {i}")),
                line=dict(color=palette[i % len(palette)]),
                opacity=0.7,
            ))

        fig.update_layout(
            title=title or "Trust Radar",
            polar=dict(radialaxis=dict(visible=True, range=[0, None])),
            showlegend=True,
        )
        return fig
