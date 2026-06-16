"""
费用相关步骤：
- record_fee                  录费用（订舱费用），可选自动跑资产推送审批
- record_generate_fee_notice  生成费用通知单
- record_generate_fee_confirm 生成费用确认单
"""
from typing import Any, Dict, List

import allure

from api.audit_api import AuditApi
from api.order import OrderApi
from core.http_client import http
from data.order_data import BookRealAmountData


def record_fee(
    order_id: str,
    fee_configs: List[Dict[str, Any]],
    audit_after_fee: bool = False,
) -> Dict[str, Any]:
    """
    录费用（订舱费用接口），按配置列表逐条调用。
    录完费用后可选择自动执行资产推送审批（audit_after_fee=True）。

    Args:
        order_id   : 订单ID
        fee_configs: 费用配置列表，每条配置支持：
                       to_customer_fees / to_supplier_fees
        audit_after_fee: 是否在录完费用后自动执行 assetPush 审批
    """
    if fee_configs is None:
        fee_configs = []

    result = {
        "order_id": order_id,
        "results": [],
        "steps": [],
    }

    for i, config in enumerate(fee_configs):
        payload = BookRealAmountData.get_payload(
            order_id=order_id,
            to_customer_fees=config.get("to_customer_fees"),
            to_supplier_fees=config.get("to_supplier_fees"),
        )
        resp = http.post(OrderApi.BOOK_REAL_AMOUNT_URL, json=payload)
        data = resp.json()
        from utils.logger import log
        log.info(f"[录费用] order_id={order_id}, index={i}, resp_code={data.get('code')}, resp_msg={data.get('msg')}")
        log.info(f"[录费用] payload_customer_count={len(payload['to_customer']['put_amount']['standard_list'])}, "
                 f"supplier_count={len(payload['to_supplier']['pay_amount']['standard_list'])}")
        result["results"].append({
            "index": i,
            "config": config,
            "payload": payload,
            "resp": resp,
            "data": data,
        })
        result["steps"].append({
            "name": f"录费用({i + 1})",
            "code": data.get("code"),
            "msg": data.get("msg"),
            "to_customer_count": len(config.get("to_customer_fees") or []),
            "to_supplier_count": len(config.get("to_supplier_fees") or []),
        })

        # 录完费用后自动执行资产推送审批
        if audit_after_fee:
            audit_type = "assetPush"

            # 1) 发起审批
            with allure.step(f'[资产推送] 发起审批({i + 1}): {audit_type}'):
                send_resp = AuditApi.send_audit(audit_type, order_id)
                send_data = send_resp.json()
                result["steps"].append({
                    "name": f"发起审批({i + 1})",
                    "code": send_data.get("code"),
                    "msg": send_data.get("msg"),
                })

            # 2) 查询审批ID
            with allure.step(f'[资产推送] 查询审批ID({i + 1}): {audit_type}'):
                query_resp = AuditApi.query_pending_audits(
                    audit_type=audit_type,
                    audit_status=["1"],
                    page_no=1,
                    page_size=1,
                )
                query_data = query_resp.json()
                records = query_data.get("data", {}).get("data", [])
                first = records[0] if records else {}
                audit_id = first.get("audit_id", "")

            # 3) 审批通过
            with allure.step(f'[资产推送] 审批通过({i + 1}): {audit_type}'):
                approve_resp = AuditApi.audit_execute(
                    audit_ids=[audit_id] if audit_id else [],
                    audit_status=2,
                )
                approve_data = approve_resp.json()
                result["steps"].append({
                    "name": f"查询审批ID({i + 1})",
                    "code": query_data.get("code"),
                    "msg": query_data.get("msg"),
                    "audit_id": audit_id,
                })
                result["steps"].append({
                    "name": f"审批通过({i + 1})",
                    "code": approve_data.get("code"),
                    "msg": approve_data.get("msg"),
                })

            result["results"][i]["audit_send_resp"] = send_resp
            result["results"][i]["audit_send_data"] = send_data
            result["results"][i]["audit_query_resp"] = query_resp
            result["results"][i]["audit_query_data"] = query_data
            result["results"][i]["audit_id"] = audit_id
            result["results"][i]["audit_approve_resp"] = approve_resp
            result["results"][i]["audit_approve_data"] = approve_data

    return result


def record_generate_fee_notice(
    order_id: str,
    finance_ids: List[str] = None,
    bank_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    生成费用通知单（发起 → 响应结构断言）

    Args:
        order_id   : 业务订单ID（从链路流程获取）
        finance_ids: 费用ID列表（默认取 FeeNoticeData 配置）
        bank_ids   : 账户ID列表（默认取 FeeNoticeData 配置）

    Returns:
        {
            'order_id': str,
            'resp': Response,
            'data': dict,
            'file_info': dict,   # data.file_name
            'steps': [...],
        }
    """
    result = {
        'order_id': order_id,
        'steps': [],
    }

    with allure.step('生成费用通知单'):
        resp = OrderApi.generate_fee_notice(
            order_id=order_id,
            finance_ids=finance_ids,
            bank_ids=bank_ids,
        )
        data = resp.json()
        result['resp'] = resp
        result['data'] = data

        # 提取 file_name（必定存在）
        result['file_info'] = data.get('data', {}).get('file_name', {}) or {}

        result['steps'].append({
            'name': '生成费用通知单',
            'code': data.get('code'),
            'msg': data.get('msg'),
        })

    return result


def record_generate_fee_confirm(
    order_id: str,
    finance_ids: List[str] = None,
    bank_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    生成费用确认单（发起 → 响应结构断言）

    Args:
        order_id   : 业务订单ID（从链路流程获取）
        finance_ids: 费用ID列表（默认取 FeeConfirmData 配置）
        bank_ids   : 账户ID列表（默认取 FeeConfirmData 配置）

    Returns:
        {
            'order_id': str,
            'resp': Response,
            'data': dict,
            'file_info': dict,   # data.file_name
            'steps': [...],
        }
    """
    result = {
        'order_id': order_id,
        'steps': [],
    }

    with allure.step('生成费用确认单'):
        resp = OrderApi.generate_fee_confirm(
            order_id=order_id,
            finance_ids=finance_ids,
            bank_ids=bank_ids,
        )
        data = resp.json()
        result['resp'] = resp
        result['data'] = data
        result['file_info'] = data.get('data', {}).get('file_name', {}) or {}
        result['steps'].append({
            'name': '生成费用确认单',
            'code': data.get('code'),
            'msg': data.get('msg'),
        })

    return result
