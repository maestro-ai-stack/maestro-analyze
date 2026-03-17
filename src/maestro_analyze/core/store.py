"""DuckDB 数据存储层。

每个分析任务的数据存在 DuckDB 里，支持：
- 导入 CSV/Excel/JSON/Parquet
- SQL 查询
- 表管理（列出、删除、导出）
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from maestro_analyze.core.config import DATA_DIR, ensure_dirs
from maestro_analyze.core.errors import DataLoadError


class Store:
    """DuckDB 数据存储。"""

    def __init__(self, db_name: str = "workspace.duckdb") -> None:
        ensure_dirs()
        self._db_path = DATA_DIR / db_name
        self._conn = duckdb.connect(str(self._db_path))

    @property
    def db_path(self) -> Path:
        return self._db_path

    # -- 导入 ---------------------------------------------------------------

    def import_file(self, path: str | Path, table_name: str | None = None) -> str:
        """导入文件到 DuckDB 表，返回表名。

        自动检测格式：CSV, Excel, JSON, Parquet
        """
        p = Path(path)
        if not p.exists():
            raise DataLoadError(f"文件不存在: {p}")

        if table_name is None:
            # 从文件名生成表名（去掉特殊字符）
            table_name = p.stem.replace("-", "_").replace(" ", "_").replace(".", "_")
            # 确保不是纯数字开头
            if table_name[0].isdigit():
                table_name = f"t_{table_name}"

        suffix = p.suffix.lower()
        try:
            if suffix == ".csv":
                self._conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{p}')"
                )
            elif suffix in (".xlsx", ".xls"):
                # DuckDB 原生支持 Excel（需要 spatial 扩展或 pandas fallback）
                df = pd.read_excel(p)
                self._conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
            elif suffix == ".json":
                self._conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json_auto('{p}')"
                )
            elif suffix == ".parquet":
                self._conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{p}')"
                )
            else:
                # 尝试当 CSV 处理
                self._conn.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{p}')"
                )
        except Exception as exc:
            raise DataLoadError(f"导入失败 {p}: {exc}") from exc

        return table_name

    def import_dataframe(self, df: pd.DataFrame, table_name: str) -> str:
        """导入 pandas DataFrame。"""
        self._conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        return table_name

    # -- 查询 ---------------------------------------------------------------

    def query(self, sql: str) -> pd.DataFrame:
        """执行 SQL，返回 DataFrame。"""
        return self._conn.execute(sql).fetchdf()

    def query_raw(self, sql: str) -> list[tuple]:
        """执行 SQL，返回原始 tuple 列表。"""
        return self._conn.execute(sql).fetchall()

    # -- 表管理 -------------------------------------------------------------

    def tables(self) -> list[dict[str, Any]]:
        """列出所有表及其行数/列数。"""
        result = self._conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        tables = []
        for (name,) in result:
            info = self._conn.execute(
                f"SELECT COUNT(*) as rows FROM {name}"
            ).fetchone()
            cols = self._conn.execute(
                f"SELECT column_name, data_type FROM information_schema.columns "
                f"WHERE table_name = '{name}' AND table_schema = 'main'"
            ).fetchall()
            tables.append({
                "name": name,
                "rows": info[0] if info else 0,
                "columns": [{"name": c[0], "type": c[1]} for c in cols],
            })
        return tables

    def describe(self, table_name: str) -> pd.DataFrame:
        """描述统计。"""
        return self._conn.execute(f"SUMMARIZE {table_name}").fetchdf()

    def preview(self, table_name: str, limit: int = 20) -> pd.DataFrame:
        """预览表数据。"""
        return self._conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchdf()

    def drop(self, table_name: str) -> None:
        """删除表。"""
        self._conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    def export(self, table_name: str, path: str | Path, fmt: str = "csv") -> Path:
        """导出表到文件。"""
        p = Path(path)
        if fmt == "csv":
            self._conn.execute(f"COPY {table_name} TO '{p}' (FORMAT CSV, HEADER)")
        elif fmt == "parquet":
            self._conn.execute(f"COPY {table_name} TO '{p}' (FORMAT PARQUET)")
        elif fmt == "json":
            self._conn.execute(f"COPY {table_name} TO '{p}' (FORMAT JSON)")
        return p

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
