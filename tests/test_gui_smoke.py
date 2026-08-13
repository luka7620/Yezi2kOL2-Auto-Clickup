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
import task_scheduler
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

    def test_broken_config_shows_error_and_blocks_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            broken = b'{"start_hour": '
            with open(path, "wb") as target:
                target.write(broken)

            with mock.patch("config_gui.messagebox.showerror") as showerror:
                gui = ConfigGUI(self.root, config_path=path)
            showerror.assert_called_once()
            self.assertIsNotNone(gui.load_error)
            self.assertEqual(gui.start_hour_var.get(), "8")
            gui.path_var.set(__file__)

            with mock.patch("config_gui.messagebox.askyesno", return_value=False):
                self.assertFalse(gui.save_config_action())
            self.assertEqual(self.read_bytes(path), broken)

            with mock.patch("config_gui.messagebox.askyesno", return_value=True), \
                    mock.patch("config_gui.messagebox.showinfo"):
                self.assertTrue(gui.save_config_action())
            self.assertIsNone(gui.load_error)
            self.assertEqual(app_config.load_config(path)["anjian_path"], __file__)

    def test_semantically_broken_config_opens_recovery_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            broken = b'{"active_days": null, "start_hour": "abc"}'
            with open(path, "wb") as target:
                target.write(broken)

            with mock.patch("config_gui.messagebox.showerror") as showerror:
                gui = ConfigGUI(self.root, config_path=path)
            showerror.assert_called_once()
            self.assertIsNotNone(gui.load_error)
            self.assertEqual(gui.start_hour_var.get(), "8")
            gui.path_var.set(__file__)

            with mock.patch("config_gui.messagebox.askyesno", return_value=False):
                self.assertFalse(gui.save_config_action())
            self.assertEqual(self.read_bytes(path), broken)

            with mock.patch("config_gui.messagebox.askyesno", return_value=True), \
                    mock.patch("config_gui.messagebox.showinfo"):
                self.assertTrue(gui.save_config_action())
            self.assertIsNone(gui.load_error)
            self.assertEqual(app_config.load_config(path)["start_hour"], 8)

    def test_missing_config_uses_defaults_without_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            with mock.patch("config_gui.messagebox.showerror") as showerror:
                gui = ConfigGUI(self.root, config_path=path)
            showerror.assert_not_called()
            self.assertIsNone(gui.load_error)
            self.assertEqual(gui.start_hour_var.get(), "8")

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
                    mock.patch("config_gui.task_scheduler.create_autostart_task") as create_task, \
                    mock.patch("config_gui.messagebox.showerror") as showerror:
                self.assertFalse(gui.test_script())
                self.assertFalse(gui.setup_autostart())
                popen.assert_not_called()
                create_task.assert_not_called()
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
                    mock.patch("config_gui.task_scheduler.create_autostart_task") as create_task, \
                    mock.patch("config_gui.messagebox.showerror"):
                self.assertFalse(gui.setup_autostart())
                create_task.assert_not_called()

    def test_setup_and_remove_autostart_present_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "config.json")
            target = os.path.join(directory, "auto_clicker.py")
            with open(target, "w", encoding="utf-8"):
                pass
            app_config.save_config(path, {"anjian_path": __file__})
            gui = self.make_gui(path)
            info = {
                "command": target,
                "arguments": "",
                "workdir": directory,
                "target_path": target,
                "interpreter_path": None,
                "warnings": [],
            }

            success = task_scheduler.SchedulerResult(True, "ok", "成功")
            failure = task_scheduler.SchedulerResult(False, "error", "拒绝访问")
            with mock.patch.object(gui, "_launch_info", return_value=info), \
                    mock.patch("config_gui.task_scheduler.create_autostart_task", return_value=success), \
                    mock.patch("config_gui.messagebox.showinfo") as showinfo:
                self.assertTrue(gui.setup_autostart())
                showinfo.assert_called_once()
                self.assertEqual(gui.status_var.get(), "开机自启已设置")
            with mock.patch.object(gui, "_launch_info", return_value=info), \
                    mock.patch("config_gui.task_scheduler.create_autostart_task", return_value=failure), \
                    mock.patch("config_gui.messagebox.showerror") as showerror:
                self.assertFalse(gui.setup_autostart())
                showerror.assert_called_once()
                self.assertEqual(gui.status_var.get(), "设置失败")

            cases = (
                (task_scheduler.SchedulerResult(True, "ok", "成功"), True, "已取消开机自启"),
                (task_scheduler.SchedulerResult(False, "not_found", "找不到"), False, "取消失败或任务不存在"),
                (task_scheduler.SchedulerResult(False, "error", "拒绝访问"), False, "取消失败或任务不存在"),
            )
            for result, expected, status in cases:
                with self.subTest(result=result.status), \
                        mock.patch("config_gui.task_scheduler.delete_autostart_task", return_value=result), \
                        mock.patch("config_gui.messagebox.showinfo") as showinfo, \
                        mock.patch("config_gui.messagebox.showerror") as showerror:
                    self.assertEqual(gui.remove_autostart(), expected)
                    self.assertEqual(gui.status_var.get(), status)
                    if result.status == "error":
                        showerror.assert_called_once()
                    else:
                        showinfo.assert_called_once()


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
