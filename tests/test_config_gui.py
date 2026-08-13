import json
from types import SimpleNamespace

import pytest

tk = pytest.importorskip("tkinter", reason="未安装 Tkinter，跳过 GUI 测试")

import config_manager
from config_gui import ConfigGUI


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("无显示环境，跳过 GUI 测试")
    root.withdraw()
    yield root
    root.destroy()


def is_descendant(widget, parent):
    current = widget
    while current is not None:
        if current == parent:
            return True
        current = current.master
    return False


def full_config():
    config = config_manager.default_config()
    config.update(
        anjian_path="C:/Anjian/app.exe",
        start_hour=9,
        start_minute=10,
        end_hour=20,
        end_minute=30,
        active_days=[1, 3, 5],
        boot_delay=21,
        launch_wait=11,
        retry_count=7,
        retry_interval=6,
        button1_text="打开",
        button2_text="运行",
        button_wait=9,
        window_keyword="YZ2K2",
        show_progress=False,
        keep_window_topmost=True,
    )
    return config


def test_notebook_tabs_and_widget_ownership(tk_root, tmp_path):
    gui = ConfigGUI(tk_root, config_file=str(tmp_path / "config.json"))
    assert gui.notebook.tabs() == (
        str(gui.tab_basic),
        str(gui.tab_schedule),
        str(gui.tab_advanced),
    )
    assert is_descendant(gui.window_keyword_entry, gui.tab_basic)
    assert is_descendant(gui.button_wait_spinbox, gui.tab_basic)
    assert is_descendant(gui.show_progress_checkbutton, gui.tab_advanced)
    assert is_descendant(gui.keep_topmost_checkbutton, gui.tab_advanced)


def test_load_and_save_round_trip_all_fields(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    expected = full_config()
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: None)
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: None)
    monkeypatch.setattr("os.path.exists", lambda value: True)

    gui = ConfigGUI(tk_root, config_file=str(path))
    collected, errors = gui.collect_form_config()
    assert errors == []
    assert collected == expected
    gui.save_config_action()
    assert json.loads(path.read_text(encoding="utf-8")) == expected


def test_gui_save_preserves_unknown_config_fields(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    expected = full_config()
    expected["custom_key"] = "preserved"
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: None)
    monkeypatch.setattr("os.path.exists", lambda value: True)

    gui = ConfigGUI(tk_root, config_file=str(path))
    gui.button_wait_var.set("13")
    gui.save_config_action()

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["custom_key"] == "preserved"
    assert saved["button_wait"] == 13
    assert saved["anjian_path"] == expected["anjian_path"]
    assert saved["window_keyword"] == expected["window_keyword"]


def test_legacy_integer_text_loads_and_saves_without_losing_fields(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    expected = full_config()
    legacy = dict(expected, start_hour="8")
    path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    error_calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: error_calls.append(args))
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: None)
    monkeypatch.setattr("os.path.exists", lambda value: True)

    gui = ConfigGUI(tk_root, config_file=str(path))
    assert error_calls == []
    gui.save_config_action()

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == dict(expected, start_hour=8)


def test_parse_errors_are_aggregated_and_do_not_write(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    gui = ConfigGUI(tk_root, config_file=str(path))
    gui.boot_delay_var.set("")
    gui.retry_count_var.set("abc")
    gui.path_var.set("")
    calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: calls.append(args))

    gui.save_config_action()

    assert len(calls) == 1
    message = calls[0][1]
    assert message.count("必须是整数") == 2
    assert "请选择按键精灵程序路径" in message
    assert not path.exists()


def test_validation_failure_does_not_call_save(tk_root, tmp_path, monkeypatch):
    gui = ConfigGUI(tk_root, config_file=str(tmp_path / "config.json"))
    gui.path_var.set("app.exe")
    gui.start_hour_var.set("99")
    monkeypatch.setattr("os.path.exists", lambda value: True)
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: None)
    calls = []
    monkeypatch.setattr(config_manager, "save_config", lambda *args: calls.append(args))
    gui.save_config_action()
    assert calls == []


def test_fresh_form_with_only_path_does_not_save(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    gui = ConfigGUI(tk_root, config_file=str(path))
    gui.path_var.set("C:/Anjian/app.exe")
    monkeypatch.setattr("os.path.exists", lambda value: True)
    calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: calls.append(args))

    gui.save_config_action()

    assert len(calls) == 1
    assert "窗口关键词不能为空" in calls[0][1]
    assert not path.is_file()


def test_whitespace_keyword_blocked_and_valid_keyword_stripped(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    gui = ConfigGUI(tk_root, config_file=str(path))
    gui.path_var.set("C:/Anjian/app.exe")
    monkeypatch.setattr("os.path.exists", lambda value: True)
    error_calls = []
    info_calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: error_calls.append(args))
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: info_calls.append(args))

    gui.window_keyword_var.set("   ")
    gui.save_config_action()
    assert len(error_calls) == 1
    assert "窗口关键词不能为空" in error_calls[0][1]
    assert not path.is_file()

    gui.window_keyword_var.set(" YZ2K2 ")
    gui.save_config_action()
    assert len(info_calls) == 1
    assert json.loads(path.read_text(encoding="utf-8"))["window_keyword"] == "YZ2K2"


