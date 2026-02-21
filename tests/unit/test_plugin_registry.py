"""Tests for P1-P1 PluginRegistry"""
import threading
import pytest
from vjlive3.plugins.registry import PluginRegistry, PluginStatus


class FakePlugin:
    METADATA = {"name": "Fake", "description": "A" * 50}
    def process(self, frame, audio): return frame


_MANIFEST = {
    "id": "com.test.fake", "name": "Fake", "version": "1.0.0",
    "description": "A" * 50, "author": "Test", "category": "effect", "tags": ["test"]
}


@pytest.fixture
def reg():
    return PluginRegistry()


def test_register_and_get(reg):
    assert reg.register("fake", FakePlugin, _MANIFEST)
    assert reg.get("fake") is FakePlugin


def test_register_duplicate_warns(reg, caplog):
    reg.register("fake", FakePlugin, _MANIFEST)
    import logging
    with caplog.at_level(logging.WARNING):
        reg.register("fake", FakePlugin, _MANIFEST)
    assert "already registered" in caplog.text


def test_register_empty_name_raises(reg):
    with pytest.raises(ValueError):
        reg.register("", FakePlugin, _MANIFEST)
    with pytest.raises(ValueError):
        reg.register("   ", FakePlugin, _MANIFEST)


def test_register_non_callable_raises(reg):
    with pytest.raises(ValueError):
        reg.register("bad", "not_a_class", _MANIFEST)  # type: ignore


def test_list_names(reg):
    reg.register("b", FakePlugin, _MANIFEST)
    reg.register("a", FakePlugin, _MANIFEST)
    names = reg.list_names()
    assert names == ["a", "b"]  # sorted


def test_list_all_info(reg):
    reg.register("fake", FakePlugin, _MANIFEST)
    infos = reg.list_all()
    assert len(infos) == 1
    assert infos[0].name == "Fake"   # from manifest["name"] = "Fake"
    assert infos[0].version == "1.0.0"


def test_unregister(reg):
    reg.register("fake", FakePlugin, _MANIFEST)
    assert reg.unregister("fake")
    assert reg.get("fake") is None


def test_unregister_nonexistent(reg):
    assert reg.unregister("ghost") is False


def test_clear(reg):
    reg.register("fake", FakePlugin, _MANIFEST)
    reg.clear()
    assert reg.list_names() == []


def test_thread_safety(reg):
    errors = []

    def worker(i):
        try:
            m = dict(_MANIFEST, name=f"Plugin{i}", id=f"com.test.p{i}")
            reg.register(f"plugin{i}", FakePlugin, m)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert not errors
    assert len(reg.list_names()) == 10


def test_get_modules_flat_single(reg):
    reg.register("fake", FakePlugin, _MANIFEST)
    modules = reg.get_modules_flat()
    assert len(modules) == 1
    assert modules[0]["plugin_id"] == "com.test.fake"


def test_get_modules_flat_multi(reg):
    multi_manifest = dict(_MANIFEST, modules=[
        {"id": "mod_a", "name": "Module A", "class_name": "ClsA"},
        {"id": "mod_b", "name": "Module B", "class_name": "ClsB"},
    ])
    reg.register("multi", FakePlugin, multi_manifest)
    modules = reg.get_modules_flat()
    assert len(modules) == 2
    ids = {m["id"] for m in modules}
    assert "com.test.fake::mod_a" in ids
    assert "com.test.fake::mod_b" in ids


def test_instance_count(reg):
    reg.register("fake", FakePlugin, _MANIFEST)
    reg.increment_instance_count("fake")
    info = reg.get_info("fake")
    assert info is not None
    assert info.instance_count == 1
    assert info.status == PluginStatus.LOADED
