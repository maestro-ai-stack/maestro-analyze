"""SVG helper functions shared by all SVG chart builders."""
from __future__ import annotations

from typing import Any

SVG_DEFAULTS: dict[str, Any] = {
    "font_family": "-apple-system, 'Helvetica Neue', sans-serif",
    "font_size": 11,
    "text_color": "#333",
    "axis_color": "#999",
    "bg_color": "#fff",
    "palette": [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
        "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
        "#6b9ac4", "#d4a373", "#c9ada7", "#a5a58d", "#6d6875",
    ],
}


def _esc(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _wrap(parts: list[str], W: int, H: int, title: str = "") -> str:
    """Wrap SVG elements in an <svg> tag with optional title."""
    if title:
        parts.insert(0, f'<text x="{W // 2}" y="18" text-anchor="middle" font-size="14" '
                        f'font-weight="bold" fill="{SVG_DEFAULTS["text_color"]}">{_esc(title)}</text>')
    body = "\n".join(parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'style="font-family:{SVG_DEFAULTS["font_family"]};background:{SVG_DEFAULTS["bg_color"]}">\n{body}\n</svg>')


def _to_html(svg: str, title: str = "") -> str:
    heading = f"<h3 style='margin:0 0 8px'>{_esc(title)}</h3>" if title else ""
    return f"<div style='font-family:{SVG_DEFAULTS['font_family']};padding:12px'>{heading}{svg}</div>"
