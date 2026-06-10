"""
订单流程编排 - 串联订单各阶段 API，自动处理数据依赖
"""
import time
from typing import Dict, Any, List

import allure

from core.http_client import http
from api.order import OrderApi
from api.audit_api import AuditApi
from data.order_data import generate_bl_no, BookRealAmountData


class OrderWorkflow:
    """
    订单完整生命周期编排

    流程阶段：新建 → 分发 → 暂存 → 提交 → 生成子订单

    每个方法返回完整的执行上下文（包含每一步的响应数据），
    测试用例只需关注 workflow 的最终结果进行断言。
    """

    @classmethod
    def _attach_context(cls, result: Dict[str, Any]):
        """将 workflow 执行结果附加到 Allure 报告"""
        allure.attach(
            str(result),
            name="Workflow 执行结果",
            attachment_type=allure.attachment_type.JSON
        )

    # =====================
    # 阶段一：新建 → 分发
    # =====================

    @classmethod
    def create_and_distribute(cls, bl_no: str = None) -> Dict[str, Any]:
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
            result["steps"].append({"Name": "新建订单", "code": create_data.get("code"), "msg": create_data.get("msg")})
            assert create_resp.status_code == 200, f"HTTP状态码异常: {create_resp.status_code}"
            assert create_data.get("code") == 200, f"新建失败: {create_data}"

        time.sleep(1)

        with allure.step("Step2: 按提单号查询获取 order_id"):
            create_order = OrderApi.get_order_by_bl_no(bl_no)
            result["create_order"] = create_order
            result["steps"].append({"Name": "按提单号查询", "found": bool(create_order), "order_id": create_order.get("order_id")})
            if not create_order:
                cls._attach_context(result)
                raise AssertionError(f"按提单号 {bl_no} 查询不到订单，无法继续流程")

        with allure.step("Step3: 分发订单"):
            distribute_resp = OrderApi.distribute_order(create_order, bl_no=bl_no)
            distribute_data = distribute_resp.json()
            result["distribute_resp"] = distribute_resp
            result["distribute_data"] = distribute_data
            result["steps"].append({"Name": "分发订单", "code": distribute_data.get("code"), "msg": distribute_data.get("msg")})
            assert distribute_resp.status_code == 200, "HTTP状态码异常"

        cls._attach_context(result)
        return result

    # =====================
    # 阶段二：暂存（status=1，提交为 status=2）
    # =====================

    @classmethod
    def stash(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
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
            result["steps"].append({"Name": "暂存订单", "code": stash_data.get("code"), "msg": stash_data.get("msg")})

        cls._attach_context(result)
        return result

    # =====================
    # 阶段三：提交
    # =====================

    @classmethod
    def submit(cls, order_info: Dict[str, Any], bl_no: str = None) -> Dict[str, Any]:
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
            result["steps"].append({"Name": "提交订单", "code": submit_data.get("code"), "msg": submit_data.get("msg")})

        cls._attach_context(result)
        return result

    @classmethod
    def generate_sub_order(cls, order_id: str) -> Dict[str, Any]:
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

        cls._attach_context(result)
        return result

    @classmethod
    def record_audit(
        cls,
        order_id: str,
        audit_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        录审批（发起审批 → 查询审批ID → 审批通过），按配置列表逐条执行

        audit_configs 每条配置格式：
            {
                'audit_type': 'assetPush',   # 审批类型
                'audit_status': 2,           # 审批状态，2=通过（默认）
            }
        返回值与 record_fee 结构一致
        """
        if audit_configs is None:
            audit_configs = []

        result = {
            'order_id': order_id,
            'results': [],
            'steps': [],
        }

        for i, cfg in enumerate(audit_configs):
            audit_type = cfg.get('audit_type', 'assetPush')

            # 1) 发起审批
            with allure.step(f'发起审批({i + 1}): {audit_type}'):
                send_resp = AuditApi.send_audit(audit_type, order_id)
                send_data = send_resp.json()
                result['steps'].append({
                    'name': f'发起审批({i + 1})',
                    'code': send_data.get('code'),
                    'msg': send_data.get('msg'),
                })

            # 2) 查最新审批ID
            with allure.step(f'查询审批ID({i + 1}): {audit_type}'):
                query_resp = AuditApi.query_pending_audits(
                    audit_type=audit_type,
                    audit_status=['1'],
                    page_no=1,
                    page_size=1,
                )
                query_data = query_resp.json()
                records = query_data.get('data', {}).get('data', [])
                first = records[0] if records else {}
                audit_id = first.get('audit_id', '')

            # 3) 审批通过
            with allure.step(f'审批通过({i + 1}): {audit_type}'):
                approve_resp = AuditApi.audit_execute(
                    audit_ids=[audit_id] if audit_id else [],
                    audit_status=cfg.get('audit_status', 2),
                )
                approve_data = approve_resp.json()

            result['results'].append({
                'index': i,
                'config': cfg,
                'send_resp': send_resp,
                'send_data': send_data,
                'query_resp': query_resp,
                'query_data': query_data,
                'audit_id': audit_id,
                'approve_resp': approve_resp,
                'approve_data': approve_data,
            })
            result['steps'].append({
                'name': f'查询审批ID({i + 1})',
                'code': query_data.get('code'),
                'msg': query_data.get('msg'),
                'audit_id': audit_id,
            })
            result['steps'].append({
                'name': f'审批通过({i + 1})',
                'code': approve_data.get('code'),
                'msg': approve_data.get('msg'),
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_order_lock(
        cls,
        order_id: str,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """
        录订单锁定审批（发起审批 → 查询审批ID → 审批通过）

        Args:
            order_id: 业务订单ID
            bl_no   : 提单号（用于查询 container）

        Returns:
            {
                'order_id': str,
                'container': [...],
                'send_resp': Response,
                'send_data': dict,
                'query_resp': Response,
                'query_data': dict,
                'audit_id': str,
                'approve_resp': Response,
                'approve_data': dict,
                'steps': [...],
            }
        """
        result = {
            'order_id': order_id,
            'steps': [],
        }

        # 1) 从订单详情获取 container
        with allure.step('获取箱型信息（用于订单锁定审批）'):
            container = OrderApi.get_container_from_order(bl_no=bl_no)
            if not container:
                from data.order_data import SubmitRequiredFields
                container = SubmitRequiredFields.DEFAULT_CONTAINER.copy()
            result['container'] = container
            result['steps'].append({
                'name': '获取箱型信息',
                'container_count': len(container),
                'from_order': bool(OrderApi.get_container_from_order(bl_no=bl_no)),
            })

        # 2) 发起订单锁定审批
        with allure.step('发起订单锁定审批'):
            send_resp = AuditApi.send_actual_cost_lock(
                order_id=order_id,
                container=container,
            )
            send_data = send_resp.json()
            result['send_resp'] = send_resp
            result['send_data'] = send_data
            result['steps'].append({
                'name': '发起订单锁定审批',
                'code': send_data.get('code'),
                'msg': send_data.get('msg'),
            })

        # 3) 查询审批ID
        with allure.step('查询订单锁定审批ID'):
            query_resp = AuditApi.query_pending_audits(
                audit_type='actualCostLockApplication',
                audit_status=['1'],
                page_no=1,
                page_size=1,
                active_tab='examine_wait',
            )
            query_data = query_resp.json()
            records = query_data.get('data', {}).get('data', [])
            first = records[0] if records else {}
            audit_id = first.get('audit_id', '')
            result['query_resp'] = query_resp
            result['query_data'] = query_data
            result['audit_id'] = audit_id
            result['steps'].append({
                'name': '查询订单锁定审批ID',
                'code': query_data.get('code'),
                'msg': query_data.get('msg'),
                'audit_id': audit_id,
            })

        # 4) 审批通过
        with allure.step('订单锁定审批通过'):
            approve_resp = AuditApi.audit_execute(
                audit_ids=[audit_id] if audit_id else [],
                audit_status=2,
            )
            approve_data = approve_resp.json()
            result['approve_resp'] = approve_resp
            result['approve_data'] = approve_data
            result['steps'].append({
                'name': '订单锁定审批通过',
                'code': approve_data.get('code'),
                'msg': approve_data.get('msg'),
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_fee(
        cls,
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

        cls._attach_context(result)
        return result

    # =====================
    # 完整流程
    # =====================

    @classmethod
    def full_flow(
        cls,
        bl_no: str = None,
        stop_at: str = 'submit',
        skip_stash: bool = False,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        完整订单流程：新建 → 分发 → [查询] → [暂存] → [提交] → [生成子订单] → [录费用] → [录审批]

        Args:
            bl_no: 提单号，默认自动生成
            stop_at: 执行到哪个阶段后停止，可选值：
                - 'create'              仅新建
                - 'distribute'         新建 + 分发
                - 'stash'              新建 + 分发 + 查询 + 暂存
                - 'submit'             新建 + 分发 + 查询 + 暂存 + 提交（默认）
                - 'generate_sub_order' 新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单
                - 'record_fee'         新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用
                - 'record_audit'       新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批
                - 'order_lock'         新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批 + 订单锁定审批
            skip_stash: 是否跳过暂存
            fee_configs: 录费用配置列表（stop_at='record_fee' 时使用）

        Returns:
            {
                'bl_no': str,
                'steps': [...],
                'create_resp/create_data/create_order': ...,
                'distribute_resp/distribute_data': ...,
                'current_order': ...,
                'stash_resp/stash_data': ...,
                'after_stash_order': ...,
                'submit_resp/submit_data': ...,
                'after_submit_order': ...,
                'generate_sub_resp/data': ...,
                'record_fee_results': [...],
            }
        """
        if bl_no is None:
            bl_no = generate_bl_no()

        result = {
            'bl_no': bl_no,
            'stop_at': stop_at,
            'skip_stash': skip_stash,
            'steps': []
        }

        # Step 1: 新建
        with allure.step(f'[{stop_at}] Step1: 新建订单, bl_no={bl_no}'):
            create_resp = OrderApi.add_order(bl_no=bl_no)
            create_data = create_resp.json()
            result['create_resp'] = create_resp
            result['create_data'] = create_data
            result['steps'].append({'name': '新建订单', 'code': create_data.get('code')})
            assert create_resp.status_code == 200, f'HTTP状态码异常: {create_resp.status_code}'
            assert create_data.get('code') == 200, f'新建失败: {create_data}'

        if stop_at == 'create':
            cls._attach_context(result)
            return result

        time.sleep(1)

        # Step 2: 按提单号查询获取 order_id
        with allure.step(f'[{stop_at}] Step2: 按提单号查询获取 order_id'):
            create_order = OrderApi.get_order_by_bl_no(bl_no)
            result['create_order'] = create_order
            result['steps'].append({'name': '按提单号查询', 'found': bool(create_order)})
            if not create_order:
                cls._attach_context(result)
                raise AssertionError(f'按提单号 {bl_no} 查询不到订单，无法继续流程')

        # Step 3: 分发
        with allure.step(f'[{stop_at}] Step3: 分发订单'):
            distribute_resp = OrderApi.distribute_order(create_order, bl_no=bl_no)
            distribute_data = distribute_resp.json()
            result['distribute_resp'] = distribute_resp
            result['distribute_data'] = distribute_data
            result['steps'].append({'name': '分发订单', 'code': distribute_data.get('code')})
            assert distribute_resp.status_code == 200, 'HTTP状态码异常'

        if stop_at == 'distribute':
            cls._attach_context(result)
            return result

        # Step 4: 查询（分发后必须查询获取最新状态）
        with allure.step(f'[{stop_at}] Step4: 查询订单（分发后）'):
            time.sleep(1)
            current_order = OrderApi.get_order_by_bl_no(bl_no)
            result['current_order'] = current_order
            result['steps'].append({
                'name': '查询订单',
                'order_id': current_order.get('order_id'),
                'entrust_status': current_order.get('entrust_status'),
                'status': current_order.get('status'),
            })

        # Step 5 / 5a: 暂存（或跳过）
        if skip_stash:
            result['steps'].append({'name': '暂存订单', 'skipped': True})
            if stop_at == 'stash':
                cls._attach_context(result)
                return result
        else:
            with allure.step(f'[{stop_at}] Step5: 暂存订单'):
                stash_result = cls.stash(current_order, bl_no=bl_no)
                result['stash_resp'] = stash_result['stash_resp']
                result['stash_data'] = stash_result['stash_data']
                result['steps'].append({
                    'name': '暂存订单',
                    'code': stash_result['stash_data'].get('code'),
                    'msg': stash_result['stash_data'].get('msg'),
                })

            if stop_at == 'stash':
                cls._attach_context(result)
                return result

            # Step 6: 暂存后再次查询
            with allure.step(f'[{stop_at}] Step6: 查询订单（暂存后）'):
                time.sleep(1)
                after_stash_order = OrderApi.get_order_by_bl_no(bl_no)
                result['after_stash_order'] = after_stash_order
                result['steps'].append({
                    'name': '查询订单（暂存后）',
                    'order_id': after_stash_order.get('order_id'),
                    'entrust_status': after_stash_order.get('entrust_status'),
                    'status': after_stash_order.get('status'),
                })

        # Step 7 / Step 5: 提交
        step_label = 'Step6' if not skip_stash else 'Step5'
        with allure.step(f'[{stop_at}] {step_label}: 提交订单'):
            submit_order = result.get('after_stash_order') or result.get('current_order')
            submit_result = cls.submit(submit_order, bl_no=bl_no)
            result['submit_resp'] = submit_result['submit_resp']
            result['submit_data'] = submit_result['submit_data']
            result['steps'].append({'name': '提交订单', 'code': submit_result['submit_data'].get('code'), 'msg': submit_result['submit_data'].get('msg')})

        # 提交后查询获取最新 order_id 用于生成子订单
        with allure.step(f'[{stop_at}] {step_label}\': 查询订单（提交后）'):
            time.sleep(1)
            after_submit_order = OrderApi.get_order_by_bl_no(bl_no)
            result['after_submit_order'] = after_submit_order
            result['steps'].append({
                'name': '查询订单（提交后）',
                'order_id': after_submit_order.get('order_id'),
            })

        # Step 8: 生成子订单
        if stop_at in ('generate_sub_order', 'record_fee', 'record_audit', 'order_lock'):
            with allure.step(f'[{stop_at}] Step7: 生成子订单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成子订单')
                gen_result = cls.generate_sub_order(order_id)
                result['generate_sub_resp'] = gen_result['generate_sub_resp']
                result['generate_sub_data'] = gen_result['generate_sub_data']
                result['steps'].append({
                    'name': '生成子订单',
                    'code': gen_result['generate_sub_data'].get('code'),
                    'msg': gen_result['generate_sub_data'].get('msg'),
                    'order_id': order_id,
                })

        # Step 9: 录费用（含资产推送审计）
        if stop_at in ('record_fee', 'record_audit', 'order_lock'):
            with allure.step(f'[{stop_at}] Step8: 录费用'):
                order_id = after_submit_order.get('order_id')
                audit_after = stop_at in ('record_audit', 'order_lock')
                fee_result = cls.record_fee(
                    order_id=order_id,
                    fee_configs=fee_configs or [],
                    audit_after_fee=audit_after,
                )
                result['record_fee_results'] = fee_result['results']
                result['steps'].extend(fee_result['steps'])

        # assetPush 已在 record_fee 内部完成（audit_after_fee=True）

        # Step 10: 订单锁定审批
        if stop_at == 'order_lock':
            with allure.step(f'[{stop_at}] Step10: 订单锁定审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起订单锁定审批')
                lock_result = cls.record_order_lock(order_id=order_id, bl_no=bl_no)
                result['order_lock_result'] = lock_result
                result['steps'].extend(lock_result['steps'])

        cls._attach_context(result)
        return result

    # =====================
    # 快捷方法
    # =====================

    @classmethod
    def run(cls, bl_no: str = None) -> Dict[str, Any]:
        """默认完整流程，等同于 full_flow(stop_at='submit')"""
        return cls.full_flow(bl_no=bl_no, stop_at='submit')

    @classmethod
    def run_until_distribute(cls, bl_no: str = None) -> Dict[str, Any]:
        """仅执行到分发阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='distribute')

    @classmethod
    def run_until_stash(cls, bl_no: str = None) -> Dict[str, Any]:
        """仅执行到暂存阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='stash')

    @classmethod
    def run_until_generate_sub_order(cls, bl_no: str = None) -> Dict[str, Any]:
        """执行到生成子订单阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='generate_sub_order')

    @classmethod
    def run_until_record_fee(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到录费用阶段"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='record_fee',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_record_audit(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到录审批阶段（含资产推送）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='record_audit',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_order_lock(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到订单锁定审批阶段（含资产推送 + 订单锁定）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='order_lock',
            fee_configs=fee_configs,
        )
