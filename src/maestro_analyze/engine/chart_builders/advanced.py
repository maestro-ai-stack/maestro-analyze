"""高级图表构建器: bubble, sankey, treemap, wordcloud, radar。"""
from __future__ import annotations

import base64
import io
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class BubbleBuilder:
    name = "bubble"
    description = "气泡图 (x, y, size, color)"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, size: str | None = None,
              color: str | None = None, text: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        if size is None:
            numeric = [c for c in df.select_dtypes(include="number").columns
                       if c not in (x, y)]
            size = numeric[0] if numeric else None
        return px.scatter(df, x=x, y=y, size=size, color=color, text=text,
                          title=title or "Bubble Chart", size_max=60)


class SankeyBuilder:
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


class TreemapBuilder:
    name = "treemap"
    description = "树图 (names, parents, values)"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              parents: str | None = None, values: str | None = None,
              color: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        kwargs: dict[str, Any] = {"title": title or "Treemap"}
        if names:
            kwargs["names"] = names
        if parents and parents in df.columns:
            kwargs["parents"] = parents
        if values and values in df.columns:
            kwargs["values"] = values
        if color and color in df.columns:
            kwargs["color"] = color
        return px.treemap(df, **kwargs)


class WordcloudBuilder:
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
            from maestro_analyze.engine.chart_builders.basic import TableBuilder
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


class RadarBuilder:
    name = "radar"
    description = "雷达图 (categories, values)"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        cats = df[x].tolist()
        vals = df[y].tolist()
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", name=y or "value",
        ))
        fig.update_layout(title=title or "Radar Chart",
                          polar=dict(radialaxis=dict(visible=True)))
        return fig


__all_charts__ = [
    BubbleBuilder, SankeyBuilder, TreemapBuilder, WordcloudBuilder, RadarBuilder,
]
