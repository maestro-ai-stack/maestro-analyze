"""Registry 核心测试。"""
import pytest
from maestro_analyze.core.registry import Registry


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


def test_has():
    reg = Registry("test")
    reg.register(DummyBuilder)
    assert reg.has("dummy")
    assert not reg.has("nonexistent")
