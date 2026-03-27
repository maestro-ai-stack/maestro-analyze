<p align="center"><img src=".github/maestro-logo.png" alt="Maestro" width="120" /></p>
<h1 align="center">maestro-analyze</h1>
<p align="center"><strong>Analyze everything, for agents.</strong></p>
<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python 3.11+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT" /></a>
  <a href="https://github.com/maestro-ai-stack/maestro-analyze"><img src="https://img.shields.io/github/stars/maestro-ai-stack/maestro-analyze" alt="GitHub stars" /></a>
</p>

Import any dataset, profile it, query it with SQL, and generate 25+ chart types -- all from the command line. DuckDB backend. Zero config. Built for AI agents and humans who prefer terminals over dashboards.

---

## Quickstart

```bash
pip install maestro-analyze
```

```bash
$ manalyze import sales.csv
  Imported: sales (12,847 rows, 9 columns)

$ manalyze profile sales
  sales -- 12,847 rows x 9 columns
  Revenue is right-skewed (median $420, mean $1,230)
  3 outliers detected in profit_margin (> 3 sigma)
  Missing: 2.1% in region column

$ manalyze chart sales --type bar --x region --y revenue
  Chart saved: charts/sales.html

$ manalyze query "SELECT region, SUM(revenue) FROM sales GROUP BY region ORDER BY 2 DESC"
```

---

## Features

- **DuckDB backend** -- import CSV, Excel, JSON, Parquet into a local analytical database. SQL everything.
- **Auto-profiling** -- descriptive stats, distribution analysis, anomaly detection, missing data audit.
- **25 chart types** -- interactive Plotly charts and pure SVG charts. Auto-selects type when you omit `--type`.
- **Trend analysis** -- time series aggregation with configurable frequency (daily, weekly, monthly, quarterly, yearly).
- **Comparison analysis** -- group-by metrics with statistical insights.
- **Plugin architecture** -- drop a `.py` file in `~/.maestro/analyst/plugins/charts/` and it auto-registers.
- **Agent-native** -- every command returns structured output. Designed as a tool for AI coding agents.

---

## Chart Types

### Plotly (interactive HTML/PNG/SVG)

| Type | Description |
|------|-------------|
| `bar` | Bar chart |
| `line` | Line chart |
| `scatter` | Scatter plot |
| `histogram` | Histogram |
| `pie` | Pie chart |
| `box` | Box plot |
| `bubble` | Bubble chart (size + color dimensions) |
| `sankey` | Sankey flow diagram |
| `treemap` | Hierarchical treemap |
| `wordcloud` | Word cloud |
| `radar` | Radar / spider chart |
| `heatmap` | Correlation heatmap |
| `distribution` | Distribution histogram with KDE |
| `funnel` | Funnel chart |
| `table` | Formatted data table |
| `event_band` | Line chart with event period bands |
| `stacked_area` | Stacked area composition |
| `bland_altman` | Agreement / validation plot |
| `coverage_matrix` | Data completeness heatmap |
| `trust_radar` | Multi-axis scoring radar |

### SVG (pure, no JavaScript dependency)

| Type | Description |
|------|-------------|
| `bump` | Ranking trajectories over time |
| `heatmap_grid` | 2D categorical grid heatmap |
| `lollipop` | Horizontal lollipop chart |
| `event_timeline` | Vertical event timeline |
| `slope` | Period comparison slope chart |
| `sparkline` | Tiny inline chart |

---

## CLI Reference

### Import data

```bash
manalyze import data.csv                          # auto-detect table name from filename
manalyze import data.xlsx --table quarterly        # custom table name
manalyze import data.parquet --db project.duckdb   # custom database file
```

### List tables

```bash
manalyze tables
```

### Profile a table

```bash
manalyze profile sales                            # auto-insights + descriptive stats
```

### SQL queries

```bash
manalyze query "SELECT * FROM sales WHERE revenue > 1000" --limit 100
```

### Generate charts

```bash
manalyze chart sales --type bar --x region --y revenue
manalyze chart sales --type scatter --x cost --y revenue --color region
manalyze chart sales --type bubble --x cost --y revenue --size volume --color region
manalyze chart sales --type sankey --source origin --target destination --values volume
manalyze chart sales --type treemap --names category --parents parent --values revenue
manalyze chart sales --type bump --x year --y rank --color entity
manalyze chart sales --sql "SELECT region, SUM(revenue) r FROM sales GROUP BY 1" --type bar --x region --y r
manalyze chart sales --type line --format png      # export as PNG instead of HTML
manalyze chart sales --type bar --fragment          # output <div> fragment for embedding
```

