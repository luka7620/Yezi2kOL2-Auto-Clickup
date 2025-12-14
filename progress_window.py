"""
进度显示窗口 - 实时显示脚本执行状态
"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import time
import logging


class ProgressWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("按键精灵启动助手")
        self.root.geometry("600x400")
        
        # 设置窗口置顶
        self.root.attributes('-topmost', True)
        
        # 居中显示
        self.center_window()
        
        # 创建界面
        self.create_widgets()
        
        # 消息队列
        self.message_queue = queue.Queue()
        
        # 是否应该关闭
        self.should_close = False
        self.auto_close_time = None
        
        # 开始更新消息
        self.update_messages()
        
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """创建界面元素"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#2C3E50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="按键精灵自动启动",
            font=("Microsoft YaHei", 16, "bold"),
            bg='#2C3E50',
            fg='white'
        )
        title_label.pack(expand=True)
        
        # 状态标签
        self.status_label = tk.Label(
            self.root,
            text="正在初始化...",
            font=("Microsoft YaHei", 11),
            fg='#3498DB',
            pady=10
        )
        self.status_label.pack()
        
        # 日志文本框
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg='#F8F9FA',
            fg='#2C3E50',
            relief=tk.FLAT,
            borderwidth=1
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 进度条（使用标签模拟）
        self.progress_frame = tk.Frame(self.root, bg='#ECF0F1', height=30)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        self.progress_frame.pack_propagate(False)
        
        self.progress_bar = tk.Frame(self.progress_frame, bg='#3498DB', width=0)
        self.progress_bar.place(x=0, y=0, relheight=1)
        
        self.progress_text = tk.Label(
            self.progress_frame,
            text="0%",
            font=("Microsoft YaHei", 9),
            bg='#ECF0F1',
            fg='#2C3E50'
        )
        self.progress_text.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # 底部按钮框
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.close_button = tk.Button(
            button_frame,
            text="手动关闭",
            command=self.close_window,
            font=("Microsoft YaHei", 10),
            bg='#E74C3C',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor='hand2'
        )
        self.close_button.pack(side=tk.RIGHT)
        
        # 倒计时标签
        self.countdown_label = tk.Label(
            button_frame,
            text="",
            font=("Microsoft YaHei", 9),
            fg='#7F8C8D'
        )
        self.countdown_label.pack(side=tk.LEFT)
        
    def add_log(self, message, level='INFO'):
        """添加日志消息"""
        self.message_queue.put(('log', message, level))
        
    def update_status(self, status, color='#3498DB'):
        """更新状态文本"""
        self.message_queue.put(('status', status, color))
        
    def update_progress(self, percent):
        """更新进度条"""
        self.message_queue.put(('progress', percent))
        
    def set_auto_close(self, seconds):
        """设置自动关闭时间"""
        self.auto_close_time = time.time() + seconds
        
    def update_messages(self):
        """更新界面（从队列中获取消息）"""
        try:
            while not self.message_queue.empty():
                msg_type, *args = self.message_queue.get_nowait()
                
                if msg_type == 'log':
                    message, level = args
                    self.log_text.config(state=tk.NORMAL)
                    
                    # 根据级别设置颜色
                    if level == 'ERROR':
                        tag = 'error'
                        self.log_text.tag_config('error', foreground='#E74C3C')
                    elif level == 'WARNING':
                        tag = 'warning'
                        self.log_text.tag_config('warning', foreground='#F39C12')
                    elif level == 'SUCCESS':
                        tag = 'success'
                        self.log_text.tag_config('success', foreground='#27AE60')
                    else:
                        tag = 'info'
                        self.log_text.tag_config('info', foreground='#2C3E50')
                    
                    timestamp = time.strftime('%H:%M:%S')
                    self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
                    
                elif msg_type == 'status':
                    status, color = args
                    self.status_label.config(text=status, fg=color)
                    
                elif msg_type == 'progress':
                    percent = args[0]
                    width = int(self.progress_frame.winfo_width() * percent / 100)
                    self.progress_bar.config(width=width)
                    self.progress_text.config(text=f"{int(percent)}%")
                    
        except queue.Empty:
            pass
        
        # 检查自动关闭
        if self.auto_close_time and time.time() >= self.auto_close_time:
            self.close_window()
            return
            
        # 更新倒计时
        if self.auto_close_time:
            remaining = int(self.auto_close_time - time.time())
            if remaining > 0:
                self.countdown_label.config(text=f"将在 {remaining} 秒后自动关闭")
            
        # 继续更新
        if not self.should_close:
            self.root.after(100, self.update_messages)
            
    def close_window(self):
        """关闭窗口"""
        self.should_close = True
        self.root.quit()
        
    def run(self):
        """运行窗口（阻塞）"""
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.root.mainloop()
        try:
            self.root.destroy()
        except:
            pass


class ProgressWindowHandler(logging.Handler):
    """
    自定义日志处理器 - 将日志输出到进度窗口
    """
    def __init__(self, window):
        super().__init__()
        self.window = window
        
    def emit(self, record):
        try:
            msg = self.format(record)
            # 只显示消息部分，不显示时间和级别（已经在日志中显示）
            message = record.getMessage()
            
            # 根据日志级别设置颜色
            if record.levelno >= logging.ERROR:
                level = 'ERROR'
            elif record.levelno >= logging.WARNING:
                level = 'WARNING'
            else:
                level = 'INFO'
                
            self.window.add_log(message, level)
        except Exception:
            self.handleError(record)


# 测试代码
if __name__ == "__main__":
    import threading
    
    # 创建窗口
    window = ProgressWindow()
    
    # 在另一个线程中模拟任务
    def test_task():
        time.sleep(1)
        window.update_status("正在检查配置...")
        window.update_progress(10)
        window.add_log("配置文件加载成功", 'INFO')
        
        time.sleep(1)
        window.update_status("正在检查时间段...")
        window.update_progress(20)
        window.add_log("当前时间在允许范围内", 'INFO')
        
        time.sleep(1)
        window.update_status("正在启动按键精灵...")
        window.update_progress(40)
        window.add_log("按键精灵启动中...", 'INFO')
        
        time.sleep(2)
        window.update_status("正在查找窗口...")
        window.update_progress(60)
        window.add_log("找到按键精灵窗口", 'SUCCESS')
        
        time.sleep(1)
        window.update_status("正在点击按钮...")
        window.update_progress(80)
        window.add_log("成功点击'开始使用'按钮", 'SUCCESS')
        
        time.sleep(1)
        window.add_log("成功点击'启动'按钮", 'SUCCESS')
        window.update_progress(100)
        
        time.sleep(0.5)
        window.update_status("任务完成！", '#27AE60')
        window.add_log("所有操作已完成，程序即将退出", 'SUCCESS')
        
        # 设置3秒后自动关闭
        window.set_auto_close(3)
    
    # 启动测试线程
    thread = threading.Thread(target=test_task, daemon=True)
    thread.start()
    
    # 运行窗口
    window.run()

