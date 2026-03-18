# maestro-analyst Plugin Architecture Refactor

**Goal:** 将 charts 和 analyzers 重构为插件注册表架构，支持用户自定义扩展。

**Architecture:** Chart 和 Analyzer 各有一个 Registry，内置类型通过 `register()` 注册，用户扩展放 `~/.maestro/analyst/plugins/` 自动发现加载。所有图表构建器实现 `ChartBuilder` 协议，所有分析策略实现 `AnalysisStrategy` 协议。CLI 不变，内部路由到 Registry。

**Tech Stack:** Python 3.11+, DuckDB, Plotly, Typer, pytest

**当前文件结构:**
```
src/maestro_analyst/
├── cli/__init__.py          # CLI 命令 (typer)
├── core/
│   ├── config.py            # 路径 + 配置
│   ├── errors.py            # 异常层级
│   └── store.py             # DuckDB 存储层
├── engine/
│   ├── analyzer.py          # Analyzer 类 (profile/compare/trend/funnel)
│   └── charts.py            # 所有图表 (make_chart + 14 种类型)
├── interfaces/sdk.py        # Python SDK
└── templates/__init__.py    # 空
```

**目标文件结构:**
```
src/maestro_analyst/
├── cli/__init__.py          # CLI (不变，路由到 registry)
├── core/
│   ├── config.py            # +PLUGINS_DIR 路径
│   ├── errors.py            # 不变
│   ├── registry.py          # NEW: 通用 Registry 类
│   └── store.py             # 不变
├── engine/
│   ├── analyzer.py          # 瘦身: 只保留 Analyzer 壳 + 策略路由
│   ├── charts.py            # 瘦身: 只保留 registry 初始化 + make_chart 路由
│   ├── chart_builders/      # NEW: 每种图表一个文件
│   │   ├── __init__.py
│   │   ├── basic.py         # bar/line/scatter/histogram/pie/box/table
│   │   ├── advanced.py      # bubble/sankey/treemap/wordcloud/radar
│   │   └── statistical.py   # heatmap/distribution/funnel
│   └── strategies/          # NEW: 每种分析策略一个文件
│       ├── __init__.py
│       ├── profile.py
│       ├── compare.py
│       ├── trend.py
│       └── funnel.py
├── interfaces/sdk.py        # 不变
└── templates/__init__.py
```

---

### Task 1: Registry 核心类

**Files:**
- Create: `src/maestro_analyst/core/registry.py`
- Create: `tests/unit/test_registry.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_registry.py
"""Registry 核心测试。"""
import pytest
from maestro_analyst.core.registry import Registry


class DummyBuilder:
    name = "dummy"
    description = "A dummy builder"

    def build(self, **kwargs):
        return {"built": True}


class AnotherBuilder:
    name = "another"
    description = "Another builder"

    def build(self, **kwargs):
        return {"built": True, "extra": kwargs}


def test_register_and_get():
    reg = Registry("test")
    reg.register(DummyBuilder)
    assert reg.get("dummy") is DummyBuilder


def test_get_unknown_raises():
    reg = Registry("test")
    with pytest.raises(KeyError, match="unknown"):
        reg.get("unknown")


def test_list_registered():
    reg = Registry("test")
    reg.register(DummyBuilder)
    reg.register(AnotherBuilder)
    items = reg.list()
    assert len(items) == 2
    names = [i["name"] for i in items]
    assert "dummy" in names
    assert "another" in names


def test_register_duplicate_warns(capsys):
    reg = Registry("test")
    reg.register(DummyBuilder)
    reg.register(DummyBuilder)  # 重复注册，覆盖 + warning
    assert reg.get("dummy") is DummyBuilder


def test_has():
    reg = Registry("test")
    reg.register(DummyBuilder)
    assert reg.has("dummy")
    assert not reg.has("nonexistent")
```

**Step 2: Run tests to verify they fail**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'maestro_analyst.core.registry'`

**Step 3: Write implementation**

```python
# src/maestro_analyst/core/registry.py
"""通用插件注册表。

Chart builders 和 Analysis strategies 共用此机制。
用法:
    registry = Registry("charts")
    registry.register(BarChartBuilder)       # 类注册
    builder_cls = registry.get("bar")        # 按 name 查找
    registry.list()                          # 列出所有已注册
    registry.load_plugins(Path("~/.maestro/analyst/plugins/charts/"))
"""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path
from typing import Any


