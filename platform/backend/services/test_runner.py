import os
import subprocess
import sys
import threading
from pathlib import Path

from services.store import store


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
REPORT_DIR = PROJECT_ROOT / "report"

# 用后端自身的 Python 解释器，保证插件一致性
PYTHON_EXE = sys.executable


def _write_env(payload: dict):
    lines = [
        f"BASE_URL={payload.get('base_url', '').strip()}",
        f"LOGIN_URL={payload.get('login_url', '').strip()}",
        f"USERNAME={payload.get('test_username', '').strip()}",
        f"PASSWORD={payload.get('test_password', '').strip()}",
        f"TOKEN_FIELD={payload.get('token_field', 'data.token').strip()}",
        f"TOKEN_TYPE={payload.get('token_type', '').strip()}",
        f"AUTH_HEADER={payload.get('auth_header', 'Authorization').strip()}",
        f"ORDER_CREATE_ID={payload.get('order_create_id', '').strip()}",
        f"ORDER_PREFIX={payload.get('order_prefix', 'lele').strip()}",
        f"LOOP_COUNT={payload.get('loop_count', 1)}",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


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
        # 先删旧 .env，再写新值（避免 pytest 读旧配置）
        try:
            ENV_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        _write_env(payload)
        loop_count = payload.get("loop_count", 1)
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

            if process.returncode == 0:
                summary_path = REPORT_DIR / "allure-results" / "test_summary.json"
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
        finally:
            try:
                ENV_FILE.unlink(missing_ok=True)
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True).start()
