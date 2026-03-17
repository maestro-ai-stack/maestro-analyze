"""Word cloud from text column."""
from __future__ import annotations

import base64
import io
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class WordcloudBuilder(BaseChartBuilder):
    name = "wordcloud"
    description = "词云 (text column)"

    def build(self, *, df: pd.DataFrame, text: str | None = None,
              x: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        try:
            from wordcloud import WordCloud
        except ImportError:
            raise ImportError("词云需要 wordcloud 库: pip install wordcloud")

        col = text or x
        all_text = " ".join(df[col].dropna().astype(str).tolist())
        if not all_text.strip():
            from maestro_analyze.engine.chart_builders.table_view import TableBuilder
            return TableBuilder().build(df=df, title=title or "词云（无文本）")

        wc = WordCloud(width=900, height=400, background_color="#1a1a2e",
                       colormap="Blues", max_words=100).generate(all_text)
        buf = io.BytesIO()
        wc.to_image().save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        fig = go.Figure()
        fig.add_layout_image(dict(
            source=f"data:image/png;base64,{b64}",
            xref="paper", yref="paper", x=0, y=1,
            sizex=1, sizey=1, xanchor="left", yanchor="top", layer="above",
        ))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(title=title or "Word Cloud",
                          width=900, height=450, margin=dict(l=0, r=0, t=40, b=0))
        return fig
