import json
from pathlib import Path

import pytest

from utils.logger import log
from core.http_client import http
from config.settings import LOGIN_URL, USERNAME, PASSWORD, TOKEN_FIELD, TOKEN_TYPE, AUTH_HEADER


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


def pytest_sessionfinish(session, exitstatus):
    allure_dir = session.config.getoption("--alluredir")
    if not allure_dir:
        return

    allure_path = Path(allure_dir)
    if not allure_path.exists() or not any(allure_path.iterdir()):
        return

    summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": []}

    for item in session.items:
        if hasattr(item, "rep_call"):
            rep = item.rep_call
            summary["total"] += 1
            if rep.passed:
                summary["passed"] += 1
            elif rep.failed:
                summary["failed"] += 1
                summary["errors"].append({
                    "name": item.name,
                    "message": str(rep.longrepr) if rep.longrepr else ""
                })
            elif rep.skipped:
                summary["skipped"] += 1

    summary_path = Path(allure_dir) / "test_summary.json"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        log.info(f"✅ 测试摘要已写入: {summary_path}")
    except Exception as e:
        log.warning(f"⚠️ 写入测试摘要失败: {e}")
