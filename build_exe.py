"""
打包脚本 - 将 Python 脚本打包成独立的 exe 文件
"""
import os
import subprocess
import shutil
import sys
import io

# 设置控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def clean_build():
    """清理之前的构建文件"""
    print("正在清理之前的构建文件...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = []
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  删除目录: {dir_name}")
    
    # 删除 .spec 文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
            print(f"  删除文件: {file}")
    
    print("清理完成！\n")


def build_config_gui():
    """打包配置程序 GUI"""
    print("=" * 60)
    print("正在打包配置程序（config_gui.exe）...")
    print("=" * 60)
    
    cmd = [
        'pyinstaller',
        '--onefile',                    # 单文件模式
        '--windowed',                   # 无控制台窗口
        '--name=按键精灵配置程序',      # 程序名称
        '--icon=NONE',                  # 图标（如果有可以指定）
        '--clean',                      # 清理临时文件
        '--noconfirm',                  # 不确认覆盖
        'config_gui.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0:
        print("[成功] 配置程序打包成功！")
        return True
    else:
        print("[失败] 配置程序打包失败：")
        print(result.stderr)
        return False


def build_auto_clicker():
    """打包自动执行脚本"""
    print("\n" + "=" * 60)
    print("正在打包自动执行脚本（auto_clicker.exe）...")
    print("=" * 60)
    
    cmd = [
        'pyinstaller',
        '--onefile',                    # 单文件模式
        '--console',                    # 保留控制台（用于调试）
        '--name=按键精灵自动启动',      # 程序名称
        '--icon=NONE',
        '--clean',
        '--noconfirm',
        '--add-data=progress_window.py;.',  # 包含进度窗口
        'auto_clicker.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    
    if result.returncode == 0:
        print("[成功] 自动执行脚本打包成功！")
        return True
    else:
        print("[失败] 自动执行脚本打包失败：")
        print(result.stderr)
        return False


def organize_output():
    """整理输出文件"""
    print("\n" + "=" * 60)
    print("正在整理输出文件...")
    print("=" * 60)
    
    # 创建发布目录
    release_dir = "release"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 复制 exe 文件
    dist_dir = "dist"
    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            if file.endswith('.exe'):
                src = os.path.join(dist_dir, file)
                dst = os.path.join(release_dir, file)
                shutil.copy2(src, dst)
                print(f"  复制: {file}")
    
    # 复制必要的文件
    files_to_copy = [
        'config.example.json',
        'README.md',
        'QUICK_START.md',
        'FOREGROUND_WINDOW_ISSUE.md',
        'VERSION_UPDATE_GUIDE.md',
        'PROGRESS_WINDOW_GUIDE.md'
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
            print(f"  复制: {file}")
    
    # 创建使用说明
    usage_file = os.path.join(release_dir, "使用说明.txt")
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("按键精灵自动启动助手 - 使用说明\n")
        f.write("=" * 60 + "\n\n")
        f.write("[文件说明]\n\n")
        f.write("1. 按键精灵配置程序.exe\n")
        f.write("   - 双击运行，进行所有配置\n")
        f.write("   - 设置按键精灵路径、时间段、按钮文本等\n")
        f.write("   - 可以一键设置/取消开机自启\n\n")
        f.write("2. 按键精灵自动启动.exe\n")
        f.write("   - 开机自动运行的程序（不要手动运行）\n")
        f.write("   - 会在配置的时间段内自动启动按键精灵\n\n")
        f.write("3. config.example.json\n")
        f.write("   - 配置文件示例\n")
        f.write("   - 第一次运行配置程序会自动创建 config.json\n\n")
        f.write("4. 其他 .md 文件\n")
        f.write("   - 详细的使用说明和故障排查指南\n\n")
        f.write("=" * 60 + "\n")
        f.write("[快速开始]\n")
        f.write("=" * 60 + "\n\n")
        f.write("第1步：双击运行 按键精灵配置程序.exe\n\n")
        f.write("第2步：在配置界面中设置：\n")
        f.write("  - 选择按键精灵程序路径\n")
        f.write("  - 设置时间段（如 8:00 - 22:00）\n")
        f.write("  - 选择生效的星期几\n")
        f.write("  - 填写按钮文本（开始使用、启动）\n")
        f.write("  - 填写窗口关键词（如：YZ2K2）\n\n")
        f.write("第3步：点击 [保存配置] 按钮\n\n")
        f.write("第4步：点击 [测试运行] 按钮，确保正常工作\n\n")
        f.write("第5步：点击 [设置开机自启] 按钮\n\n")
        f.write("完成！重启电脑测试。\n\n")
        f.write("=" * 60 + "\n")
        f.write("[注意事项]\n")
        f.write("=" * 60 + "\n\n")
        f.write("1. 配置程序和自动启动程序必须在同一个文件夹中\n")
        f.write("2. config.json 文件会自动创建在程序所在目录\n")
        f.write("3. logs 文件夹会自动创建，包含执行日志\n")
        f.write("4. 不要删除 config.json 文件，否则需要重新配置\n\n")
        f.write("5. 如果看到 \"无法将窗口设置为前台\" 的警告：\n")
        f.write("   这是正常现象！不影响功能！\n")
        f.write("   详见：FOREGROUND_WINDOW_ISSUE.md\n\n")
        f.write("=" * 60 + "\n")
        f.write("[需要帮助?]\n")
        f.write("=" * 60 + "\n\n")
        f.write("查看日志文件：logs\\auto_clicker_YYYYMMDD.log\n")
        f.write("阅读文档：README.md、QUICK_START.md\n\n")
        f.write("祝使用愉快！\n")
    
    print(f"  创建: 使用说明.txt")
    
    print(f"\n[完成] 所有文件已整理到 {release_dir} 目录")


def main():
    print("=" * 60)
    print("按键精灵自动启动助手 - 打包工具")
    print("=" * 60)
    print()
    
    # 检查是否安装了 pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("错误：未安装 pyinstaller")
        print("请先运行: pip install pyinstaller")
        return
    
    # 清理之前的构建
    clean_build()
    
    # 打包配置程序
    if not build_config_gui():
        print("\n打包失败，请检查错误信息")
        return
    
    # 打包自动执行脚本
    if not build_auto_clicker():
        print("\n打包失败，请检查错误信息")
        return
    
    # 整理输出文件
    organize_output()
    
    print("\n" + "=" * 60)
    print("[完成] 打包成功！")
    print("=" * 60)
    print()
    print(f"所有文件位于: release 目录")
    print()
    print("包含的文件：")
    print("  - 按键精灵配置程序.exe  - 配置工具")
    print("  - 按键精灵自动启动.exe  - 自动执行程序")
    print("  - config.example.json   - 配置示例")
    print("  - 使用说明.txt         - 快速使用指南")
    print("  - 各种 .md 文档         - 详细说明")
    print()
    print("=" * 60)
    print("分发建议：")
    print("=" * 60)
    print()
    print("将 release 文件夹整个复制到目标电脑即可使用！")
    print("不需要安装 Python 环境！")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

