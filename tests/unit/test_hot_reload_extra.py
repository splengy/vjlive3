import pytest
import time
import threading
from unittest.mock import patch, MagicMock

from vjlive3.plugins.hot_reload import PluginHotReloadWatcher, PluginFileHandler

class TestPluginHotReloadWatcherExtra:
    def test_file_handler_debounce_trigger_created(self):
        fired = []
        h = PluginFileHandler(on_modified=lambda p: fired.append(p))
        evt = MagicMock()
        evt.is_directory = False
        evt.src_path = "/tmp/test.py"
        h.on_created(evt)
        assert len(fired) == 1

    def test_file_handler_ignores_other_extensions(self):
        fired = []
        h = PluginFileHandler(on_modified=lambda p: fired.append(p))
        evt = MagicMock()
        evt.is_directory = False
        evt.src_path = "/tmp/test.txt"
        h.on_modified(evt)
        assert len(fired) == 0

    def test_watcher_ensure_dirs_error(self):
        with patch('pathlib.Path.mkdir', side_effect=Exception("mocked error")):
            w = PluginHotReloadWatcher(['/sys/ro_dir'])
            assert not w.is_running  # Should fail gracefully and not crash

    def test_watcher_reload_async_exception(self):
        def crashy_cb(path):
            raise RuntimeError("crash on hot reload")
        
        w = PluginHotReloadWatcher(['/tmp'], on_change=crashy_cb)
        w._on_file_changed("/tmp/test.py")
        
        time.sleep(0.3)  # Wait for threads
        assert w._pending_path is None

    def test_set_on_change(self):
        w = PluginHotReloadWatcher(['/tmp'])
        mock = MagicMock()
        w.set_on_change(mock)
        w._on_change("test")
        mock.assert_called_with("test")
