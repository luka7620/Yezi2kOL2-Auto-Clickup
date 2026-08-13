"""配置文件的加载、校验与保存逻辑。"""
import copy
import json
import re


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
    "button1_text": "开始使用",
    "button2_text": "启动",
    "button_wait": 4,
    "window_keyword": "",
    "show_progress": True,
    "keep_window_topmost": False,
}

INT_FIELDS = (
    ("start_hour", "开始时间（时）", 0, 23),
    ("start_minute", "开始时间（分）", 0, 59),
    ("end_hour", "结束时间（时）", 0, 23),
    ("end_minute", "结束时间（分）", 0, 59),
    ("boot_delay", "开机延迟(秒)", 0, 300),
    ("launch_wait", "启动等待(秒)", 0, 60),
    ("retry_count", "重试次数", 1, 20),
    ("retry_interval", "重试间隔(秒)", 1, 30),
    ("button_wait", "按钮等待(秒)", 0, 60),
)


class ConfigLoadError(Exception):
    """配置文件存在但无法读取为合法配置时抛出。"""


def default_config():
    """返回一份可独立修改的完整默认配置。"""
    return copy.deepcopy(DEFAULT_CONFIG)


def _is_valid_int(value, minimum, maximum):
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def _normalize_int(value):
    """将无歧义的十进制整数字符串迁移为整数。"""
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        try:
            return int(value.strip())
        except ValueError:
            # 超过解释器整数文本长度限制时保留原值，交由字段检查统一报错。
            return value
    return value


def _normalize_legacy_values(config):
    """规范化旧配置中曾被 GUI 接受的整数文本。"""
    for key, _label, _minimum, _maximum in INT_FIELDS:
        config[key] = _normalize_int(config[key])

    if isinstance(config["active_days"], list):
        config["active_days"] = [_normalize_int(day) for day in config["active_days"]]


def _check_field_types(config):
    """检查已知字段的持久化类型和结构，不校验是否为空。"""
    errors = []

    for key in ("anjian_path", "window_keyword", "button1_text", "button2_text"):
        if not isinstance(config[key], str):
            errors.append(f"配置项 {key} 的类型或取值无效")

    for key, _label, minimum, maximum in INT_FIELDS:
        if not _is_valid_int(config[key], minimum, maximum):
            errors.append(f"配置项 {key} 的类型或取值无效")

    active_days = config["active_days"]
    if not isinstance(active_days, list) or any(
        not _is_valid_int(day, 0, 6) for day in active_days
    ):
        errors.append("配置项 active_days 的类型或取值无效")

    for key in ("show_progress", "keep_window_topmost"):
        if not isinstance(config[key], bool):
            errors.append(f"配置项 {key} 的类型或取值无效")

    return errors


def load_config(path="config.json"):
    """读取配置，并用默认值补全旧版配置中缺失的字段。"""
    try:
        with open(path, "r", encoding="utf-8") as config_file:
            data = json.load(config_file)
    except FileNotFoundError:
        return default_config()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConfigLoadError(str(error)) from error

    if not isinstance(data, dict):
        raise ConfigLoadError("配置文件顶层必须是 JSON 对象")

    config = default_config()
    config.update(data)
    _normalize_legacy_values(config)
    errors = _check_field_types(config)
    if errors:
        raise ConfigLoadError("；".join(errors))
    return config


def validate_config(config):
    """返回配置中的全部校验错误；合法时返回空列表。"""
    errors = []

    if not isinstance(config.get("anjian_path"), str) or not config["anjian_path"]:
        errors.append("请选择按键精灵程序路径")

    if not isinstance(config.get("window_keyword"), str) or not config["window_keyword"].strip():
        errors.append("窗口关键词不能为空")

    active_days = config.get("active_days")
    if not active_days:
        errors.append("请至少选择一个生效日期")
    elif not isinstance(active_days, list) or any(
        not isinstance(day, int) or isinstance(day, bool) or day < 0 or day > 6
        for day in active_days
    ):
        errors.append("生效日期必须是 0 到 6 之间的整数")

    for key, label, minimum, maximum in INT_FIELDS:
        value = config.get(key)
        if not _is_valid_int(value, minimum, maximum):
            errors.append(f"{label}必须在 {minimum} 到 {maximum} 之间")

    if not isinstance(config.get("button1_text"), str) or not config["button1_text"].strip():
        errors.append("第一个按钮文本不能为空")
    if not isinstance(config.get("button2_text"), str) or not config["button2_text"].strip():
        errors.append("第二个按钮文本不能为空")

    if not isinstance(config.get("show_progress"), bool):
        errors.append("运行时显示进度窗口必须是布尔值")
    if not isinstance(config.get("keep_window_topmost"), bool):
        errors.append("保持目标窗口置顶必须是布尔值")

    return errors


def save_config(config, path="config.json"):
    """以现有格式将配置保存到文件。"""
    with open(path, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4, ensure_ascii=False)
