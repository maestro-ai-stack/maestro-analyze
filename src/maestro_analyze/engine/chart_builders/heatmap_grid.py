"""SVG 2D grid heatmap for entity x category."""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

from ._base import BaseChartBuilder
from ._svg_base import SVG_DEFAULTS, _esc, _wrap, _to_html

_D = SVG_DEFAULTS


class HeatmapGridBuilder(BaseChartBuilder):
    """2D grid heatmap for entity x time or any two categorical axes."""

    name = "heatmap_grid"
    description = "SVG 2D grid heatmap (entity x category)"

    def build(self, *, df: pd.DataFrame, row_label: str = "row_label",
              col_label: str = "col_label", value: str = "value",
              grade_col: str | None = None, title: str = "", **kw: Any) -> str:
        CW, CH, GAP = kw.get("cell_w", 18), kw.get("cell_h", 16), 1
        ML, MT = 120, 40
        rows = sorted(df[row_label].unique(), key=str)
        cols = sorted(df[col_label].unique(), key=str)
        grade_colors = {"exact":"#2d6a4f","pass":"#52b788","marginal":"#f4a261",
                        "fail":"#e76f51","skip":"#adb5bd"}
        vals = pd.to_numeric(df[value], errors="coerce").dropna()
        vmin, vmax = (float(vals.min()), float(vals.max())) if len(vals) else (0, 1)

        def _seq(v: float) -> str:
            if vmax <= vmin:
                return "#264653"
            t = max(0.0, min(1.0, math.log1p(v - vmin) / math.log1p(vmax - vmin)))
            return f"#{int(38+t*4):02x}{int(70+t*87):02x}{int(83+t*48):02x}"

        lk = {(r[row_label], r[col_label]): r for _, r in df.iterrows()}
        W = ML + len(cols) * (CW + GAP) + 20
        H = MT + len(rows) * (CH + GAP) + 40
        p: list[str] = []
        for ci, c in enumerate(cols):
            x = ML + ci * (CW + GAP) + CW // 2
            p.append(f'<text x="{x}" y="{MT-6}" text-anchor="end" font-size="9" '
                     f'transform="rotate(-45,{x},{MT-6})" fill="{_D["axis_color"]}">{_esc(str(c))}</text>')
        for ri, rl in enumerate(rows):
            y = MT + ri * (CH + GAP)
            p.append(f'<text x="{ML-4}" y="{y+CH//2+3}" text-anchor="end" font-size="9" '
                     f'fill="{_D["text_color"]}">{_esc(str(rl))}</text>')
            for ci, cl in enumerate(cols):
                x = ML + ci * (CW + GAP)
                rec = lk.get((rl, cl))
                if rec is None:
                    color = "#f0f0f0"
                elif grade_col and grade_col in df.columns:
                    color = grade_colors.get(str(rec[grade_col]).lower(), "#264653")
                else:
                    color = _seq(float(rec[value]) if pd.notna(rec[value]) else 0)
                p.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" fill="{color}" rx="1"/>')
        return _wrap(p, W, H, title)

    def to_html(self, **kw: Any) -> str:
        return _to_html(self.build(**kw), kw.get("title", ""))
