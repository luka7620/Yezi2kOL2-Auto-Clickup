"""应用配置、校验与启动命令解析（不依赖 GUI 或 Windows 扩展）。"""
from dataclasses import dataclass, field
import json
import os
import sys
from typing import Optional


DEFAULT_CONFIG = {
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
    "button_wait": 4,
    "button1_text": "开始使用",
    "button2_text": "启动",
    "window_keyword": "",
    "show_progress": True,
    "keep_window_topmost": False,
}

NUMBER_RULES = {
    "start_hour": (0, 23, "开始小时"),
    "start_minute": (0, 59, "开始分钟"),
    "end_hour": (0, 23, "结束小时"),
    "end_minute": (0, 59, "结束分钟"),
    "boot_delay": (0, 300, "开机延迟"),
    "launch_wait": (0, 60, "启动等待"),
    "retry_count": (1, 20, "重试次数"),
    "retry_interval": (1, 30, "重试间隔"),
    "button_wait": (1, 30, "按钮等待"),
}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_config_path() -> str:
    return os.path.abspath(os.path.join(get_app_dir(), "config.json"))


def _default_copy() -> dict:
    return {**DEFAULT_CONFIG, "active_days": list(DEFAULT_CONFIG["active_days"])}


def load_config(path: str) -> dict:
    config = _default_copy()
    try:
        with open(path, "r", encoding="utf-8") as config_file:
            loaded = json.load(config_file)
        if isinstance(loaded, dict):
            config.update(loaded)
    except (OSError, ValueError, TypeError):
        pass
    return config


def save_config(path: str, updates: dict) -> dict:
    config = load_config(path)
    config.update(updates)
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=4)
        config_file.write("\n")
    return config


def validate_raw_fields(raw: dict[str, str]) -> ValidationResult:
    result = ValidationResult()
    for key, (minimum, maximum, label) in NUMBER_RULES.items():
        value = str(raw.get(key, "")).strip()
        if not value:
            result.errors.append(f"{label}不能为空")
            continue
        try:
            number = int(value)
        except ValueError:
            result.errors.append(f"{label}必须是整数")
            continue
        if not minimum <= number <= maximum:
            result.errors.append(f"{label}必须在 {minimum} 到 {maximum} 之间")
    return result


def validate_config(cfg: dict) -> ValidationResult:
    result = ValidationResult()
    path = str(cfg.get("anjian_path", "")).strip()
    if not path:
        result.errors.append("请选择按键精灵程序路径")
    elif not os.path.isfile(path):
        result.warnings.append(f"按键精灵程序路径当前不存在：{path}")

    try:
        start = int(cfg["start_hour"]) * 60 + int(cfg["start_minute"])
        end = int(cfg["end_hour"]) * 60 + int(cfg["end_minute"])
        if start >= end:
            result.errors.append("开始时间必须严格早于结束时间（暂不支持跨零点）")
    except (KeyError, TypeError, ValueError):
        result.errors.append("开始时间或结束时间无效")

    if not cfg.get("active_days"):
        result.errors.append("请至少选择一个生效日期")
    if not str(cfg.get("button1_text", "")).strip():
        result.errors.append("第一个按钮文本不能为空")
    if not str(cfg.get("button2_text", "")).strip():
        result.errors.append("第二个按钮文本不能为空")
    return result


def resolve_launch_command(
    action: str,
    frozen: bool,
    app_dir: str,
    python_exe: Optional[str] = None,
) -> dict:
    """解析测试运行或开机自启所需的绝对路径。"""
    if action not in {"test", "autostart"}:
        raise ValueError(f"不支持的启动操作：{action}")
    app_dir = os.path.abspath(app_dir)
    python_exe = os.path.abspath(python_exe or sys.executable)
    executable = os.path.join(app_dir, "按键精灵自动启动.exe")
    script = os.path.join(app_dir, "auto_clicker.py")
    warnings = []

    if action == "test":
        target = executable if frozen else script
        args = [target, "--test"] if frozen else [python_exe, target, "--test"]
        return {
            "args": args,
            "workdir": app_dir,
            "target_path": target,
            "interpreter_path": None if frozen else python_exe,
            "warnings": warnings,
        }

    if frozen:
        command = executable
        arguments = ""
        target = executable
        interpreter = None
    else:
        script = os.path.abspath(script)
        pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        if os.path.isfile(pythonw):
            command = pythonw
        else:
            command = python_exe
            warnings.append("未找到 pythonw.exe，将使用 python.exe，开机启动时可能闪现控制台窗口")
        arguments = f'"{script}"'
        target = script
        interpreter = command
    return {
        "command": command,
        "arguments": arguments,
        "workdir": app_dir,
        "target_path": target,
        "interpreter_path": interpreter,
        "warnings": warnings,
    }