class Registry:
    """通用注册表。被注册的类必须有 name: str 属性。"""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self._items: dict[str, type] = {}

    def register(self, cls: type) -> type:
        """注册一个类。类必须有 name 属性。可用作装饰器。"""
        name = getattr(cls, "name", None)
        if name is None:
            raise ValueError(f"注册到 {self.domain} 的类必须有 'name' 属性: {cls}")
        if name in self._items:
            warnings.warn(
                f"[{self.domain}] '{name}' 已存在，将被覆盖",
                stacklevel=2,
            )
        self._items[name] = cls
        return cls

    def get(self, name: str) -> type:
        """按名称获取已注册的类。"""
        if name not in self._items:
            available = ", ".join(sorted(self._items))
            raise KeyError(
                f"[{self.domain}] 未知类型 '{name}'。可用: {available}"
            )
        return self._items[name]

    def has(self, name: str) -> bool:
        return name in self._items

    def list(self) -> list[dict[str, str]]:
        """列出所有已注册项。"""
        return [
            {
                "name": getattr(cls, "name", ""),
                "description": getattr(cls, "description", ""),
            }
            for cls in self._items.values()
        ]

    def names(self) -> list[str]:
        return sorted(self._items.keys())

    def load_plugins(self, plugins_dir: Path) -> int:
        """从目录加载插件 .py 文件。

        每个 .py 文件可以定义一个或多个带 name 属性的类，
        并在模块级调用 register() 或通过 __all_builders__ / __all_strategies__ 导出。
        返回新加载的插件数量。
        """
        if not plugins_dir.is_dir():
            return 0

        loaded = 0
        for py_file in sorted(plugins_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            try:
                mod = self._import_file(py_file)
                # 查找模块中可注册的类
                export_attr = f"__all_{self.domain}__"
                exportables = getattr(mod, export_attr, None)
                if exportables:
                    for cls in exportables:
                        self.register(cls)
                        loaded += 1
                else:
                    # 自动发现: 查找所有有 name 属性的类
                    for attr_name in dir(mod):
                        obj = getattr(mod, attr_name)
                        if (isinstance(obj, type)
                                and hasattr(obj, "name")
                                and hasattr(obj, "build" if self.domain == "charts" else "analyze")
                                and obj.__module__ == mod.__name__):
                            self.register(obj)
                            loaded += 1
            except Exception as exc:
                warnings.warn(f"[{self.domain}] 加载插件 {py_file.name} 失败: {exc}")
        return loaded

    @staticmethod
    def _import_file(file_path: Path) -> Any:
        module_name = f"maestro_analyst_plugin_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {file_path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod
```

**Step 4: Run tests**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_registry.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add src/maestro_analyst/core/registry.py tests/unit/test_registry.py
git commit -m "feat(core): add generic plugin Registry class"
```

---

### Task 2: ChartBuilder 协议 + 基础图表拆分

**Files:**
- Create: `src/maestro_analyst/engine/chart_builders/__init__.py`
- Create: `src/maestro_analyst/engine/chart_builders/basic.py`
- Create: `tests/unit/test_chart_builders.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_chart_builders.py
"""图表构建器测试。"""
import pandas as pd
import plotly.graph_objects as go
import pytest

from maestro_analyst.engine.chart_builders.basic import (
    BarBuilder, LineBuilder, ScatterBuilder, HistogramBuilder,
    PieBuilder, BoxBuilder, TableBuilder,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "category": ["A", "B", "C", "D"],
        "value": [10, 20, 15, 25],
        "metric": [1.1, 2.2, 3.3, 4.4],
    })


class TestBarBuilder:
    def test_name(self):
        assert BarBuilder.name == "bar"

    def test_build_returns_figure(self, sample_df):
        builder = BarBuilder()
        fig = builder.build(df=sample_df, x="category", y="value")
        assert isinstance(fig, go.Figure)

    def test_build_with_title(self, sample_df):
        builder = BarBuilder()
        fig = builder.build(df=sample_df, x="category", y="value", title="Test")
        assert fig.layout.title.text == "Test"


class TestLineBuilder:
    def test_name(self):
        assert LineBuilder.name == "line"

    def test_build(self, sample_df):
        fig = LineBuilder().build(df=sample_df, x="category", y="value")
        assert isinstance(fig, go.Figure)


class TestScatterBuilder:
    def test_name(self):
        assert ScatterBuilder.name == "scatter"

    def test_build(self, sample_df):
        fig = ScatterBuilder().build(df=sample_df, x="value", y="metric")
        assert isinstance(fig, go.Figure)


class TestPieBuilder:
    def test_build(self, sample_df):
        fig = PieBuilder().build(df=sample_df, names="category", values="value")
        assert isinstance(fig, go.Figure)


class TestTableBuilder:
    def test_build(self, sample_df):
        fig = TableBuilder().build(df=sample_df)
        assert isinstance(fig, go.Figure)
```

**Step 2: Run to verify fail**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_chart_builders.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/maestro_analyst/engine/chart_builders/__init__.py
"""图表构建器包。每个 builder 实现 build(**kwargs) -> go.Figure。"""
```

```python
# src/maestro_analyst/engine/chart_builders/basic.py
"""基础图表构建器: bar, line, scatter, histogram, pie, box, table。"""
from __future__ import annotations
from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class BarBuilder:
    name = "bar"
    description = "柱状图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.bar(df, x=x, y=y, color=color, title=title)


class LineBuilder:
    name = "line"
    description = "折线图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.line(df, x=x, y=y, color=color, title=title)


class ScatterBuilder:
    name = "scatter"
    description = "散点图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, color: str | None = None,
              text: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.scatter(df, x=x, y=y, color=color, text=text, title=title)


class HistogramBuilder:
    name = "histogram"
    description = "直方图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        return px.histogram(df, x=x, title=title)


class PieBuilder:
    name = "pie"
    description = "饼图"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              values: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.pie(df, names=names, values=values, title=title or "Pie Chart")


class BoxBuilder:
    name = "box"
    description = "箱线图"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        return px.box(df, x=x, y=y, title=title)


class TableBuilder:
    name = "table"
    description = "数据表格"

    def build(self, *, df: pd.DataFrame, title: str = "", **kw: Any) -> go.Figure:
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df.columns)),
            cells=dict(values=[df[c].tolist() for c in df.columns]),
        )])
        fig.update_layout(title=title)
        return fig


