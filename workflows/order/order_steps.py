"""
订单基础步骤：新建 → 分发 / 暂存 / 提交 / 生成子订单
"""
import time
from typing import Any, Dict

import allure

from api.order import OrderApi
from utils import generate_bl_no


def create_and_distribute(bl_no: str = None) -> Dict[str, Any]:
    """
    新建 + 分发（不含暂存/提交）

    Args:
        bl_no: 提单号，默认自动生成

    Returns:
        {
            "bl_no": str,
            "create_resp": Response,
            "create_data": dict,
            "create_order": dict,        # 按提单号查询到的订单
            "distribute_resp": Response,
            "distribute_data": dict,
        }
    """
    if bl_no is None:
        bl_no = generate_bl_no()

    result = {"bl_no": bl_no, "steps": []}

    with allure.step(f"Step1: 新建订单, bl_no={bl_no}"):
        create_resp = OrderApi.add_order(bl_no=bl_no)
        create_data = create_resp.json()
        result["create_resp"] = create_resp
        result["create_data"] = create_data
        result["steps"].append({"name": "新建订单", "code": create_data.get("code"), "msg": create_data.get("msg")})
        assert create_resp.status_code == 200, f"HTTP状态码异常: {create_resp.status_code}"
        assert create_data.get("code") == 200, f"新建失败: {create_data}"

    time.sleep(1)

    with allure.step("Step2: 按提单号查询获取 order_id"):
        create_order = OrderApi.get_order_by_bl_no(bl_no)
        result["create_order"] = create_order
        result["steps"].append({"name": "按提单号查询", "found": bool(create_order), "order_id": create_order.get("order_id")})
        if not create_order:
            raise AssertionError(f"按提单号 {bl_no} 查询不到订单，无法继续流程")

    with allure.step("Step3: 分发订单"):
        distribute_resp = OrderApi.distribute_order(create_order, bl_no=bl_no)
        distribute_data = distribute_resp.json()
        result["distribute_resp"] = distribute_resp
        result["distribute_data"] = distribute_data
        result["steps"].append({"name": "分发订单", "code": distribute_data.get("code"), "msg": distribute_data.get("msg")})
        assert distribute_resp.status_code == 200, "HTTP状态码异常"

    return result


def stash(order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
    """
    暂存订单（与提交共用接口，status=1）

    Args:
        order_info: 订单信息（需包含 order_id、order_no 等）
        bl_no: 提单号

    Returns:
        {
            "bl_no": str,
            "stash_resp": Response,
            "stash_data": dict,
        }
    """
    if bl_no is None:
        bl_no = order_info.get("bl_no") or generate_bl_no()

    result = {"bl_no": bl_no, "steps": []}

    with allure.step("暂存订单"):
        stash_resp = OrderApi.stash_order(order_info, bl_no=bl_no)
        stash_data = stash_resp.json()
        result["stash_resp"] = stash_resp
        result["stash_data"] = stash_data
        result["steps"].append({"name": "暂存订单", "code": stash_data.get("code"), "msg": stash_data.get("msg")})

    return result


def submit(order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
    """
    提交订单

    Args:
        order_info: 订单信息（需包含 order_id、order_no 等，通常来自 create_and_distribute）
        bl_no: 提单号

    Returns:
        {
            "bl_no": str,
            "submit_resp": Response,
            "submit_data": dict,
        }
    """
    if bl_no is None:
        bl_no = order_info.get("bl_no") or generate_bl_no()

    result = {"bl_no": bl_no, "steps": []}

    with allure.step("提交订单"):
        submit_resp = OrderApi.submit_order(order_info, bl_no=bl_no)
        submit_data = submit_resp.json()
        result["submit_resp"] = submit_resp
        result["submit_data"] = submit_data
        result["steps"].append({"name": "提交订单", "code": submit_data.get("code"), "msg": submit_data.get("msg")})

    return result


def generate_sub_order(order_id: str) -> Dict[str, Any]:
    """
    生成子订单

    Args:
        order_id: 订单ID，来源于链路中使用的 order_id

    Returns:
        {
            "order_id": str,
            "generate_sub_resp": Response,
            "generate_sub_data": dict,
        }
    """
    result = {"order_id": order_id, "steps": []}

    with allure.step("生成子订单"):
        generate_sub_resp = OrderApi.generate_sub_order(order_id)
        generate_sub_data = generate_sub_resp.json()
        result["generate_sub_resp"] = generate_sub_resp
        result["generate_sub_data"] = generate_sub_data
        result["steps"].append({
            "name": "生成子订单",
            "code": generate_sub_data.get("code"),
            "msg": generate_sub_data.get("msg")
        })

    return result
