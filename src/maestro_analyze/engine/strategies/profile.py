"""Profile 策略 — 数据画像：描述统计 + 自动洞察。"""
from __future__ import annotations

import pandas as pd

from maestro_analyze.engine.analyzer import Insight, AnalysisResult


class ProfileStrategy:
    name = "profile"
    description = "数据画像：描述统计 + 自动洞察"

    def analyze(self, *, df: pd.DataFrame, table_name: str = "data", **kw) -> AnalysisResult:
        insights: list[Insight] = []
        n_rows, n_cols = df.shape

        insights.append(Insight(
            category="summary",
            title=f"数据集包含 {n_rows:,} 行 × {n_cols} 列",
            detail=f"列：{', '.join(df.columns[:20])}{'...' if n_cols > 20 else ''}",
        ))

        # 缺失值检测
        missing = df.isnull().sum()
        missing_cols = missing[missing > 0]
        if len(missing_cols) > 0:
            worst = missing_cols.idxmax()
            pct = missing_cols[worst] / n_rows * 100
            insights.append(Insight(
                category="anomaly",
                title=f"{len(missing_cols)} 列有缺失值",
                detail=f"最严重：{worst}（{pct:.1f}% 缺失）",
                data={"missing": missing_cols.to_dict()},
            ))

        # 数值列统计
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            stats = df[numeric_cols].describe()
            lines = []
            for col in stats.columns[:5]:
                mean = stats.loc["mean", col]
                std = stats.loc["std", col]
                lines.append(f"{col}: 均值={mean:.2f}, 标准差={std:.2f}")
            insights.append(Insight(
                category="summary",
                title=f"{len(numeric_cols)} 个数值列",
                detail="; ".join(lines),
                data={"stats": stats.to_dict()},
            ))

            # 异常值检测（IQR）
            for col in numeric_cols[:10]:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                outliers = int(((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum())
                if outliers > 0:
                    insights.append(Insight(
                        category="anomaly",
                        title=f"{col} 有 {outliers} 个异常值",
                        detail=f"IQR 方法，占比 {outliers / n_rows * 100:.1f}%",
                    ))

        # 分类列统计
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cat_cols[:5]:
            n_unique = df[col].nunique()
            top = df[col].value_counts().head(3)
            insights.append(Insight(
                category="summary",
                title=f"{col}：{n_unique} 个唯一值",
                detail=f"Top 3：{', '.join(f'{k}({v})' for k, v in top.items())}",
            ))

        # 相关性
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            strong = []
            cols = corr.columns
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    r = corr.iloc[i, j]
                    if abs(r) >= 0.7:
                        strong.append((cols[i], cols[j], round(r, 3)))
            if strong:
                strong.sort(key=lambda x: abs(x[2]), reverse=True)
                insights.append(Insight(
                    category="summary",
                    title=f"发现 {len(strong)} 对强相关变量",
                    detail="; ".join(f"{a}↔{b} (r={r:.2f})" for a, b, r in strong[:5]),
                ))

        return AnalysisResult(
            table_name=table_name, row_count=n_rows, col_count=n_cols,
            insights=insights, summary_stats=df.describe(include="all") if n_rows > 0 else None,
        )


__all_strategies__ = [ProfileStrategy]
