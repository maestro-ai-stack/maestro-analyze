"""Vertical event timeline with category coloring."""
from __future__ import annotations

from typing import Any

from ._base import BaseChartBuilder
from ._svg_base import SVG_DEFAULTS, _esc, _wrap, _to_html

_D = SVG_DEFAULTS


class EventTimelineBuilder(BaseChartBuilder):
    """Vertical timeline with events alternating left/right."""

    name = "event_timeline"
    description = "Vertical event timeline with category coloring"

    def build(self, *, events: list[dict[str, Any]], title: str = "", **kw: Any) -> str:
        W = kw.get("width", 700)
        CX, EV_H, MT, MB = W // 2, 60, 50, 30
        H = MT + len(events) * EV_H + MB
        cats = sorted({e.get("category", "") for e in events})
        pal = _D["palette"]
        cc = {c: pal[i % len(pal)] for i, c in enumerate(cats)}
        p: list[str] = [f'<line x1="{CX}" y1="{MT}" x2="{CX}" y2="{H-MB}" '
                        f'stroke="{_D["axis_color"]}" stroke-width="2"/>']
        for i, ev in enumerate(events):
            y = MT + i * EV_H + EV_H // 2
            col = cc.get(ev.get("category", ""), pal[0])
            left = i % 2 == 0
            arm = 60
            xs = CX - arm if left else CX + arm
            p.append(f'<line x1="{CX}" y1="{y}" x2="{xs}" y2="{y}" stroke="{col}" stroke-width="1.5"/>')
            p.append(f'<circle cx="{CX}" cy="{y}" r="5" fill="{col}"/>')
            bx = xs - 30 if left else xs + 2
            yr = _esc(str(ev.get("year", "")))
            p.append(f'<rect x="{bx}" y="{y-10}" width="28" height="18" rx="3" fill="{col}" opacity="0.15"/>')
            p.append(f'<text x="{bx+14}" y="{y+3}" text-anchor="middle" font-size="10" '
                     f'font-weight="bold" fill="{col}">{yr}</text>')
            lx = bx - 8 if left else bx + 36
            anc = "end" if left else "start"
            p.append(f'<text x="{lx}" y="{y+4}" text-anchor="{anc}" font-size="11" '
                     f'fill="{_D["text_color"]}">{_esc(str(ev.get("label", "")))}</text>')
        return _wrap(p, W, H, title)

    def to_html(self, **kw: Any) -> str:
        return _to_html(self.build(**kw), kw.get("title", ""))
