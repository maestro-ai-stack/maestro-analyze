"""分析引擎 — Registry 路由到具体 Strategy。

数据结构定义 + Analyzer 路由壳。
策略实现在 strategies/ 子包中。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from maestro_analyze.core.config import PLUGINS_DIR
from maestro_analyze.core.registry import Registry
from maestro_analyze.core.store import Store


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class Insight:
    """单条洞察。"""
    category: str          # summary | trend | anomaly | comparison | funnel
    title: str
    detail: str
    data: dict[str, Any] = field(default_factory=dict)
    chart_spec: dict | None = None


@dataclass
class AnalysisResult:
    """分析结果。"""
    table_name: str
    row_count: int
    col_count: int
    insights: list[Insight]
    summary_stats: pd.DataFrame | None = None
    charts: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 全局 analysis registry
# ---------------------------------------------------------------------------

analysis_registry = Registry("strategies")


def _register_builtins() -> None:
    from maestro_analyze.engine.strategies.profile import __all_strategies__ as profile
    from maestro_analyze.engine.strategies.compare import __all_strategies__ as compare
    from maestro_analyze.engine.strategies.trend import __all_strategies__ as trend
    from maestro_analyze.engine.strategies.funnel import __all_strategies__ as funnel

    for cls_list in (profile, compare, trend, funnel):
        for cls in cls_list:
            analysis_registry.register(cls)


_register_builtins()
analysis_registry.load_plugins(PLUGINS_DIR / "strategies")


# ---------------------------------------------------------------------------
# Analyzer — 路由壳
# ---------------------------------------------------------------------------


class Analyzer:
    """数据分析器。路由到注册的 Strategy。"""

    def __init__(self, store: Store) -> None:
        self._store = store

    def run(self, strategy_name: str, table_name: str, **kwargs: Any) -> AnalysisResult:
        """通用路由：获取数据 + 调用策略。"""
        strategy_cls = analysis_registry.get(strategy_name)
        df = self._store.query(f"SELECT * FROM {table_name}")
        return strategy_cls().analyze(df=df, table_name=table_name, **kwargs)

    # -- 兼容方法 (保持 CLI 不变) --

    def profile(self, table_name: str) -> AnalysisResult:
        return self.run("profile", table_name)

    def compare(self, table_name: str, group_col: str, metric_cols: list[str]) -> AnalysisResult:
        return self.run("compare", table_name, group_col=group_col, metric_cols=metric_cols)

    def trend(self, table_name: str, date_col: str, metric_col: str,
              freq: str = "ME") -> AnalysisResult:
        return self.run("trend", table_name, date_col=date_col, metric_col=metric_col, freq=freq)

    def funnel(self, steps: dict[str, int]) -> AnalysisResult:
        from maestro_analyze.engine.strategies.funnel import FunnelStrategy
        return FunnelStrategy().analyze(steps=steps)

    def sql(self, query: str) -> pd.DataFrame:
        return self._store.query(query)
