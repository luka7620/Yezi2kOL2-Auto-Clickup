"""
按键精灵自动启动脚本 - 配置界面
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
from datetime import datetime


class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("按键精灵自动启动配置")
        self.root.geometry("700x800")
        self.root.resizable(False, False)
        
        self.config_file = "config.json"
        self.config = self.load_config()
        
        self.create_widgets()
        self.load_values()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="按键精灵自动启动配置", 
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        row = 1
        
        # ========== 基础设置 ==========
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(main_frame, text="基础设置", font=("Microsoft YaHei", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        # 按键精灵路径
        ttk.Label(main_frame, text="按键精灵路径:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(main_frame, textvariable=self.path_var, width=50)
        path_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_path).grid(row=row, column=2, padx=5)
        row += 1
        
        # ========== 时间设置 ==========
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(main_frame, text="时间段设置", font=("Microsoft YaHei", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        # 开始时间
        ttk.Label(main_frame, text="开始时间:").grid(row=row, column=0, sticky=tk.W, pady=5)
        time_frame1 = ttk.Frame(main_frame)
        time_frame1.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.start_hour_var = tk.StringVar()
        self.start_minute_var = tk.StringVar()
        ttk.Spinbox(time_frame1, from_=0, to=23, textvariable=self.start_hour_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame1, text="时").pack(side=tk.LEFT, padx=2)
        ttk.Spinbox(time_frame1, from_=0, to=59, textvariable=self.start_minute_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame1, text="分").pack(side=tk.LEFT, padx=2)
        row += 1
        
        # 结束时间
        ttk.Label(main_frame, text="结束时间:").grid(row=row, column=0, sticky=tk.W, pady=5)
        time_frame2 = ttk.Frame(main_frame)
        time_frame2.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.end_hour_var = tk.StringVar()
        self.end_minute_var = tk.StringVar()
        ttk.Spinbox(time_frame2, from_=0, to=23, textvariable=self.end_hour_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame2, text="时").pack(side=tk.LEFT, padx=2)
        ttk.Spinbox(time_frame2, from_=0, to=59, textvariable=self.end_minute_var, width=5).pack(side=tk.LEFT)
        ttk.Label(time_frame2, text="分").pack(side=tk.LEFT, padx=2)
        row += 1
        
        # 星期选择
        ttk.Label(main_frame, text="生效日期:").grid(row=row, column=0, sticky=tk.W, pady=5)
        week_frame = ttk.Frame(main_frame)
        week_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.week_vars = {}
        week_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, name in enumerate(week_names):
            var = tk.BooleanVar()
            self.week_vars[i] = var
            ttk.Checkbutton(week_frame, text=name, variable=var).grid(row=0, column=i, padx=2)
        row += 1
        
        # 快捷选择
        quick_select_frame = ttk.Frame(main_frame)
        quick_select_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Button(quick_select_frame, text="全选", command=self.select_all_days).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_select_frame, text="工作日", command=self.select_weekdays).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_select_frame, text="周末", command=self.select_weekend).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_select_frame, text="清空", command=self.clear_days).pack(side=tk.LEFT, padx=2)
        row += 1
        
        # ========== 执行参数 ==========
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(main_frame, text="执行参数", font=("Microsoft YaHei", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        # 开机延迟
        ttk.Label(main_frame, text="开机延迟(秒):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.boot_delay_var = tk.StringVar()
        ttk.Spinbox(main_frame, from_=0, to=300, textvariable=self.boot_delay_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="开机后等待多久执行").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # 启动等待时间
        ttk.Label(main_frame, text="启动等待(秒):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.launch_wait_var = tk.StringVar()
        ttk.Spinbox(main_frame, from_=0, to=60, textvariable=self.launch_wait_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="启动按键精灵后等待时间").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # 重试次数
        ttk.Label(main_frame, text="重试次数:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.retry_count_var = tk.StringVar()
        ttk.Spinbox(main_frame, from_=1, to=20, textvariable=self.retry_count_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="找不到窗口时重试次数").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # 重试间隔
        ttk.Label(main_frame, text="重试间隔(秒):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.retry_interval_var = tk.StringVar()
        ttk.Spinbox(main_frame, from_=1, to=30, textvariable=self.retry_interval_var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text="每次重试间隔时间").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # ========== 按钮文本设置 ==========
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(main_frame, text="按钮文本设置", font=("Microsoft YaHei", 12, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        row += 1
        
        # 第一个按钮文本
        ttk.Label(main_frame, text="第一个按钮:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.button1_text_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.button1_text_var, width=30).grid(
            row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text='如"开始使用"').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # 第二个按钮文本
        ttk.Label(main_frame, text="第二个按钮:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.button2_text_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.button2_text_var, width=30).grid(
            row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text='如"启动"').grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # ========== 操作按钮 ==========
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='ew', pady=10)
        row += 1
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config_action, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="测试运行", command=self.test_script, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="设置开机自启", command=self.setup_autostart, 
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消开机自启", command=self.remove_autostart, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
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
            
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "anjian_path": "",
            "start_hour": 8,
            "start_minute": 0,
            "end_hour": 22,
            "end_minute": 0,
            "active_days": [0, 1, 2, 3, 4, 5, 6],
            "boot_delay": 15,
            "launch_wait": 8,
            "retry_count": 5,
            "retry_interval": 3,
            "button1_text": "开始使用",
            "button2_text": "启动"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有字段都存在
                    default_config.update(config)
                    return default_config
            except Exception as e:
                messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
                return default_config
        return default_config
        
    def load_values(self):
        """将配置加载到界面"""
        self.path_var.set(self.config.get("anjian_path", ""))
        self.start_hour_var.set(str(self.config.get("start_hour", 8)))
        self.start_minute_var.set(str(self.config.get("start_minute", 0)))
        self.end_hour_var.set(str(self.config.get("end_hour", 22)))
        self.end_minute_var.set(str(self.config.get("end_minute", 0)))
        
        active_days = self.config.get("active_days", [0, 1, 2, 3, 4, 5, 6])
        for i in range(7):
            self.week_vars[i].set(i in active_days)
            
        self.boot_delay_var.set(str(self.config.get("boot_delay", 15)))
        self.launch_wait_var.set(str(self.config.get("launch_wait", 8)))
        self.retry_count_var.set(str(self.config.get("retry_count", 5)))
        self.retry_interval_var.set(str(self.config.get("retry_interval", 3)))
        self.button1_text_var.set(self.config.get("button1_text", "开始使用"))
        self.button2_text_var.set(self.config.get("button2_text", "启动"))
        
    def save_config_action(self):
        """保存配置"""
        try:
            # 验证输入
            if not self.path_var.get():
                messagebox.showerror("错误", "请选择按键精灵程序路径")
                return
                
            if not os.path.exists(self.path_var.get()):
                messagebox.showerror("错误", "按键精灵程序路径不存在")
                return
            
            active_days = [i for i in range(7) if self.week_vars[i].get()]
            if not active_days:
                messagebox.showerror("错误", "请至少选择一个生效日期")
                return
            
            # 保存配置
            config = {
                "anjian_path": self.path_var.get(),
                "start_hour": int(self.start_hour_var.get()),
                "start_minute": int(self.start_minute_var.get()),
                "end_hour": int(self.end_hour_var.get()),
                "end_minute": int(self.end_minute_var.get()),
                "active_days": active_days,
                "boot_delay": int(self.boot_delay_var.get()),
                "launch_wait": int(self.launch_wait_var.get()),
                "retry_count": int(self.retry_count_var.get()),
                "retry_interval": int(self.retry_interval_var.get()),
                "button1_text": self.button1_text_var.get(),
                "button2_text": self.button2_text_var.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            self.config = config
            self.status_var.set("配置已保存")
            messagebox.showinfo("成功", "配置已保存成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
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