### Trend analysis

```bash
manalyze trend sales --date order_date --metric revenue              # monthly by default
manalyze trend sales --date order_date --metric revenue --freq W     # weekly
```

### Comparison analysis

```bash
manalyze compare sales --group region --metrics "revenue,profit,volume"
```

### Export

```bash
manalyze export sales                              # CSV by default
manalyze export sales --format parquet             # Parquet
manalyze export sales --format json -o out.json    # JSON to specific path
```

### Drop a table

```bash
manalyze drop old_data
```

---

## Python SDK

```python
from maestro_analyze.core.store import Store
from maestro_analyze.engine.analyzer import Analyzer
from maestro_analyze.engine.charts import make_chart, save_chart

# Import and query
with Store("workspace.duckdb") as store:
    store.import_file("sales.csv")
    df = store.query("SELECT region, SUM(revenue) as rev FROM sales GROUP BY 1")

# Auto-profile
with Store("workspace.duckdb") as store:
    analyzer = Analyzer(store)
    result = analyzer.profile("sales")
    for insight in result.insights:
        print(f"{insight.title}: {insight.detail}")

# Generate charts programmatically
fig = make_chart(df, "bar", x="region", y="rev", title="Revenue by Region")
path = save_chart(fig, "revenue_by_region", "html")
```

---

## Architecture

```
CLI (typer)  -->  Store (DuckDB)  -->  Analyzer (profiling, trend, compare)
                                  -->  Chart Engine (auto-select or manual)
                                         |
                                  chart_builders/
                                    __init__.py        # auto-discovers via pkgutil
                                    _base.py           # BaseChartBuilder ABC
                                    _svg_base.py       # SVG helpers
                                    bar.py             # one file per chart type
                                    ...                # 25 built-in types
                                  ~/.maestro/analyst/plugins/charts/
                                    my_chart.py        # user plugins (auto-registered)
```

### Adding a custom chart

Drop a `.py` file in `~/.maestro/analyst/plugins/charts/`:

```python
from maestro_analyze.engine.chart_builders._base import BaseChartBuilder

class WaterfallBuilder(BaseChartBuilder):
    name = "waterfall"
    description = "Waterfall chart for incremental changes"

    def build(self, *, df, **kw):
        import plotly.graph_objects as go
        fig = go.Figure(go.Waterfall(x=df[kw["x"]], y=df[kw["y"]]))
        return fig
```

Available on next run -- no registration code needed.

---

## How it compares

| | maestro-analyze | Metabase | Jupyter | Apache Superset |
|---|---|---|---|---|
| Setup | `pip install` | Docker + database | `pip install` + kernel | Docker + database + Redis |
| Interface | CLI + Python SDK | Web UI | Notebook | Web UI |
| Agent-friendly | Yes (structured CLI output) | No (browser-only) | Partial (kernel protocol) | No (browser-only) |
| Chart types | 25 built-in + plugins | ~15 | Unlimited (matplotlib) | ~30 |
| Data backend | DuckDB (embedded) | PostgreSQL / MySQL | pandas (in-memory) | SQLAlchemy |
| Auto-profiling | Built-in | No | Manual | No |
| Config required | None | Database, SMTP, secrets | None | Database, cache, auth |
| Target user | Agents + CLI developers | Business analysts | Data scientists | BI teams |

maestro-analyze is not a replacement for full BI platforms. It is a zero-config analysis tool designed to be called by AI agents or used directly from the terminal.

---

## Optional extras

```bash
pip install maestro-analyze[ml]       # scikit-learn, scipy (clustering, statistical tests)
pip install maestro-analyze[polars]   # Polars DataFrame support
pip install maestro-analyze[all]      # everything
```

### Development setup

```bash
git clone https://github.com/maestro-ai-stack/maestro-analyze.git
cd maestro-analyze
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Contributing

**Core improvements** -- open issues and PRs on [maestro-ai-stack/maestro-analyze](https://github.com/maestro-ai-stack/maestro-analyze).

**Custom chart types** -- contribute built-in builders via PR, or distribute your own as plugin files that users drop into `~/.maestro/analyst/plugins/charts/`.

---

## License

MIT

---

<p align="center">Built by <a href="https://maestro.onl">Maestro</a> — Singapore AI product studio.</p>
