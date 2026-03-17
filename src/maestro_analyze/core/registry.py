"""通用插件注册表。

Chart builders 和 Analysis strategies 共用此机制。
用法:
    registry = Registry("charts")
    registry.register(BarChartBuilder)
    builder_cls = registry.get("bar")
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
        """注册一个类。可用作装饰器。"""
        name = getattr(cls, "name", None)
        if name is None:
            raise ValueError(f"注册到 {self.domain} 的类必须有 'name' 属性: {cls}")
        if name in self._items:
            warnings.warn(f"[{self.domain}] '{name}' 已存在，将被覆盖", stacklevel=2)
        self._items[name] = cls
        return cls

    def get(self, name: str) -> type:
        """按名称获取已注册的类。"""
        if name not in self._items:
            available = ", ".join(sorted(self._items))
            raise KeyError(f"[{self.domain}] 未知类型 '{name}'。可用: {available}")
        return self._items[name]

    def has(self, name: str) -> bool:
        return name in self._items

    def list(self) -> list[dict[str, str]]:
        return [
            {"name": getattr(cls, "name", ""), "description": getattr(cls, "description", "")}
            for cls in self._items.values()
        ]

    def names(self) -> list[str]:
        return sorted(self._items.keys())

    def load_plugins(self, plugins_dir: Path) -> int:
        """从目录加载插件 .py 文件。返回新加载的数量。"""
        if not plugins_dir.is_dir():
            return 0
        loaded = 0
        for py_file in sorted(plugins_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            try:
                mod = self._import_file(py_file)
                export_attr = f"__all_{self.domain}__"
                exportables = getattr(mod, export_attr, None)
                if exportables:
                    for cls in exportables:
                        self.register(cls)
                        loaded += 1
                else:
                    for attr_name in dir(mod):
                        obj = getattr(mod, attr_name)
                        if (isinstance(obj, type)
                                and hasattr(obj, "name")
                                and hasattr(obj, "build")
                                and obj.__module__ == mod.__name__):
                            self.register(obj)
                            loaded += 1
            except Exception as exc:
                warnings.warn(f"[{self.domain}] 加载插件 {py_file.name} 失败: {exc}")
        return loaded

    @staticmethod
    def _import_file(file_path: Path) -> Any:
        module_name = f"maestro_plugin_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {file_path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod
