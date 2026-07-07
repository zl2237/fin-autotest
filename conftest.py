import json
import os
import shutil
from pathlib import Path

import pytest

from utils.logger import log
from core.http_client import http
from config.settings import LOGIN_URL, USERNAME, PASSWORD, TOKEN_FIELD, TOKEN_TYPE, AUTH_HEADER

_allure_actual_dir = None


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """测试运行前按进程隔离 allure-results 目录，避免多人共用时互相删除。"""
    global _allure_actual_dir
    import datetime
    pid_suffix = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    allure_dir = Path(f"report/allure-results-{pid_suffix}")
    if allure_dir.exists():
        shutil.rmtree(allure_dir)
    allure_dir.mkdir(parents=True, exist_ok=True)
    config.option.alluredir = str(allure_dir)
    _allure_actual_dir = allure_dir


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """兜底：如果 allure 实际写到了默认目录，移到隔离目录。"""
    global _allure_actual_dir
    if _allure_actual_dir is None:
        return

    default_dir = Path("report/allure-results")
    actual_dir = None

    if default_dir.exists() and any(default_dir.iterdir()):
        actual_dir = default_dir
    elif _allure_actual_dir.exists() and any(_allure_actual_dir.iterdir()):
        actual_dir = _allure_actual_dir

    if actual_dir and actual_dir != _allure_actual_dir:
        _allure_actual_dir.mkdir(parents=True, exist_ok=True)
        for item in actual_dir.iterdir():
            dest = _allure_actual_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))


def get_nested_value(data, key: str):
    if not isinstance(data, dict):
        return None
    keys = key.split(".")
    result = data
    for k in keys:
        if not isinstance(result, dict):
            return None
        result = result.get(k)
        if result is None:
            return None
    return result


@pytest.fixture(scope="session", autouse=True)
def global_login():
    log.info("===== 全局登录开始（仅一次） =====")

    login_data = {"username": USERNAME, "password": PASSWORD}
    resp = http.post(
        LOGIN_URL,
        json=login_data,
        headers={"Authorization": "lele_auth"},
    )

    assert resp.status_code == 200, "登录接口请求失败"
    resp_json = resp.json()

    token = get_nested_value(resp_json, TOKEN_FIELD)
    assert token is not None, f"无法提取token：{TOKEN_FIELD}"

    auth_value = f"{TOKEN_TYPE} {token}" if TOKEN_TYPE else token
    http.session.headers.update({AUTH_HEADER: auth_value})
    log.info("✅ 登录成功，token已注入session")

    yield

    log.info("===== 全局登录fixture结束 =====")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    results = {"passed": [], "failed": [], "skipped": []}

    for report in terminalreporter.stats.get("passed", []):
        results["passed"].append(_format_case(report))

    for report in terminalreporter.stats.get("failed", []):
        results["failed"].append(_format_case(report))

    for report in terminalreporter.stats.get("skipped", []):
        results["skipped"].append(_format_case(report))

    terminalreporter.write_sep("=", "测试结果汇总", bold=True, green=True)

    terminalreporter.write_line("")
    terminalreporter.write_line(f"  ✅ Passed : {len(results['passed'])}")
    terminalreporter.write_line(f"  ❌ Failed : {len(results['failed'])}")
    terminalreporter.write_line(f"  ⏭️  Skipped: {len(results['skipped'])}")
    terminalreporter.write_line("")

    if results["failed"]:
        terminalreporter.write_sep("-", "失败用例详情", bold=True, red=True)
        for item in results["failed"]:
            terminalreporter.write_line(f"  ❌ {item['name']}")
            terminalreporter.write_line(f"     标记 : {item['markers']}")
            terminalreporter.write_line(f"     原因 : {item['message']}")
            terminalreporter.write_line("")

    report_dir = Path("report")
    report_dir.mkdir(exist_ok=True)

    target_dir = _allure_actual_dir if _allure_actual_dir is not None else Path("report/allure-results")
    summary_path = target_dir / "test_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    for failed in results["failed"]:
        errors.append({"name": failed["name"], "message": failed["message"]})

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(results["passed"]) + len(results["failed"]) + len(results["skipped"]),
            "passed": len(results["passed"]),
            "failed": len(results["failed"]),
            "skipped": len(results["skipped"]),
            "details": results,
            "errors": errors,
        }, f, ensure_ascii=False, indent=2)

    terminalreporter.write_line(f"📄 报告已生成: {summary_path}")
    terminalreporter.write_line("")


def _format_case(report):
    markers = [m for m in report.keywords if not m.startswith("_")] if isinstance(report.keywords, dict) else []
    message = ""
    if hasattr(report.longrepr, "message"):
        message = report.longrepr.message
    elif hasattr(report.longrepr, "reprcrash"):
        message = report.longrepr.reprcrash.message
    elif isinstance(report.longrepr, str):
        message = report.longrepr

    message = message.strip().replace("\n", " ")[:300]

    return {
        "name": f"{report.nodeid}",
        "markers": markers or ["无标记"],
        "message": message or "无",
    }
