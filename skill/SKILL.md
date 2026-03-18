---
name: maestro-analyze
description: >
  General-purpose data analysis and visualization engine for agents.
  26 chart types (bar, line, scatter, histogram, pie, box, table, bubble,
  sankey, treemap, wordcloud, radar, heatmap, distribution, funnel,
  bump, heatmap_grid, lollipop, event_timeline, slope, sparkline,
  event_band, stacked_area, bland_altman, coverage_matrix, trust_radar).
  Plugin architecture — add custom chart types via ~/.maestro/analyst/plugins/charts/.
  DuckDB backend for data ingestion. 4 analysis strategies (profile, compare,
  trend, funnel). CLI: manalyze.
  Triggers on: chart, visualization, plot, graph, dashboard, heatmap, scatter,
  bar chart, line chart, treemap, bump chart, sparkline, bland-altman,
  coverage matrix, stacked area, event timeline, lollipop, slope chart,
  data visualization, dataviz, analyze data, data profile, data trend.
---

# Maestro Analyze

General-purpose data analysis and visualization engine.

## Quick Reference

```bash
manalyze chart data.csv --type bar --x category --y value
manalyze chart data.csv --type bump --entity county --time_col year --value_col yield
manalyze chart data.csv --type coverage_matrix --entity county --time_col year
manalyze profile data.csv
manalyze trend data.csv --date-col date --metric-col revenue
manalyze compare data.csv --group-col region --metric-cols "revenue,cost"
```

## Architecture

```
chart_builders/
  __init__.py          # auto-discovers via pkgutil
  _base.py             # BaseChartBuilder ABC
  _svg_base.py         # SVG helpers (shared by SVG chart types)
  bar.py               # one file per chart type
  bump_chart.py
  ...26 total
```

### Adding a Custom Chart

Drop a `.py` file in `~/.maestro/analyst/plugins/charts/`:

```python
# ~/.maestro/analyst/plugins/charts/my_chart.py
from maestro_analyze.engine.chart_builders._base import BaseChartBuilder

class MyChartBuilder(BaseChartBuilder):
    name = "my_chart"
    description = "My custom chart"

    def build(self, *, df, **kw):
        import plotly.express as px
        return px.bar(df, x=kw.get("x"), y=kw.get("y"))
```

Auto-registered on next import.

## Chart Types

### Plotly (interactive)
| Name | Description |
|------|-------------|
| bar | Bar chart |
| line | Line chart |
| scatter | Scatter plot |
| histogram | Histogram |
| pie | Pie chart |
| box | Box plot |
| table | Data table |
| bubble | Bubble chart (4D) |
| sankey | Sankey flow diagram |
| treemap | Hierarchical treemap |
| wordcloud | Word cloud |
| radar | Radar/spider chart |
| heatmap | Correlation heatmap |
| distribution | Distribution histogram |
| funnel | Funnel chart |
| event_band | Line chart + event period bands |
| stacked_area | Stacked area composition |
| bland_altman | Agreement/validation plot |
| coverage_matrix | Data completeness heatmap |
| trust_radar | Multi-axis scoring radar |

### SVG (pure, no JS)
| Name | Description |
|------|-------------|
| bump | Ranking trajectories over time |
| heatmap_grid | 2D categorical grid heatmap |
| lollipop | Horizontal lollipop chart |
| event_timeline | Vertical event timeline |
| slope | Period comparison slope chart |
| sparkline | Tiny inline chart |

## Design Tokens

Chart builders consume design tokens from `maestro-creative/reference/dataviz-patterns.md`.
SVG charts use `SVG_DEFAULTS` dict; Plotly charts use `plotly_white` template.

## Cross-References

- Design rules: `maestro-creative` (palettes, typography, layout)
- Econometric charts: `maestro-economics` (coefficient plots, event study plots)
- Data quality: `maestro-data-qa` (diagnostic dashboards)
