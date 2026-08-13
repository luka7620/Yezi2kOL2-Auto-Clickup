"""Windows 任务计划程序能力（不依赖 GUI；命令执行器可注入）。"""
from dataclasses import dataclass
import html
import os
import subprocess
import tempfile


TASK_NAME = "AnjianAutoStart"


@dataclass
class SchedulerResult:
    ok: bool
    status: str
    message: str


def build_task_xml(info: dict) -> str:
    escape = lambda value: html.escape(value, quote=True)
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>按键精灵自动启动脚本</Description></RegistrationInfo>
  <Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle><WakeToRun>false</WakeToRun><ExecutionTimeLimit>PT1H</ExecutionTimeLimit><Priority>7</Priority>
  </Settings>
  <Actions Context="Author"><Exec>
    <Command>{escape(info["command"])}</Command><Arguments>{escape(info["arguments"])}</Arguments>
    <WorkingDirectory>{escape(info["workdir"])}</WorkingDirectory>
  </Exec></Actions>
</Task>'''


def _run_kwargs() -> dict:
    return {
        "capture_output": True,
        "text": True,
        "encoding": "gbk",
        "errors": "replace",
    }


def create_autostart_task(
    info: dict,
    runner=subprocess.run,
    task_name: str = TASK_NAME,
) -> SchedulerResult:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-16", suffix=".xml", delete=False
        ) as temp_file:
            temp_file.write(build_task_xml(info))
            temp_path = temp_file.name
        result = runner(
            ["schtasks", "/Create", "/TN", task_name, "/XML", temp_path, "/F"],
            **_run_kwargs(),
        )
        if result.returncode != 0:
            return SchedulerResult(False, "error", result.stderr or "")
        return SchedulerResult(True, "ok", "开机自启设置成功")
    except OSError as error:
        return SchedulerResult(False, "error", f"设置开机自启失败：{error}")
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


def delete_autostart_task(
    runner=subprocess.run,
    task_name: str = TASK_NAME,
) -> SchedulerResult:
    try:
        result = runner(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            **_run_kwargs(),
        )
    except OSError as error:
        return SchedulerResult(False, "error", f"取消开机自启失败：{error}")
    if result.returncode == 0:
        return SchedulerResult(True, "ok", "已取消开机自启")
    stderr = result.stderr or ""
    if "找不到" in stderr or "cannot find" in stderr.lower():
        return SchedulerResult(False, "not_found", stderr)
    return SchedulerResult(False, "error", stderr)
