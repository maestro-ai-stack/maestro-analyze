"""Minimal inline sparkline (no axes)."""
from __future__ import annotations

from typing import Any

from ._base import BaseChartBuilder
from ._svg_base import _to_html


class SparklineBuilder(BaseChartBuilder):
    """Tiny inline chart with no axes or labels."""

    name = "sparkline"
    description = "Minimal inline sparkline (no axes)"

    def build(self, *, values: list[float | int], width: int = 120, height: int = 30,
              color: str = "#4e79a7", **kw: Any) -> str:
        if not values:
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"/>'
        vmin, vmax = min(values), max(values)
        span = vmax - vmin if vmax > vmin else 1
        pad, pw, ph, n = 2, width - 4, height - 4, len(values)
        pts = " ".join(f"{pad + (i / max(n-1,1)) * pw:.1f},"
                       f"{pad + (1 - (v - vmin) / span) * ph:.1f}"
                       for i, v in enumerate(values))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
                f'<polyline points="{pts}" fill="none" stroke="{color}" '
                f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>')

    def to_html(self, **kw: Any) -> str:
        return _to_html(self.build(**kw))