__all_charts__ = [
    BarBuilder, LineBuilder, ScatterBuilder, HistogramBuilder,
    PieBuilder, BoxBuilder, TableBuilder,
]
```

**Step 4: Run tests**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_chart_builders.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add src/maestro_analyst/engine/chart_builders/ tests/unit/test_chart_builders.py
git commit -m "feat(charts): extract basic chart builders to plugin classes"
```

---

### Task 3: 高级图表构建器

**Files:**
- Create: `src/maestro_analyst/engine/chart_builders/advanced.py`
- Create: `src/maestro_analyst/engine/chart_builders/statistical.py`
- Create: `tests/unit/test_chart_advanced.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_chart_advanced.py
"""高级图表测试。"""
import pandas as pd
import plotly.graph_objects as go
import pytest

from maestro_analyst.engine.chart_builders.advanced import (
    BubbleBuilder, SankeyBuilder, TreemapBuilder, RadarBuilder,
)
from maestro_analyst.engine.chart_builders.statistical import (
    HeatmapBuilder, FunnelBuilder, DistributionBuilder,
)


@pytest.fixture
def num_df():
    return pd.DataFrame({
        "x": [1, 2, 3, 4], "y": [10, 20, 15, 25],
        "size": [5, 10, 8, 12], "cat": ["a", "b", "a", "b"],
    })


class TestBubbleBuilder:
    def test_name(self):
        assert BubbleBuilder.name == "bubble"

    def test_build(self, num_df):
        fig = BubbleBuilder().build(df=num_df, x="x", y="y", size="size")
        assert isinstance(fig, go.Figure)


class TestSankeyBuilder:
    def test_build(self):
        df = pd.DataFrame({
            "source": ["A", "A", "B"],
            "target": ["X", "Y", "X"],
            "value": [10, 5, 8],
        })
        fig = SankeyBuilder().build(df=df, source="source", target="target", values="value")
        assert isinstance(fig, go.Figure)


class TestTreemapBuilder:
    def test_build(self):
        df = pd.DataFrame({
            "name": ["Root", "A", "B"],
            "parent": ["", "Root", "Root"],
            "value": [0, 60, 40],
        })
        fig = TreemapBuilder().build(df=df, names="name", parents="parent", values="value")
        assert isinstance(fig, go.Figure)


class TestRadarBuilder:
    def test_build(self):
        df = pd.DataFrame({"cat": ["Speed", "Power", "Range"], "val": [80, 60, 70]})
        fig = RadarBuilder().build(df=df, x="cat", y="val")
        assert isinstance(fig, go.Figure)


class TestHeatmapBuilder:
    def test_build(self, num_df):
        fig = HeatmapBuilder().build(df=num_df)
        assert isinstance(fig, go.Figure)


class TestFunnelBuilder:
    def test_build(self):
        df = pd.DataFrame({"step": ["Visit", "Sign Up", "Pay"], "count": [1000, 300, 50]})
        fig = FunnelBuilder().build(df=df, names="step", values="count")
        assert isinstance(fig, go.Figure)
```

