#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitLab CI 企微通知脚本（企业微信群机器人）

参考飞书/阿里/腾讯内部通知风格，包含：
- 流水线基本信息
- 测试结果统计（通过/失败/跳过）
- 失败用例明细（最多 5 条，含错误信息）
- 流水线链接
- @ 提及（可选）

使用方式：
1. 在 GitLab 项目 Settings > CI/CD > Variables 中配置：
   - WECOM_WEBHOOK_URL：企业微信群机器人的 webhook 地址（完整 URL，含 key）
   - 可选：WECOM_MENTIONED_LIST：被提及的用户手机号列表，逗号分隔，如 "13800000000,13900000000"
"""

import json
import os
import sys
import urllib.request
import urllib.error


def get_env(name, default=""):
    return os.environ.get(name, default)


def read_test_summary():
    """读取 conftest.py 写入的测试摘要"""
    summary_path = "report/allure-results/test_summary.json"
    if not os.path.exists(summary_path):
        return None
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def truncate(text, max_len=120):
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def truncate_commit(msg, max_len=60):
    if not msg:
        return ""
    first_line = msg.split("\n")[0].strip()
    if len(first_line) > max_len:
        return first_line[: max_len - 3] + "..."
    return first_line


def build_message():
    pipeline_id = get_env("CI_PIPELINE_ID", "N/A")
    pipeline_url = get_env("CI_PIPELINE_URL", "")
    job_url = get_env("CI_JOB_URL", "")
    branch = get_env("CI_COMMIT_BRANCH", get_env("CI_COMMIT_REF_NAME", "N/A"))
    commit_sha = get_env("CI_COMMIT_SHORT_SHA", get_env("CI_COMMIT_SHA", "N/A"))[:8]
    commit_msg = get_env("CI_COMMIT_MESSAGE", "N/A")
    job_name = get_env("CI_JOB_NAME", "N/A")
    runner = get_env("CI_RUNNER_DESCRIPTION", "N/A")
    project_url = get_env("CI_PROJECT_URL", "")
    project_name = get_env("CI_PROJECT_NAME", "")

    commit_msg_short = truncate_commit(commit_msg, 60)

    summary = read_test_summary()
    has_summary = summary is not None

    job_status = get_env("CI_JOB_STATUS", "").lower()
    pipeline_status = get_env("CI_PIPELINE_STATUS", "").lower()
    ci_status = job_status or pipeline_status or "unknown"

    if summary is None:
        if ci_status in ("success", ""):
            overall_status = "success"
        else:
            overall_status = ci_status
    elif summary.get("failed", 0) > 0:
        overall_status = "failed"
    else:
        overall_status = ci_status

    status_icon = {"success": "✅", "failed": "❌", "canceled": "⚠️", "warning": "⚠️"}.get(
        overall_status, "❓"
    )
    status_label = {
        "success": "成功",
        "failed": "失败",
        "canceled": "已取消",
        "warning": "警告",
    }.get(overall_status, overall_status)

    lines = []
    lines.append(f"## {status_icon} 自动化测试报告")
    lines.append("")

    if pipeline_url:
        pipeline_link = f"[{pipeline_id}]({pipeline_url})"
    else:
        pipeline_link = str(pipeline_id)

    job_link = f"[{job_name}]({job_url})" if job_url else job_name

    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| **项目** | {project_name} |")
    lines.append(f"| **分支** | `{branch}` |")
    lines.append(f"| **提交** | `{commit_sha}` {commit_msg_short} |")
    lines.append(f"| **流水线** | {pipeline_link} |")
    lines.append(f"| **任务** | {job_link} |")
    lines.append(f"| **Runner** | {runner} |")
    lines.append("")

    if has_summary:
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        pass_rate = f"{passed / total * 100:.1f}%" if total > 0 else "N/A"

        lines.append(f"### 📊 测试结果")
        lines.append(f"- **总计**：{total}")
        lines.append(f"- **通过**：{passed} ✅")
        lines.append(f"- **失败**：{failed} ❌")
        lines.append(f"- **跳过**：{skipped} ⏭️")
        lines.append(f"- **通过率**：{pass_rate}")
        lines.append("")

        if summary.get("errors"):
            lines.append("### ❌ 失败用例明细")
            lines.append("")
            for idx, err in enumerate(summary["errors"][:5], 1):
                name = err.get("name", "Unknown")
                message = truncate(err.get("message", ""), 300)
                lines.append(f"{idx}. **`{name}`**")
                lines.append(f"   > {message}")
                lines.append("")
    else:
        lines.append("> ⚠️ 未找到测试结果摘要，可能测试阶段未正常执行。")
        lines.append("")

    links = []
    if pipeline_url:
        links.append(f"[查看流水线]({pipeline_url})")
    if project_url:
        links.append(f"[查看项目]({project_url})")
    if links:
        lines.append(" ".join(links))
        lines.append("")

    mentioned_list = get_env("WECOM_MENTIONED_LIST", "").strip()
    if mentioned_list:
        users = [u.strip() for u in mentioned_list.split(",") if u.strip()]
        mentions = "".join([f"@<font color=\"comment\">{u}</font> " for u in users])
        lines.append(f"{mentions}")
        lines.append("")

    return {
        "msgtype": "markdown",
        "markdown": {
            "content": "\n".join(lines)
        }
    }


def send_notification(webhook_url, payload):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, data=data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return -1, str(e)


def main():
    webhook_url = get_env("WECOM_WEBHOOK_URL", "").strip()

    if not webhook_url:
        print("⚠️ 未配置 WECOM_WEBHOOK_URL 环境变量，跳过企微通知")
        sys.exit(0)

    if not webhook_url.startswith("https://"):
        print(f"⚠️ WECOM_WEBHOOK_URL 格式异常：{webhook_url}")
        sys.exit(0)

    payload = build_message()
    status, body = send_notification(webhook_url, payload)

    if status == 200:
        try:
            result = json.loads(body)
            if result.get("errcode") == 0:
                print("✅ 企微通知发送成功")
                sys.exit(0)
            else:
                print(f"❌ 发送失败：{result}")
                sys.exit(1)
        except json.JSONDecodeError:
            print(f"⚠️ 响应解析失败：{body}")
            sys.exit(1)
    else:
        print(f"❌ 请求异常：HTTP {status}, {body}")
        sys.exit(1)


if __name__ == "__main__":
    main()
