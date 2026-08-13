"""
按键精灵自动启动脚本 - 配置界面
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
from datetime import datetime

import config_manager


class ConfigGUI:
    def __init__(self, root, config_file="config.json"):
        self.root = root
        self.root.title("按键精灵自动启动配置")
        self.root.geometry("640x560")
        self.root.minsize(600, 520)
        self.root.resizable(True, True)

        self.config_file = config_file
        self.load_recovery_error = None
        try:
            self.config = config_manager.load_config(self.config_file)
        except config_manager.ConfigLoadError as error:
            self.load_recovery_error = str(error)
            messagebox.showerror("错误", f"加载配置文件失败: {error}")
            self.config = config_manager.default_config()

        self.create_widgets()
        self.load_values()

    def create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame = ttk.Frame(self.root, padding=(16, 12, 16, 10))
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        ttk.Label(
            main_frame,
            text="按键精灵自动启动配置",
            font=("Microsoft YaHei", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            main_frame,
            text="设置目标程序、运行时间和自动点击行为",
            foreground="#666666",
        ).grid(row=1, column=0, sticky="w", pady=(2, 10))

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, sticky="nsew")
        self.tab_basic = ttk.Frame(self.notebook, padding=12)
        self.tab_schedule = ttk.Frame(self.notebook, padding=12)
        self.tab_advanced = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.tab_basic, text="基础设置")
        self.notebook.add(self.tab_schedule, text="运行时间")
        self.notebook.add(self.tab_advanced, text="高级设置")
        for tab in (self.tab_basic, self.tab_schedule, self.tab_advanced):
            tab.columnconfigure(0, weight=1)

        self._create_basic_tab()
        self._create_schedule_tab()
        self._create_advanced_tab()
        self._create_actions(main_frame)

    @staticmethod
    def _configure_group(group):
        group.columnconfigure(1, weight=1)

    @staticmethod
    def _help_label(parent, text, row):
        ttk.Label(parent, text=text, foreground="#777777").grid(
            row=row, column=1, columnspan=2, sticky="w", pady=(0, 8)
        )

    def _create_basic_tab(self):
        path_group = ttk.LabelFrame(self.tab_basic, text="程序路径", padding=12)
        path_group.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._configure_group(path_group)
        self.path_var = tk.StringVar()
        ttk.Label(path_group, text="按键精灵路径:").grid(row=0, column=0, sticky="e", padx=(0, 10))
        self.path_entry = ttk.Entry(path_group, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(path_group, text="浏览", command=self.browse_path).grid(row=0, column=2, padx=(8, 0))
        self._help_label(path_group, "选择需要自动启动的按键精灵 exe 文件", 1)

        target_group = ttk.LabelFrame(self.tab_basic, text="目标窗口与按钮", padding=12)
        target_group.grid(row=1, column=0, sticky="ew")
        self._configure_group(target_group)
        self.window_keyword_var = tk.StringVar()
        self.button1_text_var = tk.StringVar()
        self.button2_text_var = tk.StringVar()
        self.button_wait_var = tk.StringVar()

        ttk.Label(target_group, text="窗口关键词:").grid(row=0, column=0, sticky="e", padx=(0, 10))
        self.window_keyword_entry = ttk.Entry(target_group, textvariable=self.window_keyword_var)
        self.window_keyword_entry.grid(row=0, column=1, sticky="ew")
        self._help_label(target_group, "要点击的目标窗口标题关键字（必填），如 YZ2K2", 1)
        ttk.Label(target_group, text="第一个按钮:").grid(row=2, column=0, sticky="e", padx=(0, 10))
        self.button1_entry = ttk.Entry(target_group, textvariable=self.button1_text_var)
        self.button1_entry.grid(row=2, column=1, sticky="ew")
        self._help_label(target_group, '按钮文本，如“开始使用”', 3)
        ttk.Label(target_group, text="第二个按钮:").grid(row=4, column=0, sticky="e", padx=(0, 10))
        self.button2_entry = ttk.Entry(target_group, textvariable=self.button2_text_var)
        self.button2_entry.grid(row=4, column=1, sticky="ew")
        self._help_label(target_group, '按钮文本，如“启动”', 5)
        ttk.Label(target_group, text="按钮等待(秒):").grid(row=6, column=0, sticky="e", padx=(0, 10))
        self.button_wait_spinbox = ttk.Spinbox(
            target_group, from_=0, to=60, textvariable=self.button_wait_var, width=10
        )
        self.button_wait_spinbox.grid(row=6, column=1, sticky="w")
        self._help_label(target_group, "点击第一个按钮后等待秒数", 7)

    def _create_schedule_tab(self):
        time_group = ttk.LabelFrame(self.tab_schedule, text="生效时间段", padding=12)
        time_group.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._configure_group(time_group)
        self.start_hour_var = tk.StringVar()
        self.start_minute_var = tk.StringVar()
        self.end_hour_var = tk.StringVar()
        self.end_minute_var = tk.StringVar()
        self._create_time_row(time_group, 0, "开始时间:", self.start_hour_var, self.start_minute_var)
        self._create_time_row(time_group, 1, "结束时间:", self.end_hour_var, self.end_minute_var)
        self._help_label(time_group, "仅在所选时间段内执行自动启动", 2)

        day_group = ttk.LabelFrame(self.tab_schedule, text="生效日期", padding=12)
        day_group.grid(row=1, column=0, sticky="ew")
        self.week_vars = {}
        week_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, name in enumerate(week_names):
            var = tk.BooleanVar()
            self.week_vars[i] = var
            ttk.Checkbutton(day_group, text=name, variable=var).grid(row=0, column=i, padx=3, pady=(0, 10))
        quick_select_frame = ttk.Frame(day_group)
        quick_select_frame.grid(row=1, column=0, columnspan=7, sticky="w")
        ttk.Button(quick_select_frame, text="全选", command=self.select_all_days).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_select_frame, text="工作日", command=self.select_weekdays).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_select_frame, text="周末", command=self.select_weekend).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_select_frame, text="清空", command=self.clear_days).pack(side=tk.LEFT, padx=2)

    @staticmethod
    def _create_time_row(parent, row, label, hour_var, minute_var):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=(0, 10), pady=5)
        time_frame = ttk.Frame(parent)
        time_frame.grid(row=row, column=1, sticky="w", pady=5)
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=hour_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="时").pack(side=tk.LEFT, padx=(3, 8))
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=minute_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame, text="分").pack(side=tk.LEFT, padx=3)

    def _create_advanced_tab(self):
        retry_group = ttk.LabelFrame(self.tab_advanced, text="启动与重试", padding=12)
        retry_group.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._configure_group(retry_group)
        self.boot_delay_var = tk.StringVar()
        self.launch_wait_var = tk.StringVar()
        self.retry_count_var = tk.StringVar()
        self.retry_interval_var = tk.StringVar()
        fields = (
            ("开机延迟(秒):", self.boot_delay_var, 0, 300, "开机后等待多久执行"),
            ("启动等待(秒):", self.launch_wait_var, 0, 60, "启动按键精灵后等待时间"),
            ("重试次数:", self.retry_count_var, 1, 20, "找不到窗口时重试次数"),
            ("重试间隔(秒):", self.retry_interval_var, 1, 30, "每次重试间隔时间"),
        )
        for index, (label, variable, minimum, maximum, help_text) in enumerate(fields):
            row = index * 2
            ttk.Label(retry_group, text=label).grid(row=row, column=0, sticky="e", padx=(0, 10))
            ttk.Spinbox(
                retry_group, from_=minimum, to=maximum, textvariable=variable, width=10
            ).grid(row=row, column=1, sticky="w")
            self._help_label(retry_group, help_text, row + 1)

        behavior_group = ttk.LabelFrame(self.tab_advanced, text="界面行为", padding=12)
        behavior_group.grid(row=1, column=0, sticky="ew")
        self.show_progress_var = tk.BooleanVar()
        self.keep_topmost_var = tk.BooleanVar()
        self.show_progress_checkbutton = ttk.Checkbutton(
            behavior_group, text="运行时显示进度窗口", variable=self.show_progress_var
        )
        self.show_progress_checkbutton.grid(row=0, column=0, sticky="w", pady=4)
        self.keep_topmost_checkbutton = ttk.Checkbutton(
            behavior_group, text="保持目标窗口置顶", variable=self.keep_topmost_var
        )
        self.keep_topmost_checkbutton.grid(row=1, column=0, sticky="w", pady=4)

    def _create_actions(self, main_frame):
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky="ew", pady=(12, 8))
        ttk.Button(button_frame, text="保存配置", command=self.save_config_action).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_frame, text="测试运行", command=self.test_script).pack(side=tk.LEFT, padx=6)
        ttk.Button(button_frame, text="设置开机自启", command=self.setup_autostart).pack(side=tk.LEFT, padx=6)
        ttk.Button(button_frame, text="取消开机自启", command=self.remove_autostart).pack(side=tk.LEFT, padx=6)
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).grid(
            row=4, column=0, sticky="ew"
        )

    def browse_path(self):
        filename = filedialog.askopenfilename(
            title="选择按键精灵程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if filename:
            self.path_var.set(filename)
            
    def select_all_days(self):
        for var in self.week_vars.values():
            var.set(True)
            
    def select_weekdays(self):
        for i in range(5):
            self.week_vars[i].set(True)
        for i in range(5, 7):
            self.week_vars[i].set(False)
            
    def select_weekend(self):
        for i in range(5):
            self.week_vars[i].set(False)
        for i in range(5, 7):
            self.week_vars[i].set(True)
            
    def clear_days(self):
        for var in self.week_vars.values():
            var.set(False)
            
    def load_values(self):
        """将配置加载到界面"""
        self.path_var.set(self.config["anjian_path"])
        self.window_keyword_var.set(self.config["window_keyword"])
        self.start_hour_var.set(str(self.config["start_hour"]))
        self.start_minute_var.set(str(self.config["start_minute"]))
        self.end_hour_var.set(str(self.config["end_hour"]))
        self.end_minute_var.set(str(self.config["end_minute"]))
        active_days = self.config["active_days"]
        for i in range(7):
            self.week_vars[i].set(i in active_days)
        self.boot_delay_var.set(str(self.config["boot_delay"]))
        self.launch_wait_var.set(str(self.config["launch_wait"]))
        self.retry_count_var.set(str(self.config["retry_count"]))
        self.retry_interval_var.set(str(self.config["retry_interval"]))
        self.button_wait_var.set(str(self.config["button_wait"]))
        self.button1_text_var.set(self.config["button1_text"])
        self.button2_text_var.set(self.config["button2_text"])
        self.show_progress_var.set(self.config["show_progress"])
        self.keep_topmost_var.set(self.config["keep_window_topmost"])

    @staticmethod
    def _parse_int(raw, label, errors):
        try:
            return int(raw.strip())
        except ValueError:
            errors.append(f"{label}必须是整数")
            default_keys = {
                "开始时间（时）": "start_hour",
                "开始时间（分）": "start_minute",
                "结束时间（时）": "end_hour",
                "结束时间（分）": "end_minute",
                "开机延迟(秒)": "boot_delay",
                "启动等待(秒)": "launch_wait",
                "重试次数": "retry_count",
                "重试间隔(秒)": "retry_interval",
                "按钮等待(秒)": "button_wait",
            }
            return config_manager.DEFAULT_CONFIG[default_keys[label]]

    def collect_form_config(self):
        errors = []
        number_fields = (
            ("start_hour", self.start_hour_var, "开始时间（时）"),
            ("start_minute", self.start_minute_var, "开始时间（分）"),
            ("end_hour", self.end_hour_var, "结束时间（时）"),
            ("end_minute", self.end_minute_var, "结束时间（分）"),
            ("boot_delay", self.boot_delay_var, "开机延迟(秒)"),
            ("launch_wait", self.launch_wait_var, "启动等待(秒)"),
            ("retry_count", self.retry_count_var, "重试次数"),
            ("retry_interval", self.retry_interval_var, "重试间隔(秒)"),
            ("button_wait", self.button_wait_var, "按钮等待(秒)"),
        )
        config = {
            "anjian_path": self.path_var.get(),
            "window_keyword": self.window_keyword_var.get().strip(),
            "active_days": [i for i in range(7) if self.week_vars[i].get()],
            "button1_text": self.button1_text_var.get().strip(),
            "button2_text": self.button2_text_var.get().strip(),
            "show_progress": bool(self.show_progress_var.get()),
            "keep_window_topmost": bool(self.keep_topmost_var.get()),
        }
        for key, variable, label in number_fields:
            config[key] = self._parse_int(variable.get(), label, errors)
        return config, errors

    def save_config_action(self):
        """保存配置"""
        config, errors = self.collect_form_config()
        errors.extend(config_manager.validate_config(config))
        if config["anjian_path"] and not os.path.exists(config["anjian_path"]):
            errors.append("按键精灵程序路径不存在")
        if errors:
            messagebox.showerror("错误", "\n".join(errors))
            return

        if self.load_recovery_error is not None:
            confirmed = messagebox.askyesno(
                "确认覆盖配置",
                "原配置文件无法恢复读取：\n"
                f"{self.load_recovery_error}\n\n"
                "继续保存会用当前表单覆盖原配置文件，是否确认继续？",
            )
            if not confirmed:
                return

        try:
            config_manager.save_config(config, self.config_file)
            self.config = config
            self.load_recovery_error = None
            self.status_var.set(f"配置已保存 {datetime.now():%H:%M:%S}")
            messagebox.showinfo("成功", "配置已保存成功！")
        except OSError as error:
            messagebox.showerror("错误", f"保存配置失败: {error}")

    def test_script(self):
        """测试运行脚本"""
        if not os.path.exists(self.config_file):
            messagebox.showerror("错误", "请先保存配置")
            return
            
        if not os.path.exists("auto_clicker.py"):
            messagebox.showerror("错误", "找不到 auto_clicker.py 文件")
            return
            
        try:
            self.status_var.set("正在测试运行...")
            # 使用 pythonw 运行，避免弹出命令行窗口
            subprocess.Popen(["python", "auto_clicker.py", "--test"])
            messagebox.showinfo("测试", "测试脚本已启动，请查看日志文件了解执行情况")
            self.status_var.set("测试脚本已启动")
        except Exception as e:
            messagebox.showerror("错误", f"启动测试失败: {str(e)}")
            self.status_var.set("测试失败")
            
    def setup_autostart(self):
        """设置开机自启"""
        if not os.path.exists(self.config_file):
            messagebox.showerror("错误", "请先保存配置")
            return
            
        if not os.path.exists("auto_clicker.py"):
            messagebox.showerror("错误", "找不到 auto_clicker.py 文件")
            return
            
        try:
            script_path = os.path.abspath("auto_clicker.py")
            python_path = "pythonw"  # 使用 pythonw 避免弹出命令行窗口
            
            # 创建任务计划程序的 XML
            task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>按键精灵自动启动脚本</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{os.path.dirname(script_path)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
            
            # 保存临时 XML 文件
            temp_xml = "temp_task.xml"
            with open(temp_xml, 'w', encoding='utf-16') as f:
                f.write(task_xml)
            
            # 使用 schtasks 创建任务
            cmd = f'schtasks /Create /TN "AnjianAutoStart" /XML "{temp_xml}" /F'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
            
            # 删除临时文件
            if os.path.exists(temp_xml):
                os.remove(temp_xml)
            
            if result.returncode == 0:
                messagebox.showinfo("成功", "开机自启设置成功！\n任务名称: AnjianAutoStart")
                self.status_var.set("开机自启已设置")
            else:
                messagebox.showerror("错误", f"设置失败: {result.stderr}")
                self.status_var.set("设置失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"设置开机自启失败: {str(e)}")
            self.status_var.set("设置失败")
            
    def remove_autostart(self):
        """取消开机自启"""
        try:
            cmd = 'schtasks /Delete /TN "AnjianAutoStart" /F'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
            
            if result.returncode == 0:
                messagebox.showinfo("成功", "已取消开机自启")
                self.status_var.set("已取消开机自启")
            else:
                if "找不到" in result.stderr or "cannot find" in result.stderr.lower():
                    messagebox.showinfo("提示", "未找到开机自启任务")
                else:
                    messagebox.showerror("错误", f"取消失败: {result.stderr}")
                self.status_var.set("取消失败或任务不存在")
                
        except Exception as e:
            messagebox.showerror("错误", f"取消开机自启失败: {str(e)}")
            self.status_var.set("取消失败")


def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
