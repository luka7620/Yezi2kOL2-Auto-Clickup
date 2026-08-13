"""
按键精灵自动启动脚本
开机自动运行，完成任务后自动退出
"""
import os
import sys
import time
import logging
from datetime import datetime
import subprocess
import psutil
import win32gui
import win32con
import win32process
import win32api
import app_config


class AnjianAutoClicker:
    def __init__(self, test_mode=False, progress_window=None):
        self.test_mode = test_mode
        self.progress_window = progress_window
        self.config_file = app_config.get_config_path()
        self.log_dir = "logs"
        self.config = None
        
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # 配置日志
        self.setup_logging()
        
    def setup_logging(self):
        """配置日志系统"""
        log_file = os.path.join(self.log_dir, f"auto_clicker_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 创建logger
        self.logger = logging.getLogger(__name__ + str(id(self)))
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)
        
        # 如果有进度窗口，添加自定义处理器
        if self.progress_window:
            from progress_window import ProgressWindowHandler
            window_handler = ProgressWindowHandler(self.progress_window)
            window_handler.setLevel(logging.INFO)
            self.logger.addHandler(window_handler)
        
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            self.logger.error(f"配置文件不存在: {self.config_file}")
            return False
        try:
            self.config = app_config.load_config(self.config_file)
        except app_config.ConfigLoadError as error:
            self.logger.error(f"加载配置文件失败: {str(error)}")
            return False
        self.logger.info("配置文件加载成功")
        return True

    def check_time_range(self):
        """检查当前时间是否在允许的时间段内"""
        now = datetime.now()
        current_time = now.hour * 60 + now.minute
        current_weekday = now.weekday()  # 0=周一, 6=周日
        
        start_time = self.config['start_hour'] * 60 + self.config['start_minute']
        end_time = self.config['end_hour'] * 60 + self.config['end_minute']
        
        # 检查星期几
        if current_weekday not in self.config['active_days']:
            self.logger.info(f"今天是{['周一','周二','周三','周四','周五','周六','周日'][current_weekday]}，不在生效日期内")
            return False
            
        # 检查时间段
        if start_time <= current_time <= end_time:
            self.logger.info(f"当前时间 {now.strftime('%H:%M')} 在允许时间段内")
            return True
        else:
            self.logger.info(f"当前时间 {now.strftime('%H:%M')} 不在允许时间段 "
                           f"{self.config['start_hour']:02d}:{self.config['start_minute']:02d} - "
                           f"{self.config['end_hour']:02d}:{self.config['end_minute']:02d} 内")
            return False
            
    def is_anjian_running(self):
        """检查按键精灵是否已经在运行"""
        try:
            anjian_name = os.path.basename(self.config['anjian_path']).lower()
            
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == anjian_name:
                        self.logger.info(f"检测到按键精灵已经在运行 (PID: {proc.pid})")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"检查进程时出错: {str(e)}")
            return False
            
    def launch_anjian(self):
        """启动按键精灵程序"""
        try:
            anjian_path = self.config['anjian_path']
            
            if not os.path.exists(anjian_path):
                self.logger.error(f"按键精灵程序不存在: {anjian_path}")
                return False
                
            self.logger.info(f"正在启动按键精灵: {anjian_path}")
            subprocess.Popen(anjian_path)
            
            # 等待程序启动
            wait_time = self.config['launch_wait']
            self.logger.info(f"等待 {wait_time} 秒让程序完全加载...")
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动按键精灵失败: {str(e)}")
            return False
            
    def find_window(self, class_name=None, window_name=None):
        """查找窗口句柄"""
        try:
            hwnd = win32gui.FindWindow(class_name, window_name)
            if hwnd:
                self.logger.info(f"找到窗口: {win32gui.GetWindowText(hwnd)} (句柄: {hwnd})")
                return hwnd
            return None
        except Exception as e:
            self.logger.error(f"查找窗口失败: {str(e)}")
            return None
            
    def enum_child_windows(self, parent_hwnd):
        """枚举所有子窗口"""
        child_windows = []
        
        def callback(hwnd, windows):
            windows.append(hwnd)
            return True
            
        win32gui.EnumChildWindows(parent_hwnd, callback, child_windows)
        return child_windows
        
    def find_button_by_text(self, parent_hwnd, button_text, log_all=False, include_hidden=True):
        """根据文本查找按钮"""
        try:
            child_windows = self.enum_child_windows(parent_hwnd)
            
            if log_all:
                self.logger.info(f"开始枚举窗口的所有子控件，共 {len(child_windows)} 个...")
            
            # 收集所有匹配的控件，然后优先选择最佳匹配
            candidates = []
            
            for child_hwnd in child_windows:
                try:
                    # 获取窗口文本
                    text = win32gui.GetWindowText(child_hwnd)
                    class_name = win32gui.GetClassName(child_hwnd)
                    is_visible = win32gui.IsWindowVisible(child_hwnd)
                    
                    # 记录所有有文本的控件（调试用）
                    if log_all and text:
                        visible_status = "可见" if is_visible else "隐藏"
                        self.logger.info(f"  控件: '{text}' (类名: {class_name}, 状态: {visible_status})")
                    
                    # 检查是否文本匹配（不区分大小写）
                    if text and button_text.lower() in text.lower():
                        # 如果设置了include_hidden=False，则跳过隐藏的按钮
                        if not include_hidden and not is_visible:
                            continue
                        
                        # 计算匹配度分数
                        score = 0
                        # 精确匹配得最高分
                        if text.lower() == button_text.lower():
                            score += 100
                        # Button 类得高分
                        if "button" in class_name.lower():
                            score += 50
                        # 可见控件得分
                        if is_visible:
                            score += 10
                        # 文本越短越好（避免匹配到包含关键词的长文本）
                        score += max(0, 50 - len(text))
                        
                        candidates.append((score, child_hwnd, text, class_name, is_visible))
                        
                except Exception:
                    continue
            
            # 如果找到候选项，选择得分最高的
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_match = candidates[0]
                score, child_hwnd, text, class_name, is_visible = best_match
                visible_status = "可见" if is_visible else "隐藏"
                self.logger.info(f"[OK] 找到最佳匹配按钮: '{text}' (句柄: {child_hwnd}, 类名: {class_name}, 状态: {visible_status}, 得分: {score})")
                return child_hwnd
                    
            return None
            
        except Exception as e:
            self.logger.error(f"查找按钮失败: {str(e)}")
            return None
            
    def activate_window(self, hwnd):
        """
        强制激活并置顶窗口 - 使用多种方法确保成功
        特别针对开机自启场景优化
        """
        try:
            self.logger.info(f"正在激活窗口 (句柄: {hwnd})...")
            
            # 方法1: 先显示窗口（恢复最小化状态）
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)
                self.logger.info("  步骤1: 窗口已恢复显示")
            except Exception as e:
                self.logger.warning(f"  步骤1失败: {str(e)}")
            
            # 方法2: 设置窗口为置顶
            try:
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOPMOST,
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )
                time.sleep(0.2)
                self.logger.info("  步骤2: 窗口已置顶")
            except Exception as e:
                self.logger.warning(f"  步骤2失败: {str(e)}")
            
            # 方法3: 模拟Alt键绕过前台窗口限制
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                # 短暂按下Alt键可以绕过SetForegroundWindow的限制
                shell.SendKeys('%')
                time.sleep(0.1)
                self.logger.info("  步骤3: 已发送Alt键")
            except Exception as e:
                self.logger.warning(f"  步骤3失败: {str(e)}")
            
            # 方法4: 尝试设置为前台窗口
            try:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                self.logger.info("  步骤4: 窗口已设为前台")
            except Exception as e:
                self.logger.warning(f"  步骤4失败: {str(e)}")
                # 前台设置失败时的备用方案
                try:
                    # 使用BringWindowToTop
                    win32gui.BringWindowToTop(hwnd)
                    time.sleep(0.2)
                    self.logger.info("  备用方案: 使用BringWindowToTop成功")
                except Exception as e2:
                    self.logger.warning(f"  备用方案也失败: {str(e2)}")
            
            # 方法5: 使用 SwitchToThisWindow (最强力的方法)
            try:
                import ctypes
                # 这个方法即使在受限环境也能工作
                ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
                time.sleep(0.2)
                self.logger.info("  步骤5: 使用SwitchToThisWindow成功")
            except Exception as e:
                self.logger.warning(f"  步骤5失败: {str(e)}")
            
            # 最终验证
            try:
                current_fg = win32gui.GetForegroundWindow()
                if current_fg == hwnd:
                    self.logger.info("[成功] 窗口已成功激活并置顶！")
                else:
                    fg_title = win32gui.GetWindowText(current_fg)
                    self.logger.warning(f"[警告] 窗口可能未完全激活，当前前台窗口: {fg_title}")
                    self.logger.info("将继续尝试点击操作...")
            except:
                pass
                
            # 给窗口稳定的时间
            time.sleep(0.5)
            
        except Exception as e:
            self.logger.error(f"窗口激活过程出错: {str(e)}")
            self.logger.info("将继续尝试点击操作...")
    
    def click_button(self, hwnd):
        """
        点击按钮 - 使用多种方式尝试
        即使窗口不在前台也能工作
        """
        try:
            # 方法1: 发送 BM_CLICK 消息（后台点击，不需要前台）
            self.logger.info(f"方法1: 发送BM_CLICK消息到按钮 (句柄: {hwnd})")
            try:
                win32gui.SendMessage(hwnd, win32con.BM_CLICK, 0, 0)
                time.sleep(0.3)
                self.logger.info("  → BM_CLICK发送成功")
            except Exception as e:
                self.logger.warning(f"  → BM_CLICK失败: {str(e)}")
            
            # 方法2: 发送WM_LBUTTONDOWN和WM_LBUTTONUP消息
            try:
                self.logger.info(f"方法2: 发送鼠标消息")
                win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)
                time.sleep(0.05)
                win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, 0)
                time.sleep(0.3)
                self.logger.info("  → 鼠标消息发送成功")
            except Exception as e:
                self.logger.warning(f"  → 鼠标消息失败: {str(e)}")
            
            # 方法3: PostMessage（异步消息）
            try:
                self.logger.info(f"方法3: 发送PostMessage")
                win32gui.PostMessage(hwnd, win32con.BM_CLICK, 0, 0)
                time.sleep(0.3)
                self.logger.info("  → PostMessage发送成功")
            except Exception as e:
                self.logger.warning(f"  → PostMessage失败: {str(e)}")
            
            # 方法4: 物理鼠标模拟点击（需要窗口可见）
            try:
                # 获取按钮的屏幕坐标
                rect = win32gui.GetWindowRect(hwnd)
                x = (rect[0] + rect[2]) // 2
                y = (rect[1] + rect[3]) // 2
                
                self.logger.info(f"方法4: 模拟鼠标点击坐标 ({x}, {y})")
                
                # 移动鼠标到按钮中心
                win32api.SetCursorPos((x, y))
                time.sleep(0.1)
                
                # 模拟鼠标左键按下和释放
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.3)
                self.logger.info("  → 物理鼠标点击成功")
                
            except Exception as e2:
                self.logger.warning(f"  → 物理鼠标点击失败: {str(e2)}")
            
            self.logger.info(f"[完成] 已使用多种方法尝试点击按钮")
            time.sleep(0.5)  # 等待响应
            return True
            
        except Exception as e:
            self.logger.error(f"点击按钮失败: {str(e)}")
            return False
            
    def _enumerate_candidate_windows(self):
        """枚举候选顶层窗口，关键字命中优先于兼容性启发式。"""
        candidates = []
        window_keyword = str(self.config.get('window_keyword', '') or '').strip()

        def callback(hwnd, _extra):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            text = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            if "TkTopLevel" in class_name or "按键精灵自动启动配置" in text:
                return True
            if window_keyword and window_keyword.upper() in text.upper():
                candidates.append((0, hwnd, text, class_name))
                self.logger.info(f"通过关键词 '{window_keyword}' 匹配到窗口: {text}")
                return True
            if "按键精灵" in text or "Anjian" in text or "QuickMacro" in text:
                candidates.append((1, hwnd, text, class_name))
            elif class_name == "#32770" and len(self.enum_child_windows(hwnd)) > 50:
                candidates.append((1, hwnd, text, class_name))
            return True

        win32gui.EnumWindows(callback, None)
        candidates.sort(key=lambda candidate: candidate[0])
        return candidates

    def _select_main_window(self, candidates):
        """从最高优先级候选组中选择主窗口。"""
        if not candidates:
            return None
        best_priority = candidates[0][0]
        best_group = [candidate for candidate in candidates if candidate[0] == best_priority]
        selected = next(
            (candidate for candidate in best_group if "按键精灵" not in candidate[2]),
            best_group[0],
        )
        return selected[1], selected[2], selected[3]

    def _find_main_window(self):
        """按配置重试枚举并返回主窗口句柄。"""
        retry_count = self.config['retry_count']
        retry_interval = self.config['retry_interval']
        for attempt in range(retry_count):
            self.logger.info(f"第 {attempt + 1}/{retry_count} 次尝试查找按键精灵窗口...")
            selected = self._select_main_window(self._enumerate_candidate_windows())
            if selected:
                hwnd, title, class_name = selected
                self.logger.info(
                    f"找到按键精灵窗口: {title} (句柄: {hwnd}, 类名: {class_name})"
                )
                return hwnd
            if attempt < retry_count - 1:
                self.logger.info(f"未找到窗口，{retry_interval} 秒后重试...")
                time.sleep(retry_interval)
        return None

    def find_and_click_buttons(self):
        """查找并点击按键精灵的按钮"""
        try:
            button1_text = self.config['button1_text']
            button2_text = self.config['button2_text']

            main_hwnd = self._find_main_window()
            if not main_hwnd:
                self.logger.error("未找到按键精灵窗口")
                return False
            
            # 将按键精灵窗口置顶并设为前台
            self.logger.info("正在将按键精灵窗口激活并置顶...")
            self.activate_window(main_hwnd)
                
            # 点击第一个按钮
            self.logger.info(f"正在查找第一个按钮: '{button1_text}'")
            button1_hwnd = self.find_button_by_text(main_hwnd, button1_text, log_all=True)
            
            if button1_hwnd:
                if not self.click_button(button1_hwnd):
                    self.logger.error("点击第一个按钮失败")
                    return False
                
                # 等待界面更新，让第二个按钮出现
                button_wait = self.config.get('button_wait', 4)
                self.logger.info(f"等待 {button_wait} 秒让第二个按钮出现...")
                time.sleep(button_wait)
            else:
                self.logger.warning(f"未找到第一个按钮 '{button1_text}'，尝试继续...")
                
            # 点击第二个按钮 - 使用重试机制
            self.logger.info(f"正在查找第二个按钮: '{button2_text}'")
            
            button2_hwnd = None
            # 尝试多次查找第二个按钮（因为它可能需要时间加载）
            for attempt in range(3):
                if attempt > 0:
                    self.logger.info(f"第 {attempt + 1}/3 次尝试查找第二个按钮...")
                
                # 首先在当前窗口查找（第一次尝试时显示所有控件）
                log_detail = (attempt == 0)
                button2_hwnd = self.find_button_by_text(main_hwnd, button2_text, log_all=log_detail)
                
                if not button2_hwnd:
                    # 尝试重新枚举所有窗口（可能弹出了新窗口）
                    for _priority, hwnd, title, class_name in self._enumerate_candidate_windows():
                        button2_hwnd = self.find_button_by_text(hwnd, button2_text, log_all=log_detail)
                        if button2_hwnd:
                            break
                
                if button2_hwnd:
                    break
                    
                if attempt < 2:
                    self.logger.info("未找到第二个按钮，2秒后重试...")
                    time.sleep(2)
            
            if button2_hwnd:
                if not self.click_button(button2_hwnd):
                    self.logger.error("点击第二个按钮失败")
                    return False
            else:
                self.logger.error(f"未找到第二个按钮 '{button2_text}'")
                return False
                
            self.logger.info("所有按钮点击完成！")
            
            # 点击完成后，根据配置决定是否保持置顶
            keep_topmost = self.config.get('keep_window_topmost', False)
            if not keep_topmost:
                try:
                    # 取消置顶
                    win32gui.SetWindowPos(
                        main_hwnd,
                        win32con.HWND_NOTOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                    )
                    self.logger.info("已取消窗口置顶，恢复正常状态")
                except Exception as e:
                    self.logger.warning(f"取消置顶失败: {str(e)}")
            else:
                self.logger.info("保持按键精灵窗口置顶状态")
            
            return True
            
        except Exception as e:
            self.logger.error(f"查找并点击按钮时出错: {str(e)}")
            return False
            
    def run(self):
        """主执行流程"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("按键精灵自动启动脚本开始运行")
            if self.test_mode:
                self.logger.info("【测试模式】")
            self.logger.info("=" * 60)
            
            if self.progress_window:
                self.progress_window.update_status("正在加载配置...")
                self.progress_window.update_progress(5)
            
            # 加载配置
            if not self.load_config():
                self.logger.error("配置加载失败，退出程序")
                if self.progress_window:
                    self.progress_window.update_status("配置加载失败", '#E74C3C')
                return False
            
            if self.progress_window:
                self.progress_window.update_progress(10)
                
            # 如果不是测试模式，执行开机延迟
            if not self.test_mode:
                boot_delay = self.config['boot_delay']
                if boot_delay > 0:
                    self.logger.info(f"开机延迟 {boot_delay} 秒...")
                    if self.progress_window:
                        self.progress_window.update_status(f"等待系统启动（{boot_delay}秒）...")
                    time.sleep(boot_delay)
            
            if self.progress_window:
                self.progress_window.update_progress(15)
                self.progress_window.update_status("正在检查时间段...")
                    
            # 检查时间段
            if not self.check_time_range():
                self.logger.info("不在允许的时间段内，退出程序")
                if self.progress_window:
                    self.progress_window.update_status("不在允许的时间段内", '#F39C12')
                    self.progress_window.update_progress(100)
                return True  # 不是错误，只是不执行
            
            if self.progress_window:
                self.progress_window.update_progress(20)
                self.progress_window.update_status("正在检查进程...")
                
            # 检查按键精灵是否已运行
            if self.is_anjian_running():
                self.logger.info("按键精灵已在运行，无需重复启动，退出程序")
                if self.progress_window:
                    self.progress_window.update_status("按键精灵已在运行", '#27AE60')
                    self.progress_window.update_progress(100)
                return True
            
            if self.progress_window:
                self.progress_window.update_progress(30)
                self.progress_window.update_status("正在启动按键精灵...")
                
            # 启动按键精灵
            if not self.launch_anjian():
                self.logger.error("启动按键精灵失败，退出程序")
                if self.progress_window:
                    self.progress_window.update_status("启动失败", '#E74C3C')
                return False
            
            if self.progress_window:
                self.progress_window.update_progress(50)
                self.progress_window.update_status("正在查找窗口和按钮...")
                
            # 查找并点击按钮
            if not self.find_and_click_buttons():
                self.logger.error("点击按钮失败")
                if self.progress_window:
                    self.progress_window.update_status("点击按钮失败", '#E74C3C')
                return False
            
            if self.progress_window:
                self.progress_window.update_progress(100)
                self.progress_window.update_status("任务完成！", '#27AE60')
                
            self.logger.info("=" * 60)
            self.logger.info("任务完成，程序退出")
            self.logger.info("=" * 60)
            return True
            
        except Exception as e:
            self.logger.error(f"程序运行出错: {str(e)}")
            if self.progress_window:
                self.progress_window.update_status("程序出错", '#E74C3C')
            return False


def main():
    # 检查命令行参数
    test_mode = "--test" in sys.argv
    force_window = "--window" in sys.argv
    no_window = "--no-window" in sys.argv or test_mode
    
    # 从配置文件读取是否显示窗口
    show_window_config = True
    if not force_window and not no_window:
        show_window_config = app_config.resolve_show_progress(app_config.get_config_path())
    
    # 决定是否显示窗口
    show_window = force_window or (not no_window and show_window_config)
    
    progress_window = None
    success = False
    
    # 如果需要显示窗口
    if show_window:
        try:
            from progress_window import ProgressWindow
            import threading
            
            # 创建进度窗口
            progress_window = ProgressWindow()
            
            # 在单独的线程中运行脚本
            def run_script():
                nonlocal success
                clicker = AnjianAutoClicker(test_mode=test_mode, progress_window=progress_window)
                success = clicker.run()
                
                # 任务完成后，3秒后自动关闭窗口
                if progress_window:
                    progress_window.set_auto_close(3)
            
            # 启动脚本线程
            script_thread = threading.Thread(target=run_script, daemon=True)
            script_thread.start()
            
            # 运行窗口（阻塞）
            progress_window.run()
            
            # 等待脚本线程完成
            script_thread.join(timeout=5)
            
        except Exception as e:
            print(f"进度窗口出错: {str(e)}")
            # 出错时回退到无窗口模式
            clicker = AnjianAutoClicker(test_mode=test_mode, progress_window=None)
            success = clicker.run()
    else:
        # 无窗口模式
        clicker = AnjianAutoClicker(test_mode=test_mode, progress_window=None)
        success = clicker.run()
        
        # 测试模式下暂停，让用户查看结果
        if test_mode:
            print("\n测试完成，请查看上面的日志输出")
            print("按任意键退出...")
            try:
                input()
            except:
                pass
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
