#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitLab CI 企微通知脚本（企业微信群机器人）

格式要求：
- lint pass/fail：代码检查环节（lint）pass / fail
- smoke_test pass/fail：order1新建 pass / fail，失败原因：XXX
- deploy pass：服务已部署，请访问 http://172.16.18.55:10086/ 获取服务
- deploy fail：部署失败，请检查流水线日志

所有阶段无论通过与否都必须通知。
"""

import json
import os
import sys
import urllib.request
import urllib.error


def get_env(name, default=""):
    return os.environ.get(name, default)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def read_lint_status():
    """读取 lint 状态：{status, message}"""
    return read_json("report/lint_status.json", {"status": "unknown", "message": ""})


def read_smoke_test_status():
    """读取 smoke_test 状态：{status, results: [{name, status, message}]}"""
    return read_json("report/smoke_test_status.json", {"status": "unknown", "results": []})


def read_deploy_status():
    """读取 deploy 状态：{status, message}"""
    return read_json("report/deploy_status.json", {"status": "unknown", "message": ""})


def truncate(text, max_len=300):
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
    project_name = get_env("CI_PROJECT_NAME", "PR Study")
    ci_job_status = get_env("CI_JOB_STATUS", "").lower()

    commit_msg_short = truncate_commit(commit_msg, 60)

    # 读取三个阶段状态
    lint = read_lint_status()
    smoke = read_smoke_test_status()
    deploy = read_deploy_status()

    # 前端展示 emoji
    icon_map = {
        "pass": "✅",
        "fail": "❌",
        "skip": "⏭️",
        "unknown": "⚠️",
    }

    # 最终流水线状态
    all_pass = (
        lint.get("status") == "pass"
        and smoke.get("status") == "pass"
        and deploy.get("status") == "pass"
    )
    any_fail = (
        lint.get("status") == "fail"
        or smoke.get("status") == "fail"
        or deploy.get("status") == "fail"
    )
    if ci_job_status == "canceled":
        final_status = "canceled"
    elif all_pass:
        final_status = "success"
    elif any_fail:
        final_status = "failed"
    else:
        final_status = "warning"

    status_icon = icon_map.get(final_status, "❓")
    status_label = {
        "success": "全部成功",
        "failed": "存在失败",
        "canceled": "已取消",
        "warning": "部分异常",
    }.get(final_status, final_status)

    lines = []
    lines.append(f"## {status_icon} 流水线通知 #{pipeline_id}  [{status_label}]")
    lines.append("")

    # 基本信息
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| **项目** | {project_name} |")
    lines.append(f"| **分支** | `{branch}` |")
    lines.append(f"| **提交** | `{commit_sha}` {commit_msg_short} |")
    if pipeline_url:
        lines.append(f"| **流水线** | [{pipeline_id}]({pipeline_url}) |")
    lines.append("")

    # ---- 1. lint ----
    lint_status = lint.get("status", "unknown")
    lint_icon = icon_map.get(lint_status, "⚠️")
    lint_msg = lint.get("message", "")
    if lint_status == "pass":
        lines.append(f"{lint_icon} **lint**  {lint_msg}")
    elif lint_status == "fail":
        lines.append(f"{lint_icon} **lint**  {lint_msg}")
    else:
        lines.append(f"{lint_icon} **lint**  未获取到 lint 执行结果")
    lines.append("")

    # ---- 2. smoke_test ----
    smoke_status = smoke.get("status", "unknown")
    smoke_icon = icon_map.get(smoke_status, "⚠️")
    results = smoke.get("results", [])
    if results:
        for r in results:
            name = r.get("name", "unknown")
            rs = r.get("status", "unknown")
            ri = icon_map.get(rs, "⚠️")
            rm = r.get("message", "")
            # 提取用例名（取最后一段，如 test_order_new -> order_new）
            marker = name.split("/")[-1].replace("test_", "").replace("_", "")
            label = marker if marker else name
            if rs == "pass":
                lines.append(f"{ri} **{label}**  {label} pass")
            elif rs == "fail":
                reason = f"，失败原因：{truncate(rm, 300)}" if rm else ""
                lines.append(f"{ri} **{label}**  {label} fail{reason}")
            elif rs == "skip":
                lines.append(f"{ri} **{label}**  {label} skip")
    elif smoke_status == "unknown":
        lines.append(f"{smoke_icon} **smoke_test**  未获取到测试结果")
    else:
        lines.append(f"{smoke_icon} **smoke_test**  smoke_test {smoke_status}")
    lines.append("")

    # ---- 3. deploy ----
    deploy_status = deploy.get("status", "unknown")
    deploy_icon = icon_map.get(deploy_status, "⚠️")
    deploy_msg = deploy.get("message", "")
    if deploy_status == "pass":
        lines.append(f"{deploy_icon} **{deploy_msg}**")
    elif deploy_status == "fail":
        lines.append(f"{deploy_icon} **{deploy_msg}**")
    elif deploy_status == "unknown":
        lines.append(f"{deploy_icon} **deploy**  未获取到部署结果")
    else:
        lines.append(f"{deploy_icon} **deploy**  部署状态：{deploy_status}")
    lines.append("")

    # 链接
    links = []
    if pipeline_url:
        links.append(f"[查看流水线]({pipeline_url})")
    links.append(f"[服务地址](http://172.16.18.55:10086/)")
    if links:
        lines.append(" | ".join(links))

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
        print("⚠️ 未配置 WECOM_WEBHOOK_URL，跳过企微通知")
        sys.exit(0)

    if not webhook_url.startswith("https://"):
        print(f"⚠️ WECOM_WEBHOOK_URL 格式异常：{webhook_url}")
        sys.exit(0)

    # 无论状态如何，都发送通知
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
