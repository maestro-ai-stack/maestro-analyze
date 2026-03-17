"""Horizontal lollipop chart for ranked categories."""
from __future__ import annotations

from typing import Any

import pandas as pd

from ._base import BaseChartBuilder
from ._svg_base import SVG_DEFAULTS, _esc, _wrap, _to_html

_D = SVG_DEFAULTS


class LollipopBuilder(BaseChartBuilder):
    """Horizontal lollipop chart for ranked categories."""

    name = "lollipop"
    description = "Horizontal lollipop chart for ranked categories"

    def build(self, *, df: pd.DataFrame, category: str = "category", value: str = "value",
              color_col: str | None = None, title: str = "", **kw: Any) -> str:
        ROW_H, ML, MR, MT, MB = 24, 140, 80, 40, 20
        work = df.sort_values(value, ascending=True).reset_index(drop=True)
        n = len(work)
        W = kw.get("width", 700)
        H = MT + n * ROW_H + MB
        vmax = float(work[value].max()) if n else 1
        pw = W - ML - MR
        pal = _D["palette"]
        p: list[str] = []
        for i, row in work.iterrows():
            y = MT + int(i) * ROW_H + ROW_H // 2
            v = float(row[value])
            x_end = ML + (v / vmax * pw if vmax > 0 else 0)
            ci = (hash(str(row[color_col])) % len(pal)) if color_col and color_col in work.columns else int(i) % len(pal)
            col = pal[ci]
            p.append(f'<line x1="{ML}" y1="{y}" x2="{x_end:.1f}" y2="{y}" stroke="{col}" stroke-width="2"/>')
            p.append(f'<circle cx="{x_end:.1f}" cy="{y}" r="5" fill="{col}"/>')
            p.append(f'<text x="{ML-6}" y="{y+4}" text-anchor="end" font-size="10" '
                     f'fill="{_D["text_color"]}">{_esc(str(row[category]))}</text>')
            p.append(f'<text x="{x_end+8:.1f}" y="{y+4}" font-size="10" fill="{_D["axis_color"]}">{v:g}</text>')
        return _wrap(p, W, H, title)

    def to_html(self, **kw: Any) -> str:
        return _to_html(self.build(**kw), kw.get("title", ""))
