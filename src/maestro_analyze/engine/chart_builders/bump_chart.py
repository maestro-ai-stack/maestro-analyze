"""Bump chart -- ranking trajectories over time."""
from __future__ import annotations

from typing import Any

import pandas as pd

from ._base import BaseChartBuilder
from ._svg_base import SVG_DEFAULTS, _esc, _wrap, _to_html

_D = SVG_DEFAULTS


class BumpChartBuilder(BaseChartBuilder):
    """Ranking trajectories over time. Auto-ranks by value when rank_col absent."""

    name = "bump"
    description = "Bump chart -- ranking trajectories over time"

    def build(self, *, df: pd.DataFrame, entity: str = "entity", time_col: str = "year",
              rank_col: str | None = None, value_col: str | None = None,
              title: str = "", **kw: Any) -> str:
        W, H = kw.get("width", 920), kw.get("height", 440)
        ML, MR, MT, MB = 80, 160, 40, 50
        work = df.copy()
        if rank_col and rank_col in work.columns:
            work["_rank"] = work[rank_col]
        elif value_col and value_col in work.columns:
            work["_rank"] = work.groupby(time_col)[value_col].rank(ascending=False, method="min")
        else:
            raise ValueError("Provide rank_col or value_col")
        periods = sorted(work[time_col].unique())
        entities = sorted(work[entity].unique())
        max_rank = int(work["_rank"].max())
        pw, ph = W - ML - MR, H - MT - MB
        xf = lambda t: ML + (periods.index(t) / max(len(periods) - 1, 1)) * pw
        yf = lambda r: MT + ((r - 1) / max(max_rank - 1, 1)) * ph
        pal = _D["palette"]
        p: list[str] = []
        for t in periods:
            x = xf(t)
            p.append(f'<text x="{x}" y="{H-10}" text-anchor="middle" font-size="10" '
                     f'fill="{_D["axis_color"]}">{_esc(str(t))}</text>')
        for i, ent in enumerate(entities):
            col = pal[i % len(pal)]
            sub = work[work[entity] == ent].sort_values(time_col)
            pts = [(float(xf(r[time_col])), float(yf(r["_rank"]))) for _, r in sub.iterrows()]
            if not pts:
                continue
            d = " ".join(f"{'M' if j==0 else 'L'}{x:.1f},{y:.1f}" for j,(x,y) in enumerate(pts))
            p.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.5" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
            for px_, py_ in pts:
                p.append(f'<circle cx="{px_:.1f}" cy="{py_:.1f}" r="4" fill="{col}"/>')
            lx, ly = pts[-1]
            p.append(f'<text x="{lx+8}" y="{ly+4}" font-size="11" fill="{col}">{_esc(str(ent))}</text>')
        return _wrap(p, W, H, title)

    def to_html(self, **kw: Any) -> str:
        return _to_html(self.build(**kw), kw.get("title", ""))
