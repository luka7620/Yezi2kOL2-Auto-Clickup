"""按键精灵自动启动脚本 - 配置界面。"""
import html
import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import app_config


class ConfigGUI:
    def __init__(self, root, config_path=None):
        self.root = root
        self.root.title("按键精灵自动启动配置")
        self.root.geometry("700x600")
        self.root.minsize(640, 520)
        self.root.resizable(True, True)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.config_file = os.path.abspath(config_path or app_config.get_config_path())
        self.config = app_config.load_config(self.config_file)
        self.create_widgets()
        self.load_values()

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        ttk.Label(main, text="按键精灵自动启动配置", font=("Microsoft YaHei", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        self.notebook = ttk.Notebook(main)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        basic = self._make_tab("基础设置")
        schedule = self._make_tab("时间计划")
        advanced = self._make_tab("高级参数")
        options = self._make_tab("运行选项")
        self._create_basic_tab(basic)
        self._create_schedule_tab(schedule)
        self._create_advanced_tab(advanced)
        self._create_options_tab(options)

        actions = ttk.Frame(main)
        actions.grid(row=2, column=0, sticky="ew", pady=(12, 8))
        for text, command in (
            ("保存配置", self.save_config_action),
            ("测试运行", self.test_script),
            ("设置开机自启", self.setup_autostart),
            ("取消开机自启", self.remove_autostart),
        ):
            ttk.Button(actions, text=text, command=command).pack(side=tk.LEFT, padx=(0, 8))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).grid(
            row=3, column=0, sticky="ew"
        )

        self.config_vars = {
            "anjian_path": self.path_var,
            "start_hour": self.start_hour_var,
            "start_minute": self.start_minute_var,
            "end_hour": self.end_hour_var,
            "end_minute": self.end_minute_var,
            "active_days": self.week_vars,
            "boot_delay": self.boot_delay_var,
            "launch_wait": self.launch_wait_var,
            "retry_count": self.retry_count_var,
            "retry_interval": self.retry_interval_var,
            "button_wait": self.button_wait_var,
            "button1_text": self.button1_text_var,
            "button2_text": self.button2_text_var,
            "window_keyword": self.window_keyword_var,
            "show_progress": self.show_progress_var,
            "keep_window_topmost": self.keep_window_topmost_var,
        }

    def _make_tab(self, title):
        tab = ttk.Frame(self.notebook, padding=18)
        tab.columnconfigure(1, weight=1)
        self.notebook.add(tab, text=title)
        return tab

    @staticmethod
    def _entry_row(parent, row, label, variable, help_text=""):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=8)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=8)
        if help_text:
            ttk.Label(parent, text=help_text).grid(row=row, column=2, sticky="w", padx=(12, 0), pady=8)

    def _create_basic_tab(self, tab):
        self.path_var = tk.StringVar()
        self.window_keyword_var = tk.StringVar()
        self.button1_text_var = tk.StringVar()
        self.button2_text_var = tk.StringVar()
        ttk.Label(tab, text="按键精灵路径").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=8)
        ttk.Entry(tab, textvariable=self.path_var).grid(row=0, column=1, sticky="ew", pady=8)
        ttk.Button(tab, text="浏览…", command=self.browse_path).grid(row=0, column=2, padx=(12, 0), pady=8)
        self._entry_row(tab, 1, "窗口关键字", self.window_keyword_var, "用于匹配版本变化后的窗口")
        self._entry_row(tab, 2, "按钮一文本", self.button1_text_var, "例如：开始使用")
        self._entry_row(tab, 3, "按钮二文本", self.button2_text_var, "例如：启动")

    def _create_schedule_tab(self, tab):
        self.start_hour_var, self.start_minute_var = tk.StringVar(), tk.StringVar()
        self.end_hour_var, self.end_minute_var = tk.StringVar(), tk.StringVar()
        for row, label, hour_var, minute_var in (
            (0, "开始时间", self.start_hour_var, self.start_minute_var),
            (1, "结束时间", self.end_hour_var, self.end_minute_var),
        ):
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=8)
            frame = ttk.Frame(tab)
            frame.grid(row=row, column=1, sticky="w", pady=8)
            ttk.Spinbox(frame, from_=0, to=23, width=5, textvariable=hour_var).pack(side=tk.LEFT)
            ttk.Label(frame, text=" 时 ").pack(side=tk.LEFT)
            ttk.Spinbox(frame, from_=0, to=59, width=5, textvariable=minute_var).pack(side=tk.LEFT)
            ttk.Label(frame, text=" 分").pack(side=tk.LEFT)

        ttk.Label(tab, text="生效日期").grid(row=2, column=0, sticky="nw", padx=(0, 12), pady=8)
        days = ttk.Frame(tab)
        days.grid(row=2, column=1, columnspan=2, sticky="w", pady=8)
        self.week_vars = {}
        for index, name in enumerate(("周一", "周二", "周三", "周四", "周五", "周六", "周日")):
            variable = tk.BooleanVar()
            self.week_vars[index] = variable
            ttk.Checkbutton(days, text=name, variable=variable).grid(row=index // 4, column=index % 4, sticky="w", padx=(0, 12))
        shortcuts = ttk.Frame(tab)
        shortcuts.grid(row=3, column=1, columnspan=2, sticky="w", pady=8)
        for text, command in (("全选", self.select_all_days), ("工作日", self.select_weekdays),
                              ("周末", self.select_weekend), ("清空", self.clear_days)):
            ttk.Button(shortcuts, text=text, command=command).pack(side=tk.LEFT, padx=(0, 8))

    def _create_advanced_tab(self, tab):
        fields = (
            ("boot_delay", "开机延迟（秒）", 0, 300, "开机后等待再执行"),
            ("launch_wait", "启动等待（秒）", 0, 60, "等待按键精灵加载"),
            ("retry_count", "重试次数", 1, 20, "找不到窗口时重试"),
            ("retry_interval", "重试间隔（秒）", 1, 30, "每次重试间隔"),
            ("button_wait", "按钮等待（秒）", 1, 30, "两次按钮点击之间等待"),
        )
        for row, (name, label, minimum, maximum, help_text) in enumerate(fields):
            variable = tk.StringVar()
            setattr(self, f"{name}_var", variable)
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=8)
            ttk.Spinbox(tab, from_=minimum, to=maximum, width=10, textvariable=variable).grid(
                row=row, column=1, sticky="w", pady=8
            )
            ttk.Label(tab, text=help_text).grid(row=row, column=2, sticky="w", padx=(12, 0), pady=8)

    def _create_options_tab(self, tab):
        self.show_progress_var = tk.BooleanVar()
        self.keep_window_topmost_var = tk.BooleanVar()
        ttk.Checkbutton(tab, text="运行时显示进度窗口", variable=self.show_progress_var).grid(row=0, column=0, columnspan=3, sticky="w", pady=10)
        ttk.Checkbutton(tab, text="点击期间保持目标窗口置顶", variable=self.keep_window_topmost_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=10)

    def browse_path(self):
        filename = filedialog.askopenfilename(title="选择按键精灵程序", filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
        if filename:
            self.path_var.set(filename)

    def select_all_days(self):
        for variable in self.week_vars.values():
            variable.set(True)

    def select_weekdays(self):
        for index, variable in self.week_vars.items():
            variable.set(index < 5)

    def select_weekend(self):
        for index, variable in self.week_vars.items():
            variable.set(index >= 5)

    def clear_days(self):
        for variable in self.week_vars.values():
            variable.set(False)

    def load_values(self):
        for key in app_config.NUMBER_RULES:
            self.config_vars[key].set(str(self.config[key]))
        for key in ("anjian_path", "window_keyword", "button1_text", "button2_text"):
            self.config_vars[key].set(self.config[key])
        for key in ("show_progress", "keep_window_topmost"):
            self.config_vars[key].set(bool(self.config[key]))
        for index, variable in self.week_vars.items():
            variable.set(index in self.config["active_days"])

    def _raw_fields(self):
        return {key: self.config_vars[key].get() for key in app_config.NUMBER_RULES}

    def _collect_config(self, raw):
        result = {key: int(value.strip()) for key, value in raw.items()}
        result.update({
            "anjian_path": self.path_var.get().strip(),
            "window_keyword": self.window_keyword_var.get().strip(),
            "button1_text": self.button1_text_var.get().strip(),
            "button2_text": self.button2_text_var.get().strip(),
            "active_days": [index for index, variable in self.week_vars.items() if variable.get()],
            "show_progress": bool(self.show_progress_var.get()),
            "keep_window_topmost": bool(self.keep_window_topmost_var.get()),
        })
        return result

    def save_config_action(self):
        raw = self._raw_fields()
        raw_result = app_config.validate_raw_fields(raw)
        if not raw_result.ok:
            self._show_validation_errors(raw_result.errors)
            return False
        updates = self._collect_config(raw)
        result = app_config.validate_config(updates)
        if not result.ok:
            self._show_validation_errors(result.errors)
            return False
        if result.warnings and not messagebox.askyesno("配置警告", "\n".join(result.warnings) + "\n\n路径当前不存在，仍要保存吗？"):
            self.status_var.set("已取消保存")
            return False
        try:
            self.config = app_config.save_config(self.config_file, updates)
        except OSError as error:
            self.status_var.set("保存失败")
            messagebox.showerror("错误", f"保存配置失败：{error}")
            return False
        self.status_var.set("配置已保存")
        messagebox.showinfo("成功", "配置已保存成功！")
        return True

    def _show_validation_errors(self, errors):
        self.status_var.set("配置校验失败")
        messagebox.showerror("配置有误", "请修正以下问题：\n• " + "\n• ".join(errors))

    @staticmethod
    def _is_frozen():
        return bool(getattr(sys, "frozen", False))

    def _launch_info(self, action):
        return app_config.resolve_launch_command(action, self._is_frozen(), app_config.get_app_dir())

    def _check_launch_paths(self, info):
        if not os.path.isfile(info["target_path"]):
            if self._is_frozen():
                detail = "未找到 按键精灵自动启动.exe，请确认两个程序在同一文件夹"
            else:
                detail = f"未找到目标脚本：{info['target_path']}"
            self.status_var.set("启动目标不存在")
            messagebox.showerror("错误", detail)
            return False
        interpreter = info.get("interpreter_path")
        if interpreter and not os.path.isfile(interpreter):
            self.status_var.set("Python 解释器不存在")
            messagebox.showerror("错误", f"未找到 Python 解释器：{interpreter}")
            return False
        return True

    def test_script(self):
        if not os.path.isfile(self.config_file):
            messagebox.showerror("错误", "请先保存配置")
            return False
        info = self._launch_info("test")
        if not self._check_launch_paths(info):
            return False
        try:
            subprocess.Popen(info["args"], cwd=info["workdir"])
        except OSError as error:
            self.status_var.set("测试失败")
            messagebox.showerror("错误", f"启动测试失败：{error}")
            return False
        self.status_var.set("测试脚本已启动")
        messagebox.showinfo("测试", "测试脚本已启动，请查看日志文件了解执行情况")
        return True

    def setup_autostart(self):
        if not os.path.isfile(self.config_file):
            messagebox.showerror("错误", "请先保存配置")
            return False
        info = self._launch_info("autostart")
        if not self._check_launch_paths(info):
            return False
        if info["warnings"] and not messagebox.askyesno("启动方式警告", "\n".join(info["warnings"]) + "\n\n仍要继续吗？"):
            self.status_var.set("已取消设置开机自启")
            return False

        escape = lambda value: html.escape(value, quote=True)
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>按键精灵自动启动脚本</Description></RegistrationInfo>
  <Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>
  <Principals><Principal><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle><WakeToRun>false</WakeToRun><ExecutionTimeLimit>PT1H</ExecutionTimeLimit><Priority>7</Priority>
  </Settings>
  <Actions Context="Author"><Exec>
    <Command>{escape(info["command"])}</Command><Arguments>{escape(info["arguments"])}</Arguments>
    <WorkingDirectory>{escape(info["workdir"])}</WorkingDirectory>
  </Exec></Actions>
</Task>'''
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-16", suffix=".xml", delete=False) as temp_file:
                temp_file.write(task_xml)
                temp_path = temp_file.name
            result = subprocess.run(
                ["schtasks", "/Create", "/TN", "AnjianAutoStart", "/XML", temp_path, "/F"],
                capture_output=True, text=True, encoding="gbk", errors="replace"
            )
        except OSError as error:
            self.status_var.set("设置失败")
            messagebox.showerror("错误", f"设置开机自启失败：{error}")
            return False
        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
        if result.returncode != 0:
            self.status_var.set("设置失败")
            messagebox.showerror("错误", f"设置失败：{result.stderr}")
            return False
        self.status_var.set("开机自启已设置")
        messagebox.showinfo("成功", "开机自启设置成功！\n任务名称: AnjianAutoStart")
        return True

    def remove_autostart(self):
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", "AnjianAutoStart", "/F"],
                capture_output=True, text=True, encoding="gbk", errors="replace"
            )
        except OSError as error:
            self.status_var.set("取消失败")
            messagebox.showerror("错误", f"取消开机自启失败：{error}")
            return False
        if result.returncode == 0:
            self.status_var.set("已取消开机自启")
            messagebox.showinfo("成功", "已取消开机自启")
            return True
        if "找不到" in result.stderr or "cannot find" in result.stderr.lower():
            messagebox.showinfo("提示", "未找到开机自启任务")
        else:
            messagebox.showerror("错误", f"取消失败：{result.stderr}")
        self.status_var.set("取消失败或任务不存在")
        return False


def main():
    root = tk.Tk()
    ConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
