import builtins
import json

import pytest

import config_manager


DIRECT_KEYS = {
    "anjian_path",
    "start_hour",
    "start_minute",
    "end_hour",
    "end_minute",
    "active_days",
    "boot_delay",
    "launch_wait",
    "retry_count",
    "retry_interval",
    "button1_text",
    "button2_text",
}
FALLBACK_KEYS = {"button_wait", "window_keyword", "show_progress", "keep_window_topmost"}


def test_default_schema_and_values():
    assert set(config_manager.DEFAULT_CONFIG) == DIRECT_KEYS | FALLBACK_KEYS
    assert {key: config_manager.DEFAULT_CONFIG[key] for key in DIRECT_KEYS} == {
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
    }
    assert {key: config_manager.DEFAULT_CONFIG[key] for key in FALLBACK_KEYS} == {
        "button_wait": 4,
        "window_keyword": "",
        "show_progress": True,
        "keep_window_topmost": False,
    }


def test_default_config_returns_independent_copy():
    first = config_manager.default_config()
    first["active_days"].remove(0)
    assert config_manager.default_config()["active_days"] == list(range(7))


def test_load_missing_file_returns_defaults(tmp_path):
    assert config_manager.load_config(tmp_path / "missing.json") == config_manager.default_config()


def test_load_partial_config_merges_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"retry_count": 9}', encoding="utf-8")
    loaded = config_manager.load_config(path)
    assert loaded["retry_count"] == 9
    assert loaded["button_wait"] == 4
    assert set(loaded) == DIRECT_KEYS | FALLBACK_KEYS


@pytest.mark.parametrize("content", ["{not json", "[1, 2]", '"abc"'])
def test_load_rejects_invalid_or_non_object_json(tmp_path, content):
    path = tmp_path / "config.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(config_manager.ConfigLoadError):
        config_manager.load_config(path)


def test_load_wraps_read_errors(monkeypatch):
    def fail_open(*args, **kwargs):
        raise OSError("cannot read")

    monkeypatch.setattr(builtins, "open", fail_open)
    with pytest.raises(config_manager.ConfigLoadError, match="cannot read"):
        config_manager.load_config("config.json")


def test_save_load_round_trip_preserves_all_fields(tmp_path):
    path = tmp_path / "config.json"
    expected = config_manager.default_config()
    expected.update(
        anjian_path="C:/Anjian/app.exe",
        active_days=[0, 2, 6],
        button_wait=12,
        window_keyword="YZ2K2",
        show_progress=False,
        keep_window_topmost=True,
    )
    config_manager.save_config(expected, path)
    assert config_manager.load_config(path) == expected
    assert set(json.loads(path.read_text(encoding="utf-8"))) == DIRECT_KEYS | FALLBACK_KEYS


def test_validate_valid_config_and_does_not_check_path_exists():
    config = config_manager.default_config()
    config["anjian_path"] = "/definitely/not/a/real/file.exe"
    assert config_manager.validate_config(config) == []


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"anjian_path": ""}, "请选择按键精灵程序路径"),
        ({"active_days": []}, "请至少选择一个生效日期"),
        ({"active_days": [7]}, "生效日期必须是 0 到 6 之间的整数"),
        ({"start_hour": 24}, "开始时间（时）必须在 0 到 23 之间"),
        ({"end_minute": 60}, "结束时间（分）必须在 0 到 59 之间"),
        ({"boot_delay": 301}, "开机延迟(秒)必须在 0 到 300 之间"),
        ({"retry_count": 0}, "重试次数必须在 1 到 20 之间"),
        ({"button_wait": 61}, "按钮等待(秒)必须在 0 到 60 之间"),
        ({"button1_text": ""}, "第一个按钮文本不能为空"),
        ({"button2_text": ""}, "第二个按钮文本不能为空"),
    ],
)
def test_validate_reports_expected_errors(changes, message):
    config = config_manager.default_config()
    config["anjian_path"] = "app.exe"
    config.update(changes)
    assert message in config_manager.validate_config(config)