**Step 2: Run to verify fail**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_chart_advanced.py -v`

**Step 3: Write advanced.py**

```python
# src/maestro_analyst/engine/chart_builders/advanced.py
"""高级图表构建器: bubble, sankey, treemap, wordcloud, radar。"""
from __future__ import annotations

import base64
import io
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class BubbleBuilder:
    name = "bubble"
    description = "气泡图 (x, y, size, color)"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, size: str | None = None,
              color: str | None = None, text: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        if size is None:
            numeric = [c for c in df.select_dtypes(include="number").columns
                       if c not in (x, y)]
            size = numeric[0] if numeric else None
        return px.scatter(df, x=x, y=y, size=size, color=color, text=text,
                          title=title or "Bubble Chart", size_max=60)


class SankeyBuilder:
    name = "sankey"
    description = "桑基图 (source, target, value)"

    def build(self, *, df: pd.DataFrame, source: str | None = None,
              target: str | None = None, values: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        src_col = source or "source"
        tgt_col = target or "target"
        val_col = values or "value"

        all_labels = list(dict.fromkeys(
            df[src_col].tolist() + df[tgt_col].tolist()
        ))
        idx = {label: i for i, label in enumerate(all_labels)}

        vals = df[val_col].tolist() if val_col in df.columns else [1] * len(df)

        fig = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, label=all_labels),
            link=dict(
                source=[idx[s] for s in df[src_col]],
                target=[idx[t] for t in df[tgt_col]],
                value=vals,
            ),
        ))
        fig.update_layout(title=title or "Sankey Diagram")
        return fig


class TreemapBuilder:
    name = "treemap"
    description = "树图 (names, parents, values)"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              parents: str | None = None, values: str | None = None,
              color: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        kwargs: dict[str, Any] = {"title": title or "Treemap"}
        if names:
            kwargs["names"] = names
        if parents and parents in df.columns:
            kwargs["parents"] = parents
        if values and values in df.columns:
            kwargs["values"] = values
        if color and color in df.columns:
            kwargs["color"] = color
        return px.treemap(df, **kwargs)


class WordcloudBuilder:
    name = "wordcloud"
    description = "词云 (text column)"

    def build(self, *, df: pd.DataFrame, text: str | None = None,
              x: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        try:
            from wordcloud import WordCloud
        except ImportError:
            raise ImportError("词云需要 wordcloud 库: pip install wordcloud")

        col = text or x
        all_text = " ".join(df[col].dropna().astype(str).tolist())
        if not all_text.strip():
            from maestro_analyst.engine.chart_builders.basic import TableBuilder
            return TableBuilder().build(df=df, title=title or "词云（无文本）")

        wc = WordCloud(width=900, height=400, background_color="#1a1a2e",
                       colormap="Blues", max_words=100).generate(all_text)

        buf = io.BytesIO()
        wc.to_image().save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()

        fig = go.Figure()
        fig.add_layout_image(dict(
            source=f"data:image/png;base64,{b64}",
            xref="paper", yref="paper", x=0, y=1,
            sizex=1, sizey=1, xanchor="left", yanchor="top", layer="above",
        ))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(title=title or "Word Cloud",
                          width=900, height=450, margin=dict(l=0, r=0, t=40, b=0))
        return fig


class RadarBuilder:
    name = "radar"
    description = "雷达图 (categories, values)"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        cats = df[x].tolist()
        vals = df[y].tolist()
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", name=y or "value",
        ))
        fig.update_layout(title=title or "Radar Chart",
                          polar=dict(radialaxis=dict(visible=True)))
        return fig


