"""Trend 策略 — 时序趋势分析。"""
from __future__ import annotations

import pandas as pd

from maestro_analyze.engine.analyzer import Insight, AnalysisResult


class TrendStrategy:
    name = "trend"
    description = "时序趋势分析"

    def analyze(self, *, df: pd.DataFrame, table_name: str = "data",
                date_col: str, metric_col: str, freq: str = "ME", **kw) -> AnalysisResult:
        insights: list[Insight] = []
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        ts = df.set_index(date_col)[metric_col].resample(freq).mean()

        if len(ts) >= 2:
            change = (ts.iloc[-1] - ts.iloc[0]) / ts.iloc[0] * 100 if ts.iloc[0] != 0 else 0
            direction = "上升" if change > 0 else "下降"
            insights.append(Insight(
                category="trend",
                title=f"{metric_col} 整体{direction} {abs(change):.1f}%",
                detail=f"从 {ts.iloc[0]:.2f} 到 {ts.iloc[-1]:.2f}，{len(ts)} 个数据点",
                data={"series": {str(k): v for k, v in ts.to_dict().items()}},
            ))

        if len(ts) >= 3:
            recent = (ts.iloc[-1] - ts.iloc[-2]) / ts.iloc[-2] * 100 if ts.iloc[-2] != 0 else 0
            insights.append(Insight(
                category="trend",
                title=f"最近一期环比 {'+' if recent > 0 else ''}{recent:.1f}%",
                detail=f"{ts.index[-2].strftime('%Y-%m')} → {ts.index[-1].strftime('%Y-%m')}",
            ))

        return AnalysisResult(
            table_name=table_name, row_count=len(df),
            col_count=len(df.columns), insights=insights,
        )


__all_strategies__ = [TrendStrategy]
