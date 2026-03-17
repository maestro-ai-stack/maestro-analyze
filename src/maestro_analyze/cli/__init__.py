"""CLI — manalyze 命令。

用法：
  manalyze import <file>              # 导入数据文件
  manalyze tables                     # 列出所有表
  manalyze profile <table>            # 数据画像
  manalyze query "SELECT ..."         # SQL 查询
  manalyze chart <table> [--x col] [--y col]  # 生成图表
  manalyze compare <table> --group col --metrics col1,col2
  manalyze trend <table> --date col --metric col
  manalyze export <table> [--format csv|parquet|json]
"""
from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.table import Table

from maestro_analyze.core.store import Store
from maestro_analyze.engine.analyzer import Analyzer

app = typer.Typer(
    name="maestro-analyst",
    help="Analyze everything, for agents.",
    add_completion=False,
)

console = Console()

# ---------------------------------------------------------------------------
# 默认子命令注入（和 mfetch 同样逻辑）
# ---------------------------------------------------------------------------

_SUBCOMMANDS = {"import", "tables", "profile", "query", "chart", "compare",
                "trend", "funnel", "export", "drop", "--help", "-h"}


# ---------------------------------------------------------------------------
# 命令
# ---------------------------------------------------------------------------

@app.command(name="import")
def import_file(
    path: str = typer.Argument(..., help="文件路径（CSV/Excel/JSON/Parquet）"),
    table: str = typer.Option(None, "--table", "-t", help="自定义表名"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """导入数据文件到本地数据库。"""
    with Store(db) as store:
        name = store.import_file(path, table)
        info = store.tables()
        for t in info:
            if t["name"] == name:
                console.print(f"[green]✓[/green] 导入成功: {name} ({t['rows']:,} 行, {len(t['columns'])} 列)")
                return
        console.print(f"[green]✓[/green] 导入成功: {name}")


@app.command()
def tables(
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """列出所有表。"""
    with Store(db) as store:
        all_tables = store.tables()
        if not all_tables:
            console.print("[dim]没有数据表。用 manalyze import <file> 导入。[/dim]")
            return
        tbl = Table(title="数据表")
        tbl.add_column("表名", style="cyan")
        tbl.add_column("行数", justify="right")
        tbl.add_column("列数", justify="right")
        tbl.add_column("列", style="dim")
        for t in all_tables:
            cols = ", ".join(c["name"] for c in t["columns"][:6])
            if len(t["columns"]) > 6:
                cols += f" (+{len(t['columns'])-6})"
            tbl.add_row(t["name"], f"{t['rows']:,}", str(len(t["columns"])), cols)
        console.print(tbl)


@app.command()
def profile(
    table: str = typer.Argument(..., help="表名"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """数据画像：自动洞察 + 描述统计。"""
    with Store(db) as store:
        analyzer = Analyzer(store)
        result = analyzer.profile(table)

        console.print(f"\n[bold]📊 {table}[/bold] — {result.row_count:,} 行 × {result.col_count} 列\n")

        for insight in result.insights:
            icon = {"summary": "📋", "trend": "📈", "anomaly": "⚠️",
                    "comparison": "⚖️", "funnel": "🔽"}.get(insight.category, "💡")
            console.print(f"  {icon} [bold]{insight.title}[/bold]")
            console.print(f"     {insight.detail}\n")


@app.command()
def query(
    sql: str = typer.Argument(..., help="SQL 查询语句"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
    limit: int = typer.Option(50, "--limit", "-l", help="最大行数"),
) -> None:
    """执行 SQL 查询。"""
    with Store(db) as store:
        df = store.query(sql)
        if len(df) > limit:
            console.print(f"[dim]显示前 {limit} 行（共 {len(df)} 行）[/dim]")
            df = df.head(limit)
        console.print(df.to_string())


@app.command()
def chart(
    table: str = typer.Argument(..., help="表名"),
    x: str = typer.Option(None, "--x", help="X 轴列"),
    y: str = typer.Option(None, "--y", help="Y 轴列"),
    chart_type: str = typer.Option(None, "--type", "-t", help="图表类型: bar|line|scatter|bubble|sankey|treemap|wordcloud|radar|pie|box|funnel|heatmap|table"),
    size: str = typer.Option(None, "--size", help="气泡大小列 (bubble)"),
    color: str = typer.Option(None, "--color", help="颜色列"),
    text: str = typer.Option(None, "--text", help="文本标签列"),
    names: str = typer.Option(None, "--names", help="名称列 (treemap/pie/funnel)"),
    parents: str = typer.Option(None, "--parents", help="父级列 (treemap)"),
    values: str = typer.Option(None, "--values", help="数值列 (treemap/sankey)"),
    source_col: str = typer.Option(None, "--source", help="源列 (sankey)"),
    target: str = typer.Option(None, "--target", help="目标列 (sankey)"),
    title: str = typer.Option("", "--title", help="图表标题"),
    sql: str = typer.Option(None, "--sql", help="用 SQL 查询替代表名"),
    fmt: str = typer.Option("html", "--format", "-f", help="输出格式: html|png|svg"),
    fragment: bool = typer.Option(False, "--fragment", help="输出 <div> 片段（供嵌入）"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """生成图表。--type 手动指定类型，省略则自动选型。"""
    from maestro_analyze.engine.charts import make_chart, save_chart, CHART_TYPES

    with Store(db) as store:
        if sql:
            df = store.query(sql)
            name = "query_result"
        else:
            df = store.query(f"SELECT * FROM {table}")
            name = table

        fig = make_chart(
            df, chart_type,
            x=x, y=y, size=size, color=color, text=text,
            names=names, parents=parents, values=values,
            source=source_col, target=target,
            title=title or name,
        )
        path = save_chart(fig, name, fmt, fragment=fragment)
        console.print(f"[green]✓[/green] 图表已保存: {path}")
        if fragment:
            console.print(f"[dim]Fragment 模式：输出 <div> 片段，嵌入时需引入 plotly.js[/dim]")


@app.command()
def compare(
    table: str = typer.Argument(..., help="表名"),
    group: str = typer.Option(..., "--group", "-g", help="分组列"),
    metrics: str = typer.Option(..., "--metrics", "-m", help="指标列（逗号分隔）"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """对比分析。"""
    with Store(db) as store:
        analyzer = Analyzer(store)
        result = analyzer.compare(table, group, metrics.split(","))
        for insight in result.insights:
            console.print(f"  ⚖️ [bold]{insight.title}[/bold]")
            console.print(f"     {insight.detail}\n")


@app.command()
def trend(
    table: str = typer.Argument(..., help="表名"),
    date: str = typer.Option(..., "--date", "-d", help="日期列"),
    metric: str = typer.Option(..., "--metric", "-m", help="指标列"),
    freq: str = typer.Option("ME", "--freq", help="聚合频率: D|W|ME|QE|YE"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """趋势分析。"""
    with Store(db) as store:
        analyzer = Analyzer(store)
        result = analyzer.trend(table, date, metric, freq)
        for insight in result.insights:
            console.print(f"  📈 [bold]{insight.title}[/bold]")
            console.print(f"     {insight.detail}\n")


@app.command(name="export")
def export_table(
    table: str = typer.Argument(..., help="表名"),
    output: str = typer.Option(None, "--output", "-o", help="输出路径"),
    fmt: str = typer.Option("csv", "--format", "-f", help="格式: csv|parquet|json"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """导出表到文件。"""
    from maestro_analyze.core.config import OUTPUTS_DIR, ensure_dirs
    ensure_dirs()
    if output is None:
        output = str(OUTPUTS_DIR / f"{table}.{fmt}")
    with Store(db) as store:
        path = store.export(table, output, fmt)
        console.print(f"[green]✓[/green] 导出成功: {path}")


@app.command()
def drop(
    table: str = typer.Argument(..., help="表名"),
    db: str = typer.Option("workspace.duckdb", "--db", help="数据库名"),
) -> None:
    """删除表。"""
    with Store(db) as store:
        store.drop(table)
        console.print(f"[green]✓[/green] 已删除: {table}")
