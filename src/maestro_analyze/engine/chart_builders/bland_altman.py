"""Bland-Altman agreement plot (mean vs difference)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class BlandAltmanBuilder(BaseChartBuilder):
    """Bland-Altman agreement plot between two measurement sources.

    Standard in validation studies: X = mean of two sources,
    Y = difference. Reference lines at mean difference +/- 1.96 SD
    define limits of agreement.
    """

    name = "bland_altman"
    description = "Bland-Altman agreement plot (mean vs difference)"

    def build(
        self,
        *,
        df: pd.DataFrame,
        source_a: str = "source_a",
        source_b: str = "source_b",
        label_col: str | None = None,
        title: str = "",
        **kw: Any,
    ) -> go.Figure:
        a = pd.to_numeric(df[source_a], errors="coerce")
        b = pd.to_numeric(df[source_b], errors="coerce")
        mask = a.notna() & b.notna()
        a, b = a[mask], b[mask]

        mean_ab = (a + b) / 2
        diff_ab = a - b
        mean_diff = float(diff_ab.mean())
        sd_diff = float(diff_ab.std())

        fig = go.Figure()
        text_vals = df.loc[mask, label_col].tolist() if label_col and label_col in df.columns else None

        fig.add_trace(go.Scatter(
            x=mean_ab, y=diff_ab, mode="markers",
            text=text_vals,
            marker=dict(size=6, color="#4e79a7", opacity=0.6),
            name="Observations",
        ))

        # reference lines
        x_range = [float(mean_ab.min()), float(mean_ab.max())]
        for val, label, color, dash in [
            (mean_diff, f"Mean: {mean_diff:.2f}", "#333", "dash"),
            (mean_diff + 1.96 * sd_diff, f"+1.96 SD: {mean_diff + 1.96 * sd_diff:.2f}", "#e15759", "dot"),
            (mean_diff - 1.96 * sd_diff, f"-1.96 SD: {mean_diff - 1.96 * sd_diff:.2f}", "#e15759", "dot"),
        ]:
            fig.add_hline(
                y=val, line_dash=dash, line_color=color,
                annotation_text=label, annotation_position="top right",
                annotation_font_size=10,
            )

        fig.update_layout(
            title=title or "Bland-Altman Plot",
            xaxis_title=f"Mean of {source_a} and {source_b}",
            yaxis_title=f"Difference ({source_a} - {source_b})",
            hovermode="closest",
        )
        return fig