@pytest.mark.parametrize(
    ("field_name", "message"),
    [
        ("button1_text_var", "第一个按钮文本不能为空"),
        ("button2_text_var", "第二个按钮文本不能为空"),
    ],
)
def test_whitespace_button_text_is_blocked(tk_root, tmp_path, monkeypatch, field_name, message):
    path = tmp_path / "config.json"
    gui = ConfigGUI(tk_root, config_file=str(path))
    gui.path_var.set("C:/Anjian/app.exe")
    gui.window_keyword_var.set("YZ2K2")
    getattr(gui, field_name).set("   ")
    monkeypatch.setattr("os.path.exists", lambda value: True)
    calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: calls.append(args))

    gui.save_config_action()

    assert len(calls) == 1
    assert message in calls[0][1]
    assert not path.is_file()


def test_button_text_is_stripped_when_saved(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    gui = ConfigGUI(tk_root, config_file=str(path))
    gui.path_var.set("C:/Anjian/app.exe")
    gui.window_keyword_var.set("YZ2K2")
    gui.button1_text_var.set("  开始使用  ")
    gui.button2_text_var.set("  启动  ")
    monkeypatch.setattr("os.path.exists", lambda value: True)
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: None)

    gui.save_config_action()

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["button1_text"] == "开始使用"
    assert saved["button2_text"] == "启动"


def test_damaged_config_shows_once_and_falls_back(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")
    calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: calls.append(args))
    gui = ConfigGUI(tk_root, config_file=str(path))
    assert len(calls) == 1
    assert gui.config == config_manager.default_config()
    collected, errors = gui.collect_form_config()
    assert errors == []
    assert collected == config_manager.default_config()


def test_invalid_typed_config_shows_once_and_falls_back(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{"active_days": null}', encoding="utf-8")
    calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: calls.append(args))

    gui = ConfigGUI(tk_root, config_file=str(path))

    assert len(calls) == 1
    assert "active_days" in calls[0][1]
    assert gui.config == config_manager.default_config()
    collected, errors = gui.collect_form_config()
    assert errors == []
    assert collected == config_manager.default_config()


def test_oversized_legacy_integer_shows_once_and_falls_back(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"start_hour": "9" * 5000}), encoding="utf-8")
    calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: calls.append(args))

    gui = ConfigGUI(tk_root, config_file=str(path))

    assert len(calls) == 1
    assert "start_hour" in calls[0][1]
    assert gui.load_recovery_error is not None
    assert gui.config == config_manager.default_config()
    collected, errors = gui.collect_form_config()
    assert errors == []
    assert collected == config_manager.default_config()


def _fill_recovered_form(gui):
    gui.path_var.set("C:/Anjian/recovered.exe")
    gui.window_keyword_var.set("RECOVERED")


def test_recovered_form_does_not_overwrite_when_confirmation_declined(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    original = b'{"active_days": null}'
    path.write_bytes(original)
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: None)
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args: False)
    monkeypatch.setattr("os.path.exists", lambda value: True)
    save_calls = []
    monkeypatch.setattr(config_manager, "save_config", lambda *args: save_calls.append(args))
    gui = ConfigGUI(tk_root, config_file=str(path))
    _fill_recovered_form(gui)

    gui.save_config_action()

    assert save_calls == []
    assert path.read_bytes() == original
    assert gui.load_recovery_error is not None


def test_recovered_form_overwrites_only_after_confirmation(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{"active_days": null}', encoding="utf-8")
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: None)
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: None)
    confirm_calls = []
    monkeypatch.setattr(
        "tkinter.messagebox.askyesno",
        lambda *args: confirm_calls.append(args) or True,
    )
    monkeypatch.setattr("os.path.exists", lambda value: True)
    gui = ConfigGUI(tk_root, config_file=str(path))
    _fill_recovered_form(gui)

    gui.save_config_action()

    assert len(confirm_calls) == 1
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["anjian_path"] == "C:/Anjian/recovered.exe"
    assert saved["window_keyword"] == "RECOVERED"
    assert gui.load_recovery_error is None


def test_recovery_state_blocks_test_and_autostart_before_subprocess(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")
    error_calls = []
    popen_calls = []
    run_calls = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: error_calls.append(args))
    monkeypatch.setattr("os.path.exists", lambda value: True)
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: popen_calls.append((args, kwargs)))
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: run_calls.append((args, kwargs)))
    gui = ConfigGUI(tk_root, config_file=str(path))
    error_calls.clear()

    gui.test_script()
    gui.setup_autostart()

    assert popen_calls == []
    assert run_calls == []
    assert len(error_calls) == 2
    assert all("先恢复并保存有效配置" in call[1] for call in error_calls)


def test_test_and_autostart_resume_after_recovery_save(tk_root, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text("{broken", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *args: None)
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args: None)
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *args: True)
    monkeypatch.setattr("os.path.exists", lambda value: True)
    popen_calls = []
    run_calls = []
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: popen_calls.append((args, kwargs)))
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: run_calls.append((args, kwargs)) or SimpleNamespace(returncode=0, stderr=""),
    )
    gui = ConfigGUI(tk_root, config_file=str(path))
    _fill_recovered_form(gui)

    gui.save_config_action()
    assert gui.load_recovery_error is None
    gui.test_script()
    gui.setup_autostart()

    assert len(popen_calls) == 1
    assert len(run_calls) == 1
    assert not (tmp_path / "temp_task.xml").exists()
