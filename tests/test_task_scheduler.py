import os
from types import SimpleNamespace
import unittest
import uuid
import xml.etree.ElementTree as ET

import task_scheduler


class TaskSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.info = {
            "command": r"C:\Tools & Apps\pythonw.exe",
            "arguments": '"C:\\a \\"quoted\\" path\\auto_clicker.py"',
            "workdir": r"C:\Work <NBA> & Tools",
        }

    def test_xml_escapes_and_principal_reference(self):
        root = ET.fromstring(task_scheduler.build_task_xml(self.info))
        namespace = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
        actions = root.find("t:Actions", namespace)
        principal = root.find("t:Principals/t:Principal", namespace)
        self.assertIsNotNone(actions)
        self.assertIsNotNone(principal)
        self.assertEqual(actions.attrib["Context"], principal.attrib["id"])
        self.assertEqual(principal.findtext("t:LogonType", namespaces=namespace), "InteractiveToken")
        self.assertEqual(principal.findtext("t:RunLevel", namespaces=namespace), "HighestAvailable")
        exec_node = actions.find("t:Exec", namespace)
        self.assertEqual(exec_node.findtext("t:Command", namespaces=namespace), self.info["command"])
        self.assertEqual(exec_node.findtext("t:Arguments", namespaces=namespace), self.info["arguments"])
        self.assertEqual(exec_node.findtext("t:WorkingDirectory", namespaces=namespace), self.info["workdir"])

    def test_create_invokes_exact_command_and_cleans_temp(self):
        observed = {}

        def runner(args, **kwargs):
            observed["args"] = args
            observed["kwargs"] = kwargs
            observed["path"] = args[-2]
            self.assertTrue(os.path.isfile(observed["path"]))
            with open(observed["path"], "r", encoding="utf-16") as source:
                observed["xml"] = source.read()
            return SimpleNamespace(returncode=0, stderr="")

        result = task_scheduler.create_autostart_task(self.info, runner=runner)
        self.assertTrue(result.ok)
        self.assertEqual(
            observed["args"],
            ["schtasks", "/Create", "/TN", task_scheduler.TASK_NAME,
             "/XML", observed["path"], "/F"],
        )
        self.assertEqual(observed["kwargs"], {
            "capture_output": True, "text": True,
            "encoding": "gbk", "errors": "replace",
        })
        self.assertEqual(observed["xml"], task_scheduler.build_task_xml(self.info))
        self.assertFalse(os.path.exists(observed["path"]))

    def test_create_failure_and_oserror_clean_temp(self):
        paths = []

        def failing_runner(args, **kwargs):
            paths.append(args[-2])
            return SimpleNamespace(returncode=1, stderr="拒绝访问")

        result = task_scheduler.create_autostart_task(self.info, runner=failing_runner)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "error")
        self.assertIn("拒绝访问", result.message)
        self.assertFalse(os.path.exists(paths[-1]))

        def raising_runner(args, **kwargs):
            paths.append(args[-2])
            raise OSError("missing schtasks")

        result = task_scheduler.create_autostart_task(self.info, runner=raising_runner)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "error")
        self.assertIn("missing schtasks", result.message)
        self.assertFalse(os.path.exists(paths[-1]))

    def test_delete_status_mapping_and_exact_command(self):
        calls = []

        def runner_for(returncode, stderr):
            def runner(args, **kwargs):
                calls.append((args, kwargs))
                return SimpleNamespace(returncode=returncode, stderr=stderr)
            return runner

        ok = task_scheduler.delete_autostart_task(runner=runner_for(0, ""))
        chinese = task_scheduler.delete_autostart_task(runner=runner_for(1, "找不到指定任务"))
        english = task_scheduler.delete_autostart_task(runner=runner_for(1, "Cannot find task"))
        error = task_scheduler.delete_autostart_task(runner=runner_for(1, "拒绝访问"))
        self.assertTrue(ok.ok)
        self.assertEqual(chinese.status, "not_found")
        self.assertEqual(english.status, "not_found")
        self.assertEqual(error.status, "error")
        expected = ["schtasks", "/Delete", "/TN", task_scheduler.TASK_NAME, "/F"]
        expected_kwargs = {
            "capture_output": True, "text": True,
            "encoding": "gbk", "errors": "replace",
        }
        for args, kwargs in calls:
            self.assertEqual(args, expected)
            self.assertEqual(kwargs, expected_kwargs)

        raised = task_scheduler.delete_autostart_task(
            runner=lambda *args, **kwargs: (_ for _ in ()).throw(OSError("missing schtasks"))
        )
        self.assertFalse(raised.ok)
        self.assertEqual(raised.status, "error")

    @unittest.skipUnless(
        os.name == "nt" and os.environ.get("ANJIAN_SCHTASKS_IT") == "1",
        "需要 Windows 且显式启用 ANJIAN_SCHTASKS_IT=1",
    )
    def test_windows_schtasks_round_trip(self):
        task_name = f"AnjianAutoStartIT-{uuid.uuid4().hex}"
        info = {
            "command": os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe"),
            "arguments": "/c exit 0",
            "workdir": os.environ.get("SystemRoot", r"C:\Windows"),
        }
        try:
            created = task_scheduler.create_autostart_task(info, task_name=task_name)
            self.assertTrue(created.ok, created.message)
            deleted = task_scheduler.delete_autostart_task(task_name=task_name)
            self.assertTrue(deleted.ok, deleted.message)
        finally:
            task_scheduler.delete_autostart_task(task_name=task_name)


if __name__ == "__main__":
    unittest.main()
