import importlib
import importlib.util
import os
import sys
import tempfile
import unittest
from unittest import mock


_STUB_NAMES = ("win32gui", "win32con", "win32process", "win32api", "psutil")
_stubs = {
    name: mock.MagicMock()
    for name in _STUB_NAMES
    if importlib.util.find_spec(name) is None
}
with mock.patch.dict(sys.modules, _stubs):
    auto_clicker = importlib.import_module("auto_clicker")
AnjianAutoClicker = auto_clicker.AnjianAutoClicker


class FakeWin32Gui:
    def __init__(self, windows):
        self.windows = windows

    def EnumWindows(self, callback, extra):
        for hwnd in self.windows:
            callback(hwnd, extra)

    def IsWindowVisible(self, hwnd):
        return self.windows[hwnd][2]

    def GetWindowText(self, hwnd):
        return self.windows[hwnd][0]

    def GetClassName(self, hwnd):
        return self.windows[hwnd][1]


class AutoClickerWindowMatchTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.temp_directory = tempfile.TemporaryDirectory()
        os.chdir(self.temp_directory.name)
        self.clicker = AnjianAutoClicker()
        self.clicker.config = {
            "window_keyword": "",
            "retry_count": 1,
            "retry_interval": 0,
        }
        self.child_counts = {}
        self.clicker.enum_child_windows = (
            lambda hwnd: [0] * self.child_counts.get(hwnd, 0)
        )

    def tearDown(self):
        for handler in list(self.clicker.logger.handlers):
            handler.close()
            self.clicker.logger.removeHandler(handler)
        os.chdir(self.original_cwd)
        self.temp_directory.cleanup()

    def enumerate_with(self, windows):
        fake = FakeWin32Gui(windows)
        with mock.patch.object(auto_clicker, "win32gui", fake):
            return self.clicker._enumerate_candidate_windows()

    def find_with(self, windows):
        fake = FakeWin32Gui(windows)
        with mock.patch.object(auto_clicker, "win32gui", fake):
            return self.clicker._find_main_window()

    def test_keyword_matches_non_dialog_window(self):
        self.clicker.config["window_keyword"] = "NBA2K"
        windows = {101: ("NBA2K Launcher v3.1", "Chrome_WidgetWin_1", True)}
        self.assertEqual(self.find_with(windows), 101)

    def test_keyword_preferred_over_hardcoded_title(self):
        self.clicker.config["window_keyword"] = "NBA2K"
        windows = {
            101: ("按键精灵 2014", "LegacyWindow", True),
            202: ("NBA2K Launcher", "Chrome_WidgetWin_1", True),
        }
        candidates = self.enumerate_with(windows)
        priorities = {candidate[1]: candidate[0] for candidate in candidates}
        self.assertLess(priorities[202], priorities[101])
        self.assertEqual(self.find_with(windows), 202)

    def test_no_keyword_keeps_fallback_heuristics(self):
        windows = {
            101: ("按键精灵 2014", "LegacyWindow", True),
            202: ("Anjian Script", "OtherWindow", True),
            303: ("", "#32770", True),
        }
        self.child_counts[303] = 60
        candidates = self.enumerate_with(windows)
        self.assertEqual({candidate[1] for candidate in candidates}, {101, 202, 303})
        self.assertEqual(self.clicker._select_main_window(candidates)[0], 202)

    def test_keyword_configured_but_unmatched_falls_back(self):
        self.clicker.config["window_keyword"] = "OLDNAME"
        self.child_counts[303] = 60
        windows = {303: ("New Script Window", "#32770", True)}
        self.assertEqual(self.find_with(windows), 303)

    def test_keyword_is_case_insensitive_and_ignores_invisible(self):
        self.clicker.config["window_keyword"] = "nba2k"
        windows = {
            101: ("NBA2K Launcher", "Chrome_WidgetWin_1", True),
            202: ("nba2k Hidden", "OtherWindow", False),
        }
        candidates = self.enumerate_with(windows)
        self.assertEqual([candidate[1] for candidate in candidates], [101])

    def test_own_config_window_excluded_even_with_keyword(self):
        self.clicker.config["window_keyword"] = "NBA2K"
        windows = {
            101: ("NBA2K 按键精灵自动启动配置", "OtherWindow", True),
            202: ("NBA2K Helper", "TkTopLevelWidget", True),
        }
        self.assertEqual(self.enumerate_with(windows), [])
        self.assertIsNone(self.find_with(windows))


if __name__ == "__main__":
    unittest.main()
