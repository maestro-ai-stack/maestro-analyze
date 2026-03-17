"""Slope chart comparing two periods."""
from __future__ import annotations

from typing import Any

import pandas as pd

from ._base import BaseChartBuilder
from ._svg_base import SVG_DEFAULTS, _esc, _wrap, _to_html

_D = SVG_DEFAULTS


class SlopeChartBuilder(BaseChartBuilder):
    """Compares values between two periods. Green=increase, red=decrease."""

    name = "slope"
    description = "Slope chart comparing two periods"

    def build(self, *, df: pd.DataFrame, entity: str = "entity",
              start_value: str = "start_value", end_value: str = "end_value",
              start_label: str = "Before", end_label: str = "After",
              title: str = "", **kw: Any) -> str:
        W, H = kw.get("width", 500), kw.get("height", 400)
        ML, MR, MT, MB = 120, 120, 50, 30
        ph = H - MT - MB
        all_v = pd.concat([df[start_value], df[end_value]]).dropna()
        vmin, vmax = float(all_v.min()), float(all_v.max())
        span = vmax - vmin if vmax > vmin else 1
        xl, xr = ML, W - MR
        yf = lambda v: MT + (1 - (v - vmin) / span) * ph
        p: list[str] = []
        for lbl, x in [(start_label, xl), (end_label, xr)]:
            p.append(f'<text x="{x}" y="{MT-14}" text-anchor="middle" font-size="11" '
                     f'font-weight="bold" fill="{_D["axis_color"]}">{_esc(lbl)}</text>')
        for _, row in df.iterrows():
            sv, ev = float(row[start_value]), float(row[end_value])
            y1, y2 = yf(sv), yf(ev)
            col = "#2d6a4f" if ev >= sv else "#e15759"
            ent = _esc(str(row[entity]))
            p.append(f'<line x1="{xl}" y1="{y1:.1f}" x2="{xr}" y2="{y2:.1f}" '
                     f'stroke="{col}" stroke-width="2" opacity="0.7"/>')
            p.append(f'<circle cx="{xl}" cy="{y1:.1f}" r="4" fill="{col}"/>')
            p.append(f'<circle cx="{xr}" cy="{y2:.1f}" r="4" fill="{col}"/>')
            p.append(f'<text x="{xl-8}" y="{y1+4:.1f}" text-anchor="end" font-size="10" '
                     f'fill="{_D["text_color"]}">{ent} ({sv:g})</text>')
            p.append(f'<text x="{xr+8}" y="{y2+4:.1f}" text-anchor="start" font-size="10" '
                     f'fill="{_D["text_color"]}">({ev:g}) {ent}</text>')
        return _wrap(p, W, H, title)

    def to_html(self, **kw: Any) -> str:
        return _to_html(self.build(**kw), kw.get("title", ""))
