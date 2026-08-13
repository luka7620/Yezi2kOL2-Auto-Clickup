import json
import os
import tempfile
import unittest
from unittest import mock

try:
    import tkinter as tk
except ImportError as error:
    raise unittest.SkipTest(f"未安装 Tk：{error}")

import app_config
from config_gui import ConfigGUI
from progress_window import ProgressWindow


class TkTestCase(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError as error:
            self.skipTest(f"无可用图形显示：{error}")

    def tearDown(self):
        if hasattr(self, "root"):
            self.root.destroy()


class ConfigGUISmokeTests(TkTestCase):
    @staticmethod
    def read_bytes(path):
        with open(path, "rb") as source:
            return source.read()

    def make_gui(self, path):
        gui = ConfigGUI(self.root, config_path=path)
        gui.path_var.set(__file__)
        return gui

    def test_all_keys_bound_and_round_trip_preserves_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            with open(path, "w", encoding="utf-8") as target:
                json.dump({"custom_key": 1}, target)
            gui = self.make_gui(path)
            self.assertEqual(set(gui.config_vars), set(app_config.DEFAULT_CONFIG))
            gui.window_keyword_var.set("新窗口")
            gui.button_wait_var.set("6")
            gui.show_progress_var.set(False)
            gui.keep_window_topmost_var.set(True)
            with mock.patch("config_gui.messagebox.showinfo"):
                self.assertTrue(gui.save_config_action())
            saved = app_config.load_config(path)
            self.assertEqual(saved["custom_key"], 1)
            self.assertEqual(saved["window_keyword"], "新窗口")
            self.assertEqual(saved["button_wait"], 6)
            self.assertFalse(saved["show_progress"])
            self.assertTrue(saved["keep_window_topmost"])

    def test_errors_and_warnings_control_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            app_config.save_config(path, {"custom_key": 1})
            gui = self.make_gui(path)
            original = self.read_bytes(path)
            gui.path_var.set("")
            with mock.patch("config_gui.messagebox.showerror") as showerror:
                self.assertFalse(gui.save_config_action())
                showerror.assert_called_once()
            self.assertEqual(self.read_bytes(path), original)

            gui.path_var.set(os.path.join(directory, "missing.exe"))
            with mock.patch("config_gui.messagebox.askyesno", return_value=False):
                self.assertFalse(gui.save_config_action())
            self.assertEqual(self.read_bytes(path), original)
            with mock.patch("config_gui.messagebox.askyesno", return_value=True), mock.patch("config_gui.messagebox.showinfo"):
                self.assertTrue(gui.save_config_action())
            self.assertNotEqual(self.read_bytes(path), original)

    def test_missing_targets_do_not_run_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            app_config.save_config(path, {"anjian_path": __file__})
            gui = self.make_gui(path)
            missing = {
                "args": ["missing"], "workdir": directory,
                "target_path": os.path.join(directory, "missing.py"),
                "interpreter_path": None, "warnings": [],
            }
            with mock.patch.object(gui, "_launch_info", return_value=missing), \
                    mock.patch("config_gui.subprocess.Popen") as popen, \
                    mock.patch("config_gui.subprocess.run") as run, \
                    mock.patch("config_gui.messagebox.showerror") as showerror:
                self.assertFalse(gui.test_script())
                self.assertFalse(gui.setup_autostart())
                popen.assert_not_called()
                run.assert_not_called()
                self.assertEqual(showerror.call_count, 2)

            target = os.path.join(directory, "auto_clicker.py")
            with open(target, "w", encoding="utf-8"):
                pass
            missing_interpreter = dict(
                missing,
                command=os.path.join(directory, "missing-python.exe"),
                arguments=f'"{target}"',
                target_path=target,
                interpreter_path=os.path.join(directory, "missing-python.exe"),
            )
            with mock.patch.object(gui, "_launch_info", return_value=missing_interpreter), \
                    mock.patch("config_gui.subprocess.run") as run, \
                    mock.patch("config_gui.messagebox.showerror"):
                self.assertFalse(gui.setup_autostart())
                run.assert_not_called()


class ProgressWindowSmokeTests(unittest.TestCase):
    def test_public_updates_set_progressbar(self):
        try:
            window = ProgressWindow()
            window.root.withdraw()
        except tk.TclError as error:
            self.skipTest(f"无可用图形显示：{error}")
        try:
            window.update_progress(50)
            window.add_log("测试日志", "SUCCESS")
            window.update_status("测试状态")
            window.update_messages()
            self.assertEqual(float(window.progress_bar["value"]), 50)
        finally:
            window.should_close = True
            window.root.destroy()


if __name__ == "__main__":
    unittest.main()
