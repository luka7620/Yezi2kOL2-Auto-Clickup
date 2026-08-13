import json
import os
import tempfile
import unittest

import app_config


class AppConfigTests(unittest.TestCase):
    EXPECTED = {
        "anjian_path": "", "start_hour": 8, "start_minute": 0,
        "end_hour": 22, "end_minute": 0,
        "active_days": [0, 1, 2, 3, 4, 5, 6], "boot_delay": 15,
        "launch_wait": 8, "retry_count": 5, "retry_interval": 3,
        "button_wait": 4, "button1_text": "开始使用", "button2_text": "启动",
        "window_keyword": "", "show_progress": True,
        "keep_window_topmost": False,
    }

    def test_defaults_and_example_contract(self):
        self.assertEqual(app_config.DEFAULT_CONFIG, self.EXPECTED)
        with open(os.path.join(os.path.dirname(__file__), "..", "config.example.json"), encoding="utf-8") as source:
            example = json.load(source)
        self.assertEqual(set(example), set(self.EXPECTED))
        for key, value in self.EXPECTED.items():
            if key not in {"anjian_path", "window_keyword"}:
                self.assertEqual(example[key], value)

    def test_load_missing_partial_and_broken(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            first = app_config.load_config(path)
            self.assertEqual(first, self.EXPECTED)
            first["active_days"].append(99)
            self.assertNotIn(99, app_config.load_config(path)["active_days"])
            with open(path, "w", encoding="utf-8") as target:
                json.dump({"start_hour": 9}, target)
            self.assertEqual(app_config.load_config(path)["start_hour"], 9)
            self.assertEqual(app_config.load_config(path)["end_hour"], 22)
            with open(path, "w", encoding="utf-8") as target:
                target.write("not json")
            with self.assertRaises(app_config.ConfigLoadError):
                app_config.load_config(path)
            with open(path, "w", encoding="utf-8") as target:
                json.dump([1, 2], target)
            with self.assertRaises(app_config.ConfigLoadError):
                app_config.load_config(path)

    def test_save_config_blocks_broken_file_unless_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            broken = b'{"start_hour": '
            with open(path, "wb") as target:
                target.write(broken)
            with self.assertRaises(app_config.ConfigLoadError):
                app_config.save_config(path, {"start_hour": 9})
            with open(path, "rb") as source:
                self.assertEqual(source.read(), broken)

            app_config.save_config(path, {"start_hour": 9}, reset=True)
            loaded = app_config.load_config(path)
            self.assertEqual(loaded["start_hour"], 9)
            self.assertEqual(loaded["end_hour"], self.EXPECTED["end_hour"])
            self.assertEqual(set(loaded), set(self.EXPECTED))

    def test_resolve_show_progress_missing_partial_and_broken(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            expected_default = app_config.DEFAULT_CONFIG["show_progress"]
            self.assertEqual(app_config.resolve_show_progress(path), expected_default)
            with open(path, "w", encoding="utf-8") as target:
                json.dump({"show_progress": False}, target)
            self.assertFalse(app_config.resolve_show_progress(path))
            with open(path, "w", encoding="utf-8") as target:
                target.write("not json")
            self.assertEqual(app_config.resolve_show_progress(path), expected_default)

    def test_save_preserves_unknown_key_and_chinese(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            with open(path, "w", encoding="utf-8") as target:
                json.dump({"custom_key": 1}, target)
            app_config.save_config(path, {"button1_text": "中文按钮"})
            with open(path, "r", encoding="utf-8") as source:
                text = source.read()
            self.assertIn("中文按钮", text)
            self.assertNotIn("\\u4e2d", text)
            self.assertEqual(json.loads(text)["custom_key"], 1)

    def test_validate_raw_fields(self):
        valid = {key: str(app_config.DEFAULT_CONFIG[key]) for key in app_config.NUMBER_RULES}
        self.assertTrue(app_config.validate_raw_fields(valid).ok)
        for key, value in (("boot_delay", ""), ("boot_delay", "abc"), ("boot_delay", "999")):
            invalid = dict(valid)
            invalid[key] = value
            self.assertFalse(app_config.validate_raw_fields(invalid).ok)

    def test_validate_config_semantics(self):
        base = dict(self.EXPECTED)
        for changes in (
            {"anjian_path": ""},
            {"anjian_path": __file__, "start_hour": 8, "end_hour": 8},
            {"anjian_path": __file__, "start_hour": 22, "end_hour": 8},
            {"anjian_path": __file__, "active_days": []},
            {"anjian_path": __file__, "button1_text": ""},
            {"anjian_path": __file__, "button2_text": ""},
        ):
            config = dict(base)
            config.update(changes)
            self.assertFalse(app_config.validate_config(config).ok)
        warning = dict(base, anjian_path=os.path.join(tempfile.gettempdir(), "missing-anjian.exe"))
        result = app_config.validate_config(warning)
        self.assertTrue(result.ok)
        self.assertTrue(result.warnings)

    def test_config_path_is_absolute_and_cwd_independent(self):
        original = os.getcwd()
        before = app_config.get_config_path()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                after = app_config.get_config_path()
        finally:
            os.chdir(original)
        self.assertTrue(os.path.isabs(before))
        self.assertEqual(before, after)

    def test_resolve_test_commands(self):
        app_dir = os.path.abspath("some app")
        python = os.path.abspath("python.exe")
        source = app_config.resolve_launch_command("test", False, app_dir, python)
        self.assertEqual(source["args"], [python, os.path.join(app_dir, "auto_clicker.py"), "--test"])
        self.assertEqual(source["workdir"], app_dir)
        self.assertEqual(source["target_path"], os.path.join(app_dir, "auto_clicker.py"))
        self.assertEqual(source["interpreter_path"], python)
        frozen = app_config.resolve_launch_command("test", True, app_dir, python)
        executable = os.path.join(app_dir, "按键精灵自动启动.exe")
        self.assertEqual(frozen["args"], [executable, "--test"])
        self.assertEqual(frozen["workdir"], app_dir)
        self.assertEqual(frozen["target_path"], executable)
        self.assertIsNone(frozen["interpreter_path"])

    def test_resolve_autostart_commands_and_pythonw_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            python = os.path.join(directory, "python.exe")
            with open(python, "w", encoding="utf-8"):
                pass
            source = app_config.resolve_launch_command("autostart", False, directory, python)
            self.assertEqual(source["command"], python)
            self.assertEqual(source["interpreter_path"], python)
            self.assertTrue(source["warnings"])
            self.assertEqual(source["arguments"], f'"{os.path.join(directory, "auto_clicker.py")}"')
            self.assertEqual(source["workdir"], directory)
            self.assertEqual(source["target_path"], os.path.join(directory, "auto_clicker.py"))
            pythonw = os.path.join(directory, "pythonw.exe")
            with open(pythonw, "w", encoding="utf-8"):
                pass
            source = app_config.resolve_launch_command("autostart", False, directory, python)
            self.assertEqual(source["command"], pythonw)
            self.assertFalse(source["warnings"])

            frozen = app_config.resolve_launch_command("autostart", True, directory, python)
            self.assertEqual(frozen["command"], os.path.join(directory, "按键精灵自动启动.exe"))
            self.assertEqual(frozen["arguments"], "")
            self.assertEqual(frozen["workdir"], directory)
            self.assertEqual(frozen["target_path"], os.path.join(directory, "按键精灵自动启动.exe"))
            self.assertIsNone(frozen["interpreter_path"])


if __name__ == "__main__":
    unittest.main()
