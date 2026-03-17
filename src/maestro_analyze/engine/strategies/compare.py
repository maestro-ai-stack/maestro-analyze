"""Compare 策略 — 按分组对比分析。"""
from __future__ import annotations

import pandas as pd

from maestro_analyze.engine.analyzer import Insight, AnalysisResult


class CompareStrategy:
    name = "compare"
    description = "按分组列对比指标"

    def analyze(self, *, df: pd.DataFrame, table_name: str = "data",
                group_col: str, metric_cols: list[str], **kw) -> AnalysisResult:
        insights: list[Insight] = []

        for metric in metric_cols:
            grouped = df.groupby(group_col)[metric].agg(["mean", "median", "std", "count"])
            best = grouped["mean"].idxmax()
            worst = grouped["mean"].idxmin()
            insights.append(Insight(
                category="comparison",
                title=f"{metric} 按 {group_col} 对比",
                detail=f"最高：{best}（均值 {grouped.loc[best, 'mean']:.2f}），"
                       f"最低：{worst}（均值 {grouped.loc[worst, 'mean']:.2f}）",
                data={"grouped": grouped.to_dict()},
            ))

        return AnalysisResult(
            table_name=table_name, row_count=len(df),
            col_count=len(df.columns), insights=insights,
        )


__all_strategies__ = [CompareStrategy]
