import importlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


_STUB_NAMES = ("win32gui", "win32con", "win32process", "win32api", "psutil")
_stubs = {
    name: mock.MagicMock()
    for name in _STUB_NAMES
    if importlib.util.find_spec(name) is None
}
with mock.patch.dict(sys.modules, _stubs):
    auto_clicker = importlib.import_module("auto_clicker")
AnjianAutoClicker = auto_clicker.AnjianAutoClicker


class AutoClickerConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.temp_directory = tempfile.TemporaryDirectory()
        os.chdir(self.temp_directory.name)
        self.clicker = AnjianAutoClicker()
        self.clicker.config_file = os.path.join(self.temp_directory.name, "config.json")

    def tearDown(self):
        for handler in list(self.clicker.logger.handlers):
            handler.close()
            self.clicker.logger.removeHandler(handler)
        os.chdir(self.original_cwd)
        self.temp_directory.cleanup()

    def test_partial_config_merges_defaults(self):
        with open(self.clicker.config_file, "w", encoding="utf-8") as target:
            json.dump({"show_progress": True}, target)
        self.assertTrue(self.clicker.load_config())
        expected = {
            "boot_delay": 15,
            "start_hour": 8,
            "end_hour": 22,
            "button1_text": "开始使用",
            "button2_text": "启动",
            "active_days": [0, 1, 2, 3, 4, 5, 6],
        }
        for key, value in expected.items():
            self.assertEqual(self.clicker.config[key], value)

    def test_broken_config_fails_and_logs(self):
        with open(self.clicker.config_file, "w", encoding="utf-8") as target:
            target.write("not json")
        with self.assertLogs(self.clicker.logger, level="ERROR") as captured:
            self.assertFalse(self.clicker.load_config())
        self.assertIn("加载配置文件失败", "\n".join(captured.output))

    def test_semantically_broken_config_fails_gracefully(self):
        with open(self.clicker.config_file, "w", encoding="utf-8") as target:
            json.dump({"start_hour": "abc"}, target)
        with self.assertLogs(self.clicker.logger, level="ERROR") as captured:
            self.assertFalse(self.clicker.load_config())
        self.assertIn("加载配置文件失败", "\n".join(captured.output))

    def test_missing_config_still_required(self):
        with self.assertLogs(self.clicker.logger, level="ERROR") as captured:
            self.assertFalse(self.clicker.load_config())
        self.assertIn("配置文件不存在", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
