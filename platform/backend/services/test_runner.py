import os
import re
import subprocess
import sys
import threading
from pathlib import Path

from services.store import store


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPORT_DIR = PROJECT_ROOT / "report"

# 用后端自身的 Python 解释器，保证插件一致性
PYTHON_EXE = sys.executable


def _prepare_env(run_id: str, payload: dict):
    """根据 payload 生成独立的子进程环境变量，不写回项目根目录的 .env。"""
    env = os.environ.copy()
    # 强制子进程 stdout/stderr 输出 UTF-8，解决 Windows 控制台默认 GBK 编码导致的中文乱码
    env["PYTHONIOENCODING"] = "utf-8"
    env["BASE_URL"] = payload.get("base_url", "").strip()
    env["LOGIN_URL"] = payload.get("login_url", "").strip()
    env["USERNAME"] = payload.get("test_username", "").strip()
    env["PASSWORD"] = payload.get("test_password", "").strip()
    env["TOKEN_FIELD"] = payload.get("token_field", "data.token").strip()
    env["TOKEN_TYPE"] = payload.get("token_type", "").strip()
    env["AUTH_HEADER"] = payload.get("auth_header", "Authorization").strip()
    env["ORDER_CREATE_ID"] = payload.get("order_create_id", "").strip()
    env["ORDER_PREFIX"] = payload.get("order_prefix", "lele").strip()
    env["LOOP_COUNT"] = str(payload.get("loop_count", 1))
    env["TEST_ENV"] = payload.get("test_env", "").strip()
    env["ALLURE_RESULT_DIR"] = str(REPORT_DIR / f"allure-results-{run_id}")
    return env


def _parse_summary_from_logs(logs: list) -> dict:
    """从 pytest 日志中解析 passed/failed/skipped 数量"""
    pattern = re.compile(
        r"(\d+)\s+passed|[,\s]+(\d+)\s+failed|[,\s]+(\d+)\s+skipped"
    )
    summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
    for line in logs:
        m = pattern.search(line)
        if m:
            summary["passed"] += int(m.group(1)) if m.group(1) else 0
            summary["failed"] += int(m.group(2)) if m.group(2) else 0
            summary["skipped"] += int(m.group(3)) if m.group(3) else 0
    summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"]
    return summary


def run_test(run_id: str, marker: str, payload: dict):
    def _worker():
        subprocess_env = _prepare_env(run_id, payload)
        loop_count = int(payload.get("loop_count", 1))

        try:
            cmd = [
                PYTHON_EXE, "-m", "pytest",
                "-m", marker,
                "-v",
                "--tb=short",
            ]
            if loop_count > 1:
                cmd.append("--count=" + str(loop_count))
            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                env=subprocess_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
            )
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                line = line.rstrip("\n")
                store.append_log(run_id, line)
            process.wait()

            summary_path = REPORT_DIR / f"allure-results-{run_id}" / "test_summary.json"
            if process.returncode == 0:
                if summary_path.exists():
                    import json as _json
                    result = {
                        "status": "success",
                        "summary": _json.loads(summary_path.read_text(encoding="utf-8")),
                    }
                else:
                    logs_snapshot = store.get(run_id).logs if store.get(run_id) else []
                    result = {
                        "status": "success",
                        "summary": _parse_summary_from_logs(logs_snapshot),
                    }
                store.complete(run_id, result)
            else:
                logs_snapshot = store.get(run_id).logs if store.get(run_id) else []
                result = {
                    "status": "failed",
                    "error": f"pytest 退出码: {process.returncode}",
                    "summary": _parse_summary_from_logs(logs_snapshot),
                }
                store.complete(run_id, result)
        except Exception as e:
            store.fail(run_id, str(e))

    threading.Thread(target=_worker, daemon=True).start()
