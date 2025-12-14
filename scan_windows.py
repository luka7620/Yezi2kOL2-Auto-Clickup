"""
简化的窗口扫描工具 - 将结果输出到文件
"""
import sys
import win32gui


def enum_all_windows():
    """枚举所有顶层窗口"""
    windows = []
    
    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            if title:
                results.append((hwnd, title, class_name))
        return True
    
    win32gui.EnumWindows(callback, windows)
    return windows


def enum_child_windows(parent_hwnd):
    """枚举所有子窗口"""
    children = []
    
    def callback(hwnd, results):
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)
            
            if title:  # 只记录有文本的控件
                results.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': class_name,
                    'visible': is_visible
                })
        except:
            pass
        return True
    
    win32gui.EnumChildWindows(parent_hwnd, callback, children)
    return children


def main():
    output_file = "window_scan_result.txt"
    
    print("正在扫描所有窗口...")
    windows = enum_all_windows()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("窗口扫描结果\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"找到 {len(windows)} 个可见窗口\n\n")
        f.write("=" * 80 + "\n")
        f.write("所有窗口列表\n")
        f.write("=" * 80 + "\n\n")
        
        for i, (hwnd, title, class_name) in enumerate(windows, 1):
            f.write(f"{i:3d}. 窗口标题: {title}\n")
            f.write(f"     类名: {class_name}\n")
            f.write(f"     句柄: {hwnd}\n\n")
        
        # 查找可能的按键精灵窗口
        f.write("\n" + "=" * 80 + "\n")
        f.write("分析所有窗口的子控件（查找按钮）\n")
        f.write("=" * 80 + "\n\n")
        
        for i, (hwnd, title, class_name) in enumerate(windows, 1):
            children = enum_child_windows(hwnd)
            
            # 只分析有子控件的窗口
            if children:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"窗口 {i}: {title}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"找到 {len(children)} 个有文本的子控件:\n\n")
                
                for j, child in enumerate(children, 1):
                    f.write(f"  [{j}] 文本: '{child['title']}'\n")
                    f.write(f"      类名: {child['class_name']}\n")
                    f.write(f"      句柄: {child['hwnd']}\n")
                    if not child['visible']:
                        f.write(f"      状态: [隐藏]\n")
                    f.write("\n")
    
    print(f"扫描完成！")
    print(f"结果已保存到: {output_file}")
    print()
    print("请打开该文件，查找：")
    print("1. 找到按键精灵的窗口（窗口标题是您的脚本文件名）")
    print("2. 查看该窗口下的所有子控件")
    print("3. 找到包含'开始使用'和'启动'的控件文本")
    print("4. 将这些文本复制到配置中")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()







