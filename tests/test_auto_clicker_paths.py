import os
import tempfile
import unittest

try:
    import win32gui  # noqa: F401
except ImportError:
    raise unittest.SkipTest("需要 Windows pywin32")

import app_config
from auto_clicker import AnjianAutoClicker


class AutoClickerPathTests(unittest.TestCase):
    def test_config_path_does_not_follow_cwd(self):
        original = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            clicker = None
            try:
                clicker = AnjianAutoClicker()
            finally:
                if clicker is not None:
                    for handler in list(clicker.logger.handlers):
                        handler.close()
                        clicker.logger.removeHandler(handler)
                os.chdir(original)
        self.assertIsNotNone(clicker)
        self.assertEqual(clicker.config_file, app_config.get_config_path())
        self.assertTrue(os.path.isabs(clicker.config_file))
