"""SDK 入口 — 供其他 Agent/skill 调用。"""
from __future__ import annotations

import pandas as pd

from maestro_analyze.core.store import Store
from maestro_analyze.engine.analyzer import Analyzer, AnalysisResult


def analyze_file(path: str, table_name: str | None = None,
                 db: str = "workspace.duckdb") -> AnalysisResult:
    """导入文件并自动分析。一步到位。"""
    with Store(db) as store:
        name = store.import_file(path, table_name)
        analyzer = Analyzer(store)
        return analyzer.profile(name)


def analyze_dataframe(df: pd.DataFrame, table_name: str = "data",
                      db: str = "workspace.duckdb") -> AnalysisResult:
    """分析 DataFrame。"""
    with Store(db) as store:
        store.import_dataframe(df, table_name)
        analyzer = Analyzer(store)
        return analyzer.profile(table_name)


def query(sql: str, db: str = "workspace.duckdb") -> pd.DataFrame:
    """执行 SQL 查询。"""
    with Store(db) as store:
        return store.query(sql)