__all_charts__ = [
    BubbleBuilder, SankeyBuilder, TreemapBuilder, WordcloudBuilder, RadarBuilder,
]
```

**Step 4: Write statistical.py**

```python
# src/maestro_analyst/engine/chart_builders/statistical.py
"""统计图表构建器: heatmap, distribution, funnel。"""
from __future__ import annotations
from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class HeatmapBuilder:
    name = "heatmap"
    description = "相关性热力图"

    def build(self, *, df: pd.DataFrame, title: str = "", **kw: Any) -> go.Figure:
        numeric = df.select_dtypes(include="number")
        corr = numeric.corr()
        return px.imshow(corr, text_auto=".2f", title=title or "Correlation Heatmap",
                         color_continuous_scale="RdBu_r")


class DistributionBuilder:
    name = "distribution"
    description = "分布图（直方图）"

    def build(self, *, df: pd.DataFrame, x: str | None = None,
              title: str = "", **kw: Any) -> go.Figure:
        fig = go.Figure()
        col = x or df.select_dtypes(include="number").columns[0]
        fig.add_trace(go.Histogram(x=df[col], name="分布", nbinsx=30))
        fig.update_layout(title=title or f"{col} Distribution")
        return fig


class FunnelBuilder:
    name = "funnel"
    description = "漏斗图"

    def build(self, *, df: pd.DataFrame, names: str | None = None,
              values: str | None = None, x: str | None = None,
              y: str | None = None, title: str = "", **kw: Any) -> go.Figure:
        n_col = names or x
        v_col = values or y
        fig = go.Figure(go.Funnel(
            y=df[n_col].tolist(),
            x=df[v_col].tolist(),
            textinfo="value+percent previous",
        ))
        fig.update_layout(title=title or "Funnel")
        return fig


__all_charts__ = [HeatmapBuilder, DistributionBuilder, FunnelBuilder]
```

**Step 5: Run tests**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_chart_advanced.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/maestro_analyst/engine/chart_builders/advanced.py \
        src/maestro_analyst/engine/chart_builders/statistical.py \
        tests/unit/test_chart_advanced.py
git commit -m "feat(charts): add advanced and statistical chart builders"
```

---

### Task 4: 重写 charts.py 为 Registry 路由

**Files:**
- Modify: `src/maestro_analyst/engine/charts.py`
- Create: `tests/unit/test_charts_registry.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_charts_registry.py
"""测试 charts 模块通过 registry 路由。"""
import pandas as pd
import plotly.graph_objects as go
import pytest

from maestro_analyst.engine.charts import make_chart, chart_registry, to_fragment, CHART_TYPES


@pytest.fixture
def df():
    return pd.DataFrame({"cat": ["A", "B", "C"], "val": [10, 20, 30]})


def test_chart_registry_has_all_types():
    for ct in ["bar", "line", "scatter", "histogram", "pie", "box", "table",
               "bubble", "sankey", "treemap", "radar", "heatmap", "funnel", "distribution"]:
        assert chart_registry.has(ct), f"Missing chart type: {ct}"


def test_make_chart_with_type(df):
    fig = make_chart(df, "bar", x="cat", y="val")
    assert isinstance(fig, go.Figure)


def test_make_chart_auto(df):
    fig = make_chart(df, x="cat", y="val")
    assert isinstance(fig, go.Figure)


def test_make_chart_unknown_type(df):
    with pytest.raises(KeyError, match="unknown_type"):
        make_chart(df, "unknown_type", x="cat", y="val")


def test_to_fragment(df):
    fig = make_chart(df, "bar", x="cat", y="val")
    html = to_fragment(fig)
    assert "<div" in html
    assert "<html" not in html


def test_chart_types_dict():
    assert isinstance(CHART_TYPES, dict)
    assert "bar" in CHART_TYPES
    assert "bubble" in CHART_TYPES
```

