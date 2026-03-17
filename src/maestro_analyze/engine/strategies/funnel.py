"""Funnel 策略 — 漏斗分析。"""
from __future__ import annotations

from maestro_analyze.engine.analyzer import Insight, AnalysisResult


class FunnelStrategy:
    name = "funnel"
    description = "漏斗转化分析"

    def analyze(self, *, steps: dict[str, int], **kw) -> AnalysisResult:
        insights: list[Insight] = []
        names = list(steps.keys())
        values = list(steps.values())

        for i in range(1, len(names)):
            rate = values[i] / values[i - 1] * 100 if values[i - 1] > 0 else 0
            drop = 100 - rate
            insights.append(Insight(
                category="funnel",
                title=f"{names[i - 1]} → {names[i]}：转化 {rate:.1f}%",
                detail=f"流失 {drop:.1f}%（{values[i - 1] - values[i]:,} 人）",
            ))

        if len(values) >= 2:
            total_rate = values[-1] / values[0] * 100 if values[0] > 0 else 0
            insights.append(Insight(
                category="funnel",
                title=f"端到端转化率 {total_rate:.1f}%",
                detail=f"{names[0]}({values[0]:,}) → {names[-1]}({values[-1]:,})",
            ))

        return AnalysisResult(
            table_name="funnel", row_count=sum(values),
            col_count=len(names), insights=insights,
        )


__all_strategies__ = [FunnelStrategy]
