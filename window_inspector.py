"""
窗口探测工具 - 用于诊断和查找按键精灵的窗口和控件
"""
import sys
import win32gui
import win32con

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def enum_all_windows():
    """枚举所有顶层窗口"""
    windows = []
    
    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            if title:  # 只显示有标题的窗口
                results.append((hwnd, title, class_name))
        return True
    
    win32gui.EnumWindows(callback, windows)
    return windows


def enum_child_windows(parent_hwnd, indent=0):
    """递归枚举所有子窗口和控件"""
    children = []
    
    def callback(hwnd, results):
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)
            is_enabled = win32gui.IsWindowEnabled(hwnd)
            
            info = {
                'hwnd': hwnd,
                'title': title,
                'class_name': class_name,
                'rect': rect,
                'visible': is_visible,
                'enabled': is_enabled,
                'indent': indent
            }
            results.append(info)
            
            # 递归枚举子控件
            sub_children = []
            win32gui.EnumChildWindows(hwnd, callback, sub_children)
            for child in sub_children:
                child['indent'] = indent + 1
                results.append(child)
                
        except Exception as e:
            pass
        return True
    
    win32gui.EnumChildWindows(parent_hwnd, callback, children)
    return children


def print_window_info(hwnd, title, class_name):
    """打印窗口的详细信息"""
    print("=" * 80)
    print(f"窗口标题: {title}")
    print(f"窗口类名: {class_name}")
    print(f"窗口句柄: {hwnd}")
    print("-" * 80)
    
    # 枚举所有子控件
    children = enum_child_windows(hwnd)
    
    if not children:
        print("  (没有找到子控件)")
    else:
        print(f"找到 {len(children)} 个子控件:")
        print()
        
        for i, child in enumerate(children, 1):
            indent = "  " * child['indent']
            status = []
            if not child['visible']:
                status.append("隐藏")
            if not child['enabled']:
                status.append("禁用")
            status_str = f" [{', '.join(status)}]" if status else ""
            
            if child['title']:
                print(f"{indent}[{i}] 文本: '{child['title']}'")
                print(f"{indent}    类名: {child['class_name']}")
                print(f"{indent}    句柄: {child['hwnd']}{status_str}")
                print()


def main():
    print("=" * 80)
    print("窗口探测工具 - 查找按键精灵的窗口和按钮")
    print("=" * 80)
    print()
    
    # 枚举所有窗口
    print("正在扫描所有可见窗口...")
    windows = enum_all_windows()
    
    # 显示所有窗口，让用户选择
    print()
    print(f"找到 {len(windows)} 个可见窗口：")
    print("=" * 80)
    
    for i, (hwnd, title, class_name) in enumerate(windows[:50], 1):  # 显示前50个
        print(f"{i:2d}. {title}")
        if class_name:
            print(f"    类名: {class_name}")
    
    print()
    print("=" * 80)
    print()
    print("请找到按键精灵的窗口（窗口标题是您的脚本文件名）")
    print("输入窗口编号来分析该窗口，或输入0退出：")
    print()
    
    try:
        choice = int(input("请输入编号: ").strip())
        if choice == 0:
            print("已退出")
            return
        if 1 <= choice <= len(windows):
            selected = windows[choice - 1]
            anjian_windows = [selected]
        else:
            print("编号无效")
            return
    except (ValueError, EOFError):
        print("输入无效")
        return
    
    # 显示找到的窗口
    print()
    print(f"[OK] 找到 {len(anjian_windows)} 个可能的窗口:")
    print()
    
    for i, (hwnd, title, class_name) in enumerate(anjian_windows, 1):
        print(f"{i}. {title}")
        print(f"   类名: {class_name}")
        print(f"   句柄: {hwnd}")
        print()
    
    # 分析所有找到的窗口
    selected = anjian_windows[0]
    print(f"正在分析窗口: {selected[1]}")
    print()
    
    # 显示详细信息
    print()
    print_window_info(selected[0], selected[1], selected[2])
    
    # 查找可能的按钮
    print("=" * 80)
    print("[搜索] 查找可能的按钮控件:")
    print("=" * 80)
    
    children = enum_child_windows(selected[0])
    button_keywords = ["启动", "开始", "运行", "start", "begin", "run", "确定", "ok", "使用"]
    
    found_buttons = []
    for child in children:
        if child['title']:
            title_lower = child['title'].lower()
            class_lower = child['class_name'].lower()
            
            # 检查是否是按钮类控件
            is_button = 'button' in class_lower or 'btn' in class_lower
            
            # 检查文本是否包含按钮关键词
            has_keyword = any(keyword in title_lower for keyword in button_keywords)
            
            if is_button or has_keyword:
                found_buttons.append(child)
    
    if found_buttons:
        print()
        print(f"找到 {len(found_buttons)} 个可能的按钮:")
        print()
        for i, btn in enumerate(found_buttons, 1):
            print(f"[{i}] 按钮文本: '{btn['title']}'")
            print(f"    类名: {btn['class_name']}")
            print(f"    句柄: {btn['hwnd']}")
            print(f"    可见: {'是' if btn['visible'] else '否'}")
            print(f"    启用: {'是' if btn['enabled'] else '否'}")
            print()
    else:
        print()
        print("[!] 未找到明显的按钮控件")
        print()
        print("建议：")
        print("1. 检查上面列出的所有控件，找到包含 '开始使用' 或 '启动' 的文本")
        print("2. 将完整的文本内容复制到配置文件中")
        print("3. 按钮可能使用了自定义控件，不是标准的 Button 类")
        print()
    
    # 生成建议的配置
    print("=" * 80)
    print("[配置建议]")
    print("=" * 80)
    print()
    
    if found_buttons:
        print("根据找到的按钮，建议在配置中使用以下文本：")
        print()
        for i, btn in enumerate(found_buttons[:5], 1):  # 最多显示5个
            print(f"{i}. 按钮文本: {btn['title']}")
        print()
        print("您可以使用完整文本，或者只使用关键词部分（如'开始使用'或'启动'）")
    else:
        print("请手动查看上面列出的所有控件，找到您需要点击的按钮文本。")
    
    print()
    print("=" * 80)
    print("分析完成！请将上述信息用于配置 config_gui.py")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

