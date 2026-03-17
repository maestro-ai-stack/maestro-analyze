"""Line chart with shaded event/period bands."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ._base import BaseChartBuilder


class EventBandChartBuilder(BaseChartBuilder):
    """Line chart with vertical shaded bands marking historical periods.

    Standard in applied economics for annotating policy changes, wars,
    or treatment windows on time-series plots.
    """

    name = "event_band"
    description = "Line chart with shaded event/period bands"

    def build(
        self,
        *,
        df: pd.DataFrame,
        time_col: str = "year",
        value_col: str = "value",
        entity_col: str | None = None,
        events: list[dict[str, Any]] | None = None,
        title: str = "",
        **kw: Any,
    ) -> go.Figure:
        if entity_col and entity_col in df.columns:
            fig = px.line(df, x=time_col, y=value_col, color=entity_col,
                          title=title or "Event Band Chart")
        else:
            fig = px.line(df, x=time_col, y=value_col,
                          title=title or "Event Band Chart")

        for ev in (events or []):
            fig.add_vrect(
                x0=ev.get("start", ev.get("x0")),
                x1=ev.get("end", ev.get("x1")),
                fillcolor=ev.get("color", "rgba(100,100,100,0.15)"),
                opacity=ev.get("opacity", 0.3),
                layer="below",
                line_width=0,
                annotation_text=ev.get("name", ""),
                annotation_position="top left",
                annotation_font_size=10,
            )

        fig.update_layout(hovermode="x unified")
        return fig