**Step 2: Run to verify fail**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_charts_registry.py -v`

**Step 3: Rewrite charts.py**

```python
# src/maestro_analyst/engine/charts.py
"""图表引擎 — Registry 路由到具体 Builder。

用法:
    fig = make_chart(df, "bubble", x="x", y="y", size="size")
    html = to_fragment(fig)
    path = save_chart(fig, "my_chart", fmt="html", fragment=True)

扩展:
    将自定义 Builder 放到 ~/.maestro/analyst/plugins/charts/
    Builder 需有 name 属性 + build(**kwargs) -> go.Figure 方法
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from maestro_analyst.core.config import OUTPUTS_DIR, PLUGINS_DIR, ensure_dirs
from maestro_analyst.core.registry import Registry


# ---------------------------------------------------------------------------
# 全局 chart registry
# ---------------------------------------------------------------------------

chart_registry = Registry("charts")


def _register_builtins() -> None:
    """注册所有内置图表构建器。"""
    from maestro_analyst.engine.chart_builders.basic import __all_charts__ as basic
    from maestro_analyst.engine.chart_builders.advanced import __all_charts__ as advanced
    from maestro_analyst.engine.chart_builders.statistical import __all_charts__ as stats

    for cls in basic + advanced + stats:
        chart_registry.register(cls)


_register_builtins()

# 加载用户插件
chart_registry.load_plugins(PLUGINS_DIR / "charts")


# ---------------------------------------------------------------------------
# CHART_TYPES — 兼容旧接口
# ---------------------------------------------------------------------------

CHART_TYPES: dict[str, str] = {
    item["name"]: item["description"]
    for item in chart_registry.list()
}


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------

def make_chart(
    df: pd.DataFrame,
    chart_type: str | None = None,
    **kwargs: Any,
) -> go.Figure:
    """统一图表创建接口。chart_type=None 时自动选型。"""
    if chart_type is None:
        return _auto_chart(df, **kwargs)

    builder_cls = chart_registry.get(chart_type)
    builder = builder_cls()
    return builder.build(df=df, **kwargs)


def to_fragment(fig: go.Figure) -> str:
    """返回图表的 <div> HTML 片段（不含 plotly.js）。"""
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False},
    )


def save_chart(fig: go.Figure, name: str, fmt: str = "html",
               fragment: bool = False) -> Path:
    """保存图表到文件。fragment=True 输出 <div> 片段。"""
    ensure_dirs()
    path = OUTPUTS_DIR / f"{name}.{fmt}"

    if fmt == "html":
        if fragment:
            path.write_text(to_fragment(fig))
        else:
            fig.write_html(str(path))
    elif fmt in ("png", "svg"):
        fig.write_image(str(path), format=fmt)

    return path


# ---------------------------------------------------------------------------
# 自动选型 (保持兼容)
# ---------------------------------------------------------------------------

def _auto_chart(df: pd.DataFrame, x: str | None = None,
                y: str | None = None, **kwargs: Any) -> go.Figure:
    """根据数据类型自动选择图表。"""
    if x is None and y is None:
        return _auto_detect(df, **kwargs)

    if x and y:
        x_dtype = df[x].dtype
        y_dtype = df[y].dtype

        if x_dtype == "object" and pd.api.types.is_numeric_dtype(y_dtype):
            return make_chart(df, "bar", x=x, y=y, **kwargs)
        if pd.api.types.is_datetime64_any_dtype(df[x]):
            return make_chart(df, "line", x=x, y=y, **kwargs)
        if pd.api.types.is_numeric_dtype(x_dtype) and pd.api.types.is_numeric_dtype(y_dtype):
            return make_chart(df, "scatter", x=x, y=y, **kwargs)

    return make_chart(df, "bar", x=x, y=y, **kwargs)


def _auto_detect(df: pd.DataFrame, **kwargs: Any) -> go.Figure:
    numeric = df.select_dtypes(include="number").columns.tolist()
    cat = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date = df.select_dtypes(include=["datetime64"]).columns.tolist()

    if date and numeric:
        return make_chart(df, "line", x=date[0], y=numeric[0], **kwargs)
    if cat and numeric:
        return make_chart(df, "bar", x=cat[0], y=numeric[0], **kwargs)
    if len(numeric) >= 2:
        return make_chart(df, "scatter", x=numeric[0], y=numeric[1], **kwargs)
    if numeric:
        return make_chart(df, "histogram", x=numeric[0], **kwargs)
    return make_chart(df, "table", **kwargs)


# ---------------------------------------------------------------------------
# 兼容旧函数签名（deprecated，保留到 0.3）
# ---------------------------------------------------------------------------

def auto_chart(df, x=None, y=None, title=""):
    return make_chart(df, x=x, y=y, title=title)

def distribution_chart(series, title=""):
    df = series.to_frame()
    return make_chart(df, "distribution", x=series.name, title=title)

def correlation_heatmap(df, title="相关性矩阵"):
    return make_chart(df, "heatmap", title=title)

def trend_chart(series, title=""):
    import plotly.express as px
    return px.line(x=series.index, y=series.values, title=title or f"{series.name} 趋势")

def funnel_chart(steps, title="漏斗分析"):
    df = pd.DataFrame({"step": list(steps.keys()), "count": list(steps.values())})
    return make_chart(df, "funnel", names="step", values="count", title=title)
```

**Step 4: Add PLUGINS_DIR to config.py**

在 `config.py` 中 `OUTPUTS_DIR` 行后加:

```python
PLUGINS_DIR = BASE_DIR / "plugins"
```

并在 `ensure_dirs()` 的 for 循环中加入 `PLUGINS_DIR`。

**Step 5: Run tests**

Run: `cd ~/maestro-analyst && pytest tests/unit/ -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/maestro_analyst/engine/charts.py src/maestro_analyst/core/config.py \
        tests/unit/test_charts_registry.py
git commit -m "refactor(charts): route through Registry, support plugins"
```

---

### Task 5: AnalysisStrategy 协议 + 策略拆分

**Files:**
- Create: `src/maestro_analyst/engine/strategies/__init__.py`
- Create: `src/maestro_analyst/engine/strategies/profile.py`
- Create: `src/maestro_analyst/engine/strategies/compare.py`
- Create: `src/maestro_analyst/engine/strategies/trend.py`
- Create: `src/maestro_analyst/engine/strategies/funnel.py`
- Modify: `src/maestro_analyst/engine/analyzer.py`
- Create: `tests/unit/test_strategies.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_strategies.py
"""分析策略测试。"""
import pandas as pd
import pytest

from maestro_analyst.engine.strategies.profile import ProfileStrategy
from maestro_analyst.engine.strategies.compare import CompareStrategy
from maestro_analyst.engine.strategies.trend import TrendStrategy
from maestro_analyst.engine.strategies.funnel import FunnelStrategy
from maestro_analyst.engine.analyzer import AnalysisResult


@pytest.fixture
def sales_df():
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=12, freq="ME"),
        "revenue": [100, 120, 110, 130, 140, 135, 150, 160, 155, 170, 180, 190],
        "region": ["US", "EU"] * 6,
    })


class TestProfileStrategy:
    def test_name(self):
        assert ProfileStrategy.name == "profile"

    def test_analyze(self, sales_df):
        result = ProfileStrategy().analyze(df=sales_df, table_name="sales")
        assert isinstance(result, AnalysisResult)
        assert result.row_count == 12
        assert len(result.insights) > 0


class TestCompareStrategy:
    def test_name(self):
        assert CompareStrategy.name == "compare"

    def test_analyze(self, sales_df):
        result = CompareStrategy().analyze(
            df=sales_df, table_name="sales",
            group_col="region", metric_cols=["revenue"],
        )
        assert isinstance(result, AnalysisResult)
        assert any("revenue" in i.title for i in result.insights)


class TestTrendStrategy:
    def test_name(self):
        assert TrendStrategy.name == "trend"

    def test_analyze(self, sales_df):
        result = TrendStrategy().analyze(
            df=sales_df, table_name="sales",
            date_col="date", metric_col="revenue",
        )
        assert isinstance(result, AnalysisResult)
        assert any("trend" in i.category for i in result.insights)


class TestFunnelStrategy:
    def test_name(self):
        assert FunnelStrategy.name == "funnel"

    def test_analyze(self):
        result = FunnelStrategy().analyze(
            steps={"Visit": 1000, "SignUp": 300, "Pay": 50},
        )
        assert isinstance(result, AnalysisResult)
        assert any("funnel" in i.category for i in result.insights)
```

**Step 2: Run to verify fail**

Run: `cd ~/maestro-analyst && pytest tests/unit/test_strategies.py -v`

**Step 3: Write strategy files**

每个策略文件从现有 `analyzer.py` 的对应方法提取，改为独立类，实现 `analyze(**kwargs) -> AnalysisResult`。`analyzer.py` 瘦身为路由壳。

strategy `__init__.py`:
```python
# src/maestro_analyst/engine/strategies/__init__.py
"""分析策略包。每个 strategy 实现 analyze(**kwargs) -> AnalysisResult。"""
```

profile.py — 从 `Analyzer.profile()` 提取
compare.py — 从 `Analyzer.compare()` 提取
trend.py — 从 `Analyzer.trend()` 提取
funnel.py — 从 `Analyzer.funnel()` 提取

每个类必须有:
- `name: str` 类属性
- `description: str` 类属性
- `def analyze(self, **kwargs) -> AnalysisResult` 方法

analyzer.py 瘦身为:
```python
class Analyzer:
    def __init__(self, store):
        self._store = store

    def run(self, strategy_name, table_name, **kwargs):
        from maestro_analyst.engine.analyzer import analysis_registry
        strategy_cls = analysis_registry.get(strategy_name)
        df = self._store.query(f"SELECT * FROM {table_name}")
        return strategy_cls().analyze(df=df, table_name=table_name, **kwargs)

    # 兼容方法
    def profile(self, table_name):
        return self.run("profile", table_name)

    def compare(self, table_name, group_col, metric_cols):
        return self.run("compare", table_name, group_col=group_col, metric_cols=metric_cols)

    def trend(self, table_name, date_col, metric_col, freq="ME"):
        return self.run("trend", table_name, date_col=date_col, metric_col=metric_col, freq=freq)

    def funnel(self, steps):
        from maestro_analyst.engine.strategies.funnel import FunnelStrategy
        return FunnelStrategy().analyze(steps=steps)
```

**Step 4: Run tests**

Run: `cd ~/maestro-analyst && pytest tests/unit/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add src/maestro_analyst/engine/strategies/ src/maestro_analyst/engine/analyzer.py \
        tests/unit/test_strategies.py
git commit -m "refactor(analyzer): extract strategies to plugin classes"
```

---

### Task 6: CLI 适配 + 集成测试

**Files:**
- Modify: `src/maestro_analyst/cli/__init__.py` (已有的 chart 命令不变，验证正常)
- Create: `tests/integration/test_cli.py`

**Step 1: Write CLI integration tests**

```python
# tests/integration/test_cli.py
"""CLI 集成测试。"""
import subprocess
import sys

import pytest


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "maestro_analyst", *args],
        capture_output=True, text=True, timeout=30,
    )


def test_tables():
    r = run_cli("tables")
    assert r.returncode == 0


def test_chart_help():
    r = run_cli("chart", "--help")
    assert r.returncode == 0
    assert "--type" in r.stdout


def test_chart_types_listed():
    r = run_cli("chart", "--help")
    assert "bubble" in r.stdout or "bar" in r.stdout
```

**Step 2: Run**

Run: `cd ~/maestro-analyst && pytest tests/ -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add tests/integration/test_cli.py
git commit -m "test: add CLI integration tests"
```

---

### Task 7: Plugin 示例 + 文档

**Files:**
- Create: `examples/custom_chart_plugin.py`

**Step 1: Write a sample plugin**

```python
# examples/custom_chart_plugin.py
"""示例: 自定义图表插件。

复制到 ~/.maestro/analyst/plugins/charts/ 即可使用:
    manalyze chart my_table --type waterfall --x category --y value
"""
import pandas as pd
import plotly.graph_objects as go


class WaterfallBuilder:
    name = "waterfall"
    description = "瀑布图"

    def build(self, *, df, x=None, y=None, title="", **kw):
        fig = go.Figure(go.Waterfall(
            x=df[x].tolist(),
            y=df[y].tolist(),
            textposition="outside",
        ))
        fig.update_layout(title=title or "Waterfall Chart")
        return fig


__all_charts__ = [WaterfallBuilder]
```

**Step 2: Commit + push**

```bash
git add examples/custom_chart_plugin.py
git commit -m "docs: add custom chart plugin example"
git push origin main
```

---

**总结: 7 个 Task，预计改动:**
- 新建 9 个文件（4 builder + 4 strategy + 1 registry）
- 重写 2 个文件（charts.py, analyzer.py）
- 小改 1 个文件（config.py）
- 新建 5 个测试文件
- CLI 不变，只验证
