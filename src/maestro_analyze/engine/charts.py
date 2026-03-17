"""图表引擎 — Registry 路由到具体 Builder。

用法:
    fig = make_chart(df, "bubble", x="x", y="y", size="size")
    html = to_fragment(fig)
    path = save_chart(fig, "my_chart", fmt="html", fragment=True)

扩展:
    将自定义 Builder 放到 ~/.maestro/analyst/plugins/charts/
    Builder 需有 name 属性 + build(**kwargs) -> go.Figure 方法
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from maestro_analyze.core.config import OUTPUTS_DIR, PLUGINS_DIR, ensure_dirs
from maestro_analyze.core.registry import Registry

# ---------------------------------------------------------------------------
# 全局 chart registry
# ---------------------------------------------------------------------------

chart_registry = Registry("charts")


def _register_builtins() -> None:
    from maestro_analyze.engine.chart_builders.basic import __all_charts__ as basic
    from maestro_analyze.engine.chart_builders.advanced import __all_charts__ as advanced
    from maestro_analyze.engine.chart_builders.statistical import __all_charts__ as stats
    for cls in basic + advanced + stats:
        chart_registry.register(cls)


_register_builtins()
chart_registry.load_plugins(PLUGINS_DIR / "charts")

# ---------------------------------------------------------------------------
# CHART_TYPES — 兼容旧接口
# ---------------------------------------------------------------------------

CHART_TYPES: dict[str, str] = {
    item["name"]: item["description"] for item in chart_registry.list()
}

# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def make_chart(df: pd.DataFrame, chart_type: str | None = None, **kwargs: Any) -> go.Figure:
    """统一图表创建接口。chart_type=None 时自动选型。"""
    if chart_type is None:
        return _auto_chart(df, **kwargs)
    builder_cls = chart_registry.get(chart_type)
    return builder_cls().build(df=df, **kwargs)


def to_fragment(fig: go.Figure) -> str:
    """返回图表的 <div> HTML 片段（不含 plotly.js）。"""
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={"displayModeBar": False},
    )


def save_chart(fig: go.Figure, name: str, fmt: str = "html",
               fragment: bool = False) -> Path:
    """保存图表到文件。fragment=True 输出 <div> 片段。"""
    ensure_dirs()
    path = OUTPUTS_DIR / f"{name}.{fmt}"
    if fmt == "html":
        if fragment:
            path.write_text(to_fragment(fig))
        else:
            fig.write_html(str(path))
    elif fmt in ("png", "svg"):
        fig.write_image(str(path), format=fmt)
    return path


# ---------------------------------------------------------------------------
# 自动选型
# ---------------------------------------------------------------------------


def _auto_chart(df: pd.DataFrame, x: str | None = None,
                y: str | None = None, **kwargs: Any) -> go.Figure:
    if x is None and y is None:
        return _auto_detect(df, **kwargs)
    if x and y:
        x_dtype = df[x].dtype
        y_dtype = df[y].dtype
        if x_dtype == "object" and pd.api.types.is_numeric_dtype(y_dtype):
            return make_chart(df, "bar", x=x, y=y, **kwargs)
        if pd.api.types.is_datetime64_any_dtype(df[x]):
            return make_chart(df, "line", x=x, y=y, **kwargs)
        if pd.api.types.is_numeric_dtype(x_dtype) and pd.api.types.is_numeric_dtype(y_dtype):
            return make_chart(df, "scatter", x=x, y=y, **kwargs)
    return make_chart(df, "bar", x=x, y=y, **kwargs)


def _auto_detect(df: pd.DataFrame, **kwargs: Any) -> go.Figure:
    numeric = df.select_dtypes(include="number").columns.tolist()
    cat = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include=["datetime64"]).columns.tolist()

    if date and numeric:
        return make_chart(df, "line", x=date[0], y=numeric[0], **kwargs)
    if cat and numeric:
        return make_chart(df, "bar", x=cat[0], y=numeric[0], **kwargs)
    if len(numeric) >= 2:
        return make_chart(df, "scatter", x=numeric[0], y=numeric[1], **kwargs)
    if numeric:
        return make_chart(df, "histogram", x=numeric[0], **kwargs)
    return make_chart(df, "table", **kwargs)


# ---------------------------------------------------------------------------
# 兼容旧函数签名
# ---------------------------------------------------------------------------

def auto_chart(df, x=None, y=None, title=""):
    return make_chart(df, x=x, y=y, title=title)


def distribution_chart(series, title=""):
    df = series.to_frame()
    return make_chart(df, "distribution", x=series.name, title=title)


def correlation_heatmap(df, title="相关性矩阵"):
    return make_chart(df, "heatmap", title=title)


def trend_chart(series, title=""):
    import plotly.express as px
    return px.line(x=series.index, y=series.values, title=title or f"{series.name} 趋势")


def funnel_chart(steps, title="漏斗分析"):
    df = pd.DataFrame({"step": list(steps.keys()), "count": list(steps.values())})
    return make_chart(df, "funnel", names="step", values="count", title=title)
