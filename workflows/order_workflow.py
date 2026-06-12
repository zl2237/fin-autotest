"""
订单流程编排 - 串联订单各阶段 API，自动处理数据依赖
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List

import allure

from config.settings import BASE_DIR, TEST_DATA_DIR
from core.http_client import http
from api.order import OrderApi
from api.audit_api import AuditApi
from api.finance_api import FinanceApi, _default_main_id
from data.order_data import (
    generate_bl_no,
    BookRealAmountData,
    FeeNoticeData,
    FeeConfirmData,
    ReceiveAccountData,
    ACTION_CHECK,
    ACTION_SUBMIT,
    CONFIRM_TYPE_PENDING,
)


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
    def record_generate_fee_notice(
        cls,
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

        cls._attach_context(result)
        return result

    @classmethod
    def record_receive_account(
        cls,
        bl_no: str,
        put_settle_object_id: str,
        main_id: str,
        put_settle_object: str,
    ) -> Dict[str, Any]:
        """
        发起应收对账批次（financePutList 查询 → check 预校验 → submit 正式提交）

        三个请求共享相同的 select_list（来自 financePutList 响应 data.data）。

        Args:
            bl_no                : 提单号
            put_settle_object_id : 托单结算对象ID
            main_id              : 主体ID
            put_settle_object   : 托单结算对象名称
            main_name            : 主体名称（固定从配置读取，不从外部传入）

        Returns:
            {
                'bl_no': str,
                'put_list_resp': Response,
                'put_list_data': dict,
                'select_list': [...],
                'check_resp': Response,
                'check_data': dict,
                'submit_resp': Response,
                'submit_data': dict,
                'receive_account_id': str,
                'receive_account_no': str,
                'steps': [...],
            }
        """
        from data.order_data import RECEIVE_ACCOUNT_MAIN_NAME

        result = {
            'bl_no': bl_no,
            'steps': [],
        }
        main_name = RECEIVE_ACCOUNT_MAIN_NAME

        # Step 1: financePutList - 查询应收款项列表
        with allure.step('查询应收款项列表（financePutList）'):
            put_list_resp = FinanceApi.query_finance_put_list(
                bl_no=bl_no,
                put_settle_object_id=put_settle_object_id,
                main_id=main_id,
            )
            put_list_data = put_list_resp.json()
            result['put_list_resp'] = put_list_resp
            result['put_list_data'] = put_list_data
            result['steps'].append({
                'name': '查询应收款项列表',
                'code': put_list_data.get('code'),
                'msg': put_list_data.get('msg'),
            })

        # 从 financePutList 响应构建 select_list
        select_list = ReceiveAccountData.build_select_list_from_put_list(put_list_data.get('data', {}))
        result['select_list'] = select_list

        # Step 2: orderReceiveAccountEdit (action=check) - 预校验
        with allure.step('应收对账预校验（action=check）'):
            check_resp = FinanceApi.edit_receive_account(
                action=ACTION_CHECK,
                put_settle_object_id=put_settle_object_id,
                main_id=main_id,
                put_settle_object=put_settle_object,
                main_name=main_name,
                select_list=select_list,
            )
            check_data = check_resp.json()
            result['check_resp'] = check_resp
            result['check_data'] = check_data
            result['steps'].append({
                'name': '应收对账预校验',
                'code': check_data.get('code'),
                'msg': check_data.get('msg'),
            })

        # Step 3: orderReceiveAccountEdit (action=submit) - 正式发起
        with allure.step('发起应收对账批次（action=submit）'):
            submit_resp = FinanceApi.edit_receive_account(
                action=ACTION_SUBMIT,
                put_settle_object_id=put_settle_object_id,
                main_id=main_id,
                put_settle_object=put_settle_object,
                main_name=main_name,
                select_list=select_list,
            )
            submit_data = submit_resp.json()
            result['submit_resp'] = submit_resp
            result['submit_data'] = submit_data

            submit_data_inner = submit_data.get('data', {})
            result['receive_account_id'] = submit_data_inner.get('receive_account_id', '')
            result['receive_account_no'] = submit_data_inner.get('receive_account_no', '')

            result['steps'].append({
                'name': '发起应收对账批次',
                'code': submit_data.get('code'),
                'msg': submit_data.get('msg'),
                'receive_account_id': result['receive_account_id'],
                'receive_account_no': result['receive_account_no'],
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_confirm_account(
        cls,
        receive_account_id: str,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """
        确认应收对账（receiveConfirmList 查询 → accountConfirm 确认 → receiveAccountPage 验证）

        Args:
            receive_account_id: 应收对账批次ID（来自 record_receive_account 响应）
            bl_no: 提单号（用于确认后查询验证）

        Returns:
            {
                'receive_account_id': str,
                'detail_resp': Response,
                'detail_data': dict,
                'confirm_list_resp': Response,
                'confirm_list_data': dict,
                'confirm_list': [...],
                'submit_resp': Response,
                'submit_data': dict,
                'page_resp': Response,
                'page_data': dict,
                'steps': [...],
            }
        """
        result = {
            'receive_account_id': receive_account_id,
            'steps': [],
        }

        # Step 1: receiveAccountDetail - 查询批次详情
        with allure.step('查询应收对账批次详情（receiveAccountDetail）'):
            detail_resp = FinanceApi.get_receive_account_detail(
                receive_account_id=receive_account_id,
            )
            detail_data = detail_resp.json()
            result['detail_resp'] = detail_resp
            result['detail_data'] = detail_data
            result['steps'].append({
                'name': '查询应收对账批次详情',
                'code': detail_data.get('code'),
                'msg': detail_data.get('msg'),
            })

        # Step 2: receiveConfirmList - 查询应收确认列表
        with allure.step('查询应收确认列表（receiveConfirmList）'):
            confirm_list_resp = FinanceApi.get_receive_confirm_list(
                receive_account_id=receive_account_id,
                confirm_type=CONFIRM_TYPE_PENDING,
            )
            confirm_list_data = confirm_list_resp.json()
            result['confirm_list_resp'] = confirm_list_resp
            result['confirm_list_data'] = confirm_list_data

            confirm_list = confirm_list_data.get('data', []) or []
            result['confirm_list'] = confirm_list

            result['steps'].append({
                'name': '查询应收确认列表',
                'code': confirm_list_data.get('code'),
                'msg': confirm_list_data.get('msg'),
                'confirm_count': len(confirm_list),
            })

        # Step 3: accountConfirm - 确认应收对账
        with allure.step('确认应收对账（accountConfirm）'):
            submit_resp = FinanceApi.confirm_receive_account(
                receive_account_id=receive_account_id,
                confirm_list=confirm_list,
                confirm_type=CONFIRM_TYPE_PENDING,
            )
            submit_data = submit_resp.json()
            result['submit_resp'] = submit_resp
            result['submit_data'] = submit_data
            result['steps'].append({
                'name': '确认应收对账',
                'code': submit_data.get('code'),
                'msg': submit_data.get('msg'),
            })

        # Step 4: receiveAccountPage - 确认后查询批次列表（验证状态）
        with allure.step('确认后查询批次列表（receiveAccountPage）'):
            page_resp = FinanceApi.get_receive_account_page(
                bl_nos=[bl_no] if bl_no else [],
            )
            page_data = page_resp.json()
            result['page_resp'] = page_resp
            result['page_data'] = page_data
            result['steps'].append({
                'name': '确认后查询批次列表',
                'code': page_data.get('code'),
                'msg': page_data.get('msg'),
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_invoice_batch(
        cls,
        bl_no: str,
        put_settle_object_id: str,
        main_id: str,
        put_settle_object: str,
        main_name: str,
        order_fee_real_ids: List[str],
        order_sub_ids: List[str],
        order_sub_customer_ids: List[str],
    ) -> Dict[str, Any]:
        """
        发起应收开票批次审批

        流程：financePutList → monthExchangeRate → getSellInfo → batchOrderEdit(submit) → batchpage(verify)

        Args:
            bl_no                   : 提单号
            put_settle_object_id    : 托单结算对象ID
            main_id                : 主体ID
            put_settle_object      : 托单结算对象名称
            main_name              : 主体名称
            order_fee_real_ids     : 费用ID列表（来自 financePutList amount_list）
            order_sub_ids          : 子订单ID列表
            order_sub_customer_ids : 子订单客户ID列表

        Returns:
            {
                'put_list_resp' / 'put_list_data' / 'put_list_data_records': ...,
                'rate_resp' / 'rate_data' / 'exchange_rate': ...,
                'sell_info_resp' / 'sell_info_data' / 'seller_list': ...,
                'submit_resp' / 'submit_data' / 'batch_id' / 'batch_no': ...,
                'page_resp' / 'page_data': ...,
                'steps': [...],
            }
        """
        from api.invoice_batch_api import InvoiceBatchApi
        from data.order_data import (
            INVOICE_USD_TURN_ON,
            INVOICE_MERGE_CNY_NO,
            INVOICE_RATE_TYPE_SPECIFY,
            INVOICE_DEFAULT_RATE,
            INVOICE_DEFAULT_FORM,
            INVOICE_DEFAULT_TYPE,
            INVOICE_DEFAULT_ITEM,
        )

        result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

        # Step 1: financePutList（开票模式）查询应收款项
        with allure.step('查询应收款项列表（financePutList 开票模式）'):
            put_list_resp = InvoiceBatchApi.query_finance_put_list_for_invoice(
                bl_no=bl_no,
                put_settle_object_id=put_settle_object_id,
                main_id=main_id,
            )
            put_list_data = put_list_resp.json()
            result['put_list_resp'] = put_list_resp
            result['put_list_data'] = put_list_data
            result['steps'].append({
                'name': '查询应收款项列表（开票）',
                'code': put_list_data.get('code'),
                'msg': put_list_data.get('msg'),
            })

        # Step 2: monthExchangeRate 获取汇率
        with allure.step('获取汇率（monthExchangeRate）'):
            rate_resp = InvoiceBatchApi.get_month_exchange_rate(main_id=main_id)
            rate_data = rate_resp.json()
            result['rate_resp'] = rate_resp
            result['rate_data'] = rate_data
            exchange_rate = rate_data.get('data', {}).get('rate', '7')
            if not exchange_rate:
                exchange_rate = str(INVOICE_DEFAULT_RATE)
            result['exchange_rate'] = exchange_rate
            result['steps'].append({
                'name': '获取汇率',
                'code': rate_data.get('code'),
                'msg': rate_data.get('msg'),
                'rate': exchange_rate,
            })

        # Step 3: getSellInfo 获取开票方信息（需要先有 purchaser 信息）
        # 从 put_list_data 中提取 amount_list 构建 fee_usd_total 和 order_fee_real_ids
        put_records = put_list_data.get('data', {}).get('data', []) or []
        fee_usd_total = "0.00"
        real_fee_ids = []
        real_order_sub_ids = []
        real_order_sub_customer_ids = []
        if put_records:
            record = put_records[0]
            amount_list = record.get('amount_list', []) or []
            total = sum(float(item.get('real_amount', 0)) for item in amount_list)
            fee_usd_total = f"{total:.2f}"
            real_fee_ids = [str(item.get('order_fee_real_id', '')) for item in amount_list if item.get('order_fee_real_id')]
            real_order_sub_id = str(record.get('order_sub_id', ''))
            real_order_sub_ids = [real_order_sub_id] if real_order_sub_id else order_sub_ids
            real_order_sub_customer_id = str(record.get('customer_id', ''))
            real_order_sub_customer_ids = [real_order_sub_customer_id] if real_order_sub_customer_id else order_sub_customer_ids
            # 确保 put_settle_object 和 main_name 与查询结果一致
            if record.get('put_settle_object'):
                put_settle_object = record.get('put_settle_object', put_settle_object)
            if record.get('main_name'):
                main_name = record.get('main_name', main_name)

        if not real_fee_ids:
            cls._attach_context(result)
            raise AssertionError(f'financePutList 响应中 amount_list 为空，无法发起应收开票批次: {put_list_data}')

        with allure.step('获取开票方信息（getSellInfo）'):
            sell_info_resp = InvoiceBatchApi.get_sell_info(
                put_settle_object_id=put_settle_object_id,
                put_settle_object=put_settle_object,
                main_id=main_id,
                main_name_cn=main_name,
                order_fee_real_ids=real_fee_ids,
                order_sub_ids=real_order_sub_ids,
                sys_rate=exchange_rate,
                usd_is_turn=INVOICE_USD_TURN_ON,
            )
            sell_info_data = sell_info_resp.json()
            result['sell_info_resp'] = sell_info_resp
            result['sell_info_data'] = sell_info_data
            seller_list = sell_info_data.get('data', []) or []
            result['seller_list'] = seller_list
            result['steps'].append({
                'name': '获取开票方信息',
                'code': sell_info_data.get('code'),
                'msg': sell_info_data.get('msg'),
                'seller_count': len(seller_list),
            })

        # Step 4: batchOrderEdit(submit) 正式提交开票批次
        # 构建 usd_require：使用卖家信息（seller_id）和 purchaser 信息
        usd_seller = seller_list[0] if seller_list else {}
        usd_purchaser = seller_list[1] if len(seller_list) > 1 else seller_list[0] if seller_list else {}

        usd_require = {
            "fast_remark": "[]",
            "currency": "CNY",
            "amount_total_usd": float(fee_usd_total) if fee_usd_total else 0,
            "amount_total_cny": "",
            "rate": float(exchange_rate) if exchange_rate else 0,
            "turn_amount_total_cny": f"{float(fee_usd_total) * float(exchange_rate):.2f}" if fee_usd_total and exchange_rate else "0.00",
            "turn_amount_total_usd": "",
            "turn_amount_total": f"{float(fee_usd_total) * float(exchange_rate):.2f}" if fee_usd_total and exchange_rate else "0.00",
            "invoice_apply_name": f"{main_name} + {put_settle_object} + 2026-05 + USD {fee_usd_total}",
            "invoice_apply_simple": "",
            "invoice_form": INVOICE_DEFAULT_FORM,
            "invoice_type": INVOICE_DEFAULT_TYPE,
            "purchaser_id": str(put_settle_object_id),
            "purchaser_head_cn": put_settle_object,
            "purchaser_tax_number": usd_purchaser.get('identifier_no', ''),
            "seller_id": usd_seller.get('order_main_finance_id', ''),
            "seller_name": usd_seller.get('bank_account', ''),
            "bank_account": "",
            "seller_info": json.dumps(usd_seller),
            "invoice_items": "",
            "invoice_rate_type": "",
            "invoice_rate": "",
            "require_other": "暂无要求",
            "remark": "—",
            "rate_list": [
                {
                    "cost_name": item.get('fee_real_name', ''),
                    "fee_real_no": item.get('fee_real_no', ''),
                    "cost_no": item.get('cost_no', ''),
                    "invoice_rate": str(INVOICE_DEFAULT_RATE),
                    "real_amount": item.get('real_amount', '0.00'),
                    "currency": item.get('currency', 'USD'),
                    "invoice_item": INVOICE_DEFAULT_ITEM,
                    "amount_error_flag": False,
                    "rowIndex": idx,
                    "invoice_item_name": "国际货物运输代理海运费",
                }
                for idx, item in enumerate(put_records[0].get('amount_list', []) or [])
            ] if put_records and put_records[0].get('amount_list') else [],
            "purchaser_name": put_settle_object,
            "fund_name": usd_seller.get('fund_name', ''),
        }
        cny_require = {
            "fast_remark": "[]",
            "currency": "",
            "amount_total_usd": "",
            "amount_total_cny": "",
            "rate": "",
            "turn_amount_total_cny": "",
            "turn_amount_total_usd": "",
            "turn_amount_total": "",
            "invoice_apply_name": "",
            "invoice_apply_simple": "",
            "invoice_form": "",
            "invoice_type": "",
            "purchaser_id": "",
            "purchaser_head_cn": "",
            "purchaser_tax_number": "",
            "seller_id": "",
            "seller_name": "",
            "bank_account": "",
            "seller_info": "",
            "invoice_items": "",
            "invoice_rate_type": "",
            "invoice_rate": "",
            "require_other": "",
            "remark": "—",
            "rate_list": [],
        }

        with allure.step('提交应收开票批次申请（batchOrderEdit submit）'):
            submit_resp = InvoiceBatchApi.batch_order_edit(
                action="submit",
                put_settle_object_id=put_settle_object_id,
                put_settle_object=put_settle_object,
                main_id=main_id,
                main_name_cn=main_name,
                order_fee_real_ids=real_fee_ids,
                order_sub_ids=real_order_sub_ids,
                order_sub_customer_ids=real_order_sub_customer_ids,
                usd_require=usd_require,
                cny_require=cny_require,
                sys_rate=exchange_rate,
                appoint_rate=str(INVOICE_DEFAULT_RATE),
                cost_usd=fee_usd_total,
                cost_cny="0.00",
                rate_type=INVOICE_RATE_TYPE_SPECIFY,
                audit_msg={"title": "开票批次ID", "code": None, "msgs": ["应收开票批次申请"]},
                select_node_user=[],
                fee_currency="USD",
            )
            invoice_submit_data = submit_resp.json()
            result['invoice_submit_resp'] = submit_resp
            result['invoice_submit_data'] = invoice_submit_data
            result['steps'].append({
                'name': '提交应收开票批次申请',
                'code': invoice_submit_data.get('code'),
                'msg': invoice_submit_data.get('msg'),
            })

        # Step 5: batchpage 验证批次创建
        with allure.step('验证应收开票批次（batchpage）'):
            page_resp = InvoiceBatchApi.query_batch_page(bl_no=bl_no)
            page_data = page_resp.json()
            result['page_resp'] = page_resp
            result['page_data'] = page_data
            result['steps'].append({
                'name': '验证应收开票批次',
                'code': page_data.get('code'),
                'msg': page_data.get('msg'),
            })

            # 从批次列表中提取最新一条的 batch_id
            records = page_data.get("data", {}).get("data", []) or []
            result['batch_id'] = records[0].get("receive_invoice_batch_id", "") if records else ""

        cls._attach_context(result)
        return result

    @classmethod
    def record_invoice_batch_audit(
        cls,
        batch_id: str,
    ) -> Dict[str, Any]:
        """
        审核生成开票申请（查询审批ID → 审批通过）

        Args:
            batch_id: 开票批次ID（来自 record_invoice_batch 响应中的 batch_id）

        Returns:
            {
                'batch_id': str,
                'audit_query_resp': Response,
                'audit_query_data': dict,
                'audit_id': str,
                'audit_execute_resp': Response,
                'audit_execute_data': dict,
                'steps': [...],
            }
        """
        result: Dict[str, Any] = {
            "batch_id": batch_id,
            "steps": [],
        }

        # Step 1: auditPage - 查询开票批次审批ID
        with allure.step('查询应收开票批次审批ID（auditPage）'):
            query_resp = AuditApi.query_invoice_batch_audit(
                relation_id=batch_id,
                audit_status=["1"],
                page_no=1,
                page_size=1,
                active_tab="examine_wait",
            )
            query_data = query_resp.json()
            result['audit_query_resp'] = query_resp
            result['audit_query_data'] = query_data

            records = query_data.get("data", {}).get("data", []) or []
            first = records[0] if records else {}
            audit_id = first.get("audit_id", "")
            result['audit_id'] = audit_id
            result['steps'].append({
                'name': '查询应收开票批次审批ID',
                'code': query_data.get('code'),
                'msg': query_data.get('msg'),
                'audit_id': audit_id,
                'audit_count': len(records),
            })

            if not audit_id:
                cls._attach_context(result)
                raise AssertionError(f'未查到开票批次审批记录，batch_id={batch_id}，响应: {query_data}')

        # Step 2: auditExecute - 审批通过
        with allure.step('审批通过应收开票批次（auditExecute）'):
            execute_resp = AuditApi.audit_execute(
                audit_ids=[audit_id],
                audit_status=2,
            )
            execute_data = execute_resp.json()
            result['audit_execute_resp'] = execute_resp
            result['audit_execute_data'] = execute_data
            result['steps'].append({
                'name': '审批通过应收开票批次',
                'code': execute_data.get('code'),
                'msg': execute_data.get('msg'),
                'audit_id': audit_id,
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_invoice_upload(
        cls,
        bl_no: str,
        receive_invoice_batch_id: str = None,
        file_id: str = None,
        file_name: str = None,
        file_url: str = None,
        original_name: str = None,
        invoice_amount: str = None,
        invoice_number: str = None,
        buyer_chinese_header: str = None,
        buyer_identifier_no: str = None,
        seller_chinese_header: str = None,
        seller_identifier_no: str = None,
        fee_file_info: Dict[str, Any] = None,
        invoice_file_path: str = None,
    ) -> Dict[str, Any]:
        """
        发票上传与登记

        流程：uploadFile（Step 0）→ invoiceAdd（Step 1）→ applyPage（Step 2）→ allocationInvoiceFee（Step 3）

        Args:
            bl_no                    : 提单号
            receive_invoice_batch_id : 开票批次ID（来自 record_invoice_batch，可选）
            file_id                  : 发票文件ID（已废弃，推荐用 invoice_file_path）
            file_name                : 发票文件名（已废弃，推荐用 invoice_file_path）
            file_url                 : 发票文件URL（已废弃，推荐用 invoice_file_path）
            original_name            : 原始文件名（已废弃，推荐用 invoice_file_path）
            invoice_amount           : 发票金额
            invoice_number           : 发票号码（自动生成唯一值）
            buyer_chinese_header    : 购买方名称
            buyer_identifier_no     : 购买方税号
            seller_chinese_header   : 销售方名称
            seller_identifier_no    : 销售方税号
            fee_file_info           : 费用通知单的文件信息 dict（file_id/file_name/file_url/original_name）
            invoice_file_path        : 本地发票文件路径，传入则自动执行 Step 0 上传并提取 file 信息

        Returns:
            {
                'add_resp' / 'add_data' / 'receive_invoice_id' / 'invoice_number': ...,
                'apply_page_resp' / 'apply_page_data' / 'receive_invoice_apply_id': ...,
                'alloc_resp' / 'alloc_data': ...,
                'steps': [...],
            }
        """
        from api.invoice_upload_api import InvoiceUploadApi
        from data.order_data import _RECEIVE_INVOICE_UPLOAD_CFG

        result: Dict[str, Any] = {"bl_no": bl_no, "steps": []}

        # Step 0: uploadFile - 上传发票文件，获取真实的 file 信息
        uploaded_file_info: Dict[str, Any] = {}
        if invoice_file_path:
            with allure.step('上传发票文件（uploadFile）'):
                upload_resp = InvoiceUploadApi.upload_file(file_path=invoice_file_path)
                upload_data = upload_resp.json()
                result['upload_resp'] = upload_resp
                result['upload_data'] = upload_data
                uploaded_file_info = upload_data.get("data", {}) or {}
                result['uploaded_file_info'] = uploaded_file_info
                result['steps'].append({
                    'name': '上传发票文件',
                    'code': upload_data.get('code'),
                    'msg': upload_data.get('msg'),
                    'file_id': uploaded_file_info.get('file_id'),
                    'file_name': uploaded_file_info.get('file_name'),
                    'file_url': uploaded_file_info.get('file_url'),
                    'file_type': uploaded_file_info.get('file_type'),
                    'original_name': uploaded_file_info.get('original_name'),
                })
                if not uploaded_file_info.get('file_id'):
                    cls._attach_context(result)
                    raise AssertionError(f'uploadFile 响应中未找到 file_id: {upload_data}')

        # 从 YAML 读取默认值
        cfg = _RECEIVE_INVOICE_UPLOAD_CFG or {}
        buyer_cfg = cfg.get("buyer", {})
        seller_cfg = cfg.get("seller", {})
        file_cfg = cfg.get("invoice_file", {})
        buyer_chinese_header = buyer_chinese_header or buyer_cfg.get("chinese_header", "")
        buyer_identifier_no = buyer_identifier_no or buyer_cfg.get("identifier_no", "")
        seller_chinese_header = seller_chinese_header or seller_cfg.get("chinese_header", "")
        seller_identifier_no = seller_identifier_no or seller_cfg.get("identifier_no", "")
        # 填充文件字段：Step 0 最高 > fee_file_info > 显式参数 > file_cfg
        if uploaded_file_info:
            file_id = uploaded_file_info.get('file_id', '') or "9999999999"
            file_name = uploaded_file_info.get('file_name', '') or ""
            file_url = uploaded_file_info.get('file_url', '') or ""
            original_name = uploaded_file_info.get('original_name', '') or ""
        elif fee_file_info:
            file_id = file_id or fee_file_info.get('file_id', '') or "9999999999"
            file_name = file_name or fee_file_info.get('file_name', '') or ""
            file_url = file_url or fee_file_info.get('file_url', '') or ""
            original_name = original_name or fee_file_info.get('original_name', '') or ""
        else:
            file_id = file_id or file_cfg.get("file_id", "") or "9999999999"
            file_name = file_name or file_cfg.get("file_name", "") or ""
            file_url = file_url or file_cfg.get("file_url", "") or ""
            original_name = original_name or file_cfg.get("original_name", "") or ""

        # Step 1: invoiceAdd - 上传应收发票
        if invoice_number is None:
            invoice_number = InvoiceUploadApi.generate_unique_invoice_number(prefix="API_INV")
        if invoice_amount is None:
            invoice_amount = "1500"

        invoice_original = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": "pdf",
            "original_name": original_name,
            "file_url": file_url,
        }

        with allure.step('上传应收发票（invoiceAdd）'):
            add_resp = InvoiceUploadApi.invoice_add(
                invoice_number=invoice_number,
                invoice_amount=invoice_amount,
                invoice_original=invoice_original,
                buyer_chinese_header=buyer_chinese_header,
                buyer_identifier_no=buyer_identifier_no,
                seller_chinese_header=seller_chinese_header,
                seller_identifier_no=seller_identifier_no,
                invoice_image_name=file_name or "",
                file_path=file_url or "",
            )
            add_data = add_resp.json()
            result['add_resp'] = add_resp
            result['add_data'] = add_data
            result['invoice_number'] = invoice_number

            add_data_records = add_data.get("data", {}) or {}
            receive_invoice_id = add_data_records.get(invoice_number, "")
            result['receive_invoice_id'] = receive_invoice_id
            result['steps'].append({
                'name': '上传应收发票',
                'code': add_data.get('code'),
                'msg': add_data.get('msg'),
                'invoice_number': invoice_number,
                'receive_invoice_id': receive_invoice_id,
            })

            if not receive_invoice_id:
                cls._attach_context(result)
                raise AssertionError(f'invoiceAdd 响应中未找到 receive_invoice_id: {add_data}')

        # Step 2: applyPage - 按提单号查询发票申请ID
        with allure.step('获取发票申请ID（applyPage）'):
            apply_page_resp = InvoiceUploadApi.apply_page(bl_no=bl_no)
            apply_page_data = apply_page_resp.json()
            result['apply_page_resp'] = apply_page_resp
            result['apply_page_data'] = apply_page_data

            records = apply_page_data.get("data", {}).get("data", []) or []
            first = records[0] if records else {}
            receive_invoice_apply_id = first.get("receive_invoice_apply_id", "")
            result['receive_invoice_apply_id'] = receive_invoice_apply_id
            result['steps'].append({
                'name': '获取发票申请ID',
                'code': apply_page_data.get('code'),
                'msg': apply_page_data.get('msg'),
                'receive_invoice_apply_id': receive_invoice_apply_id,
                'record_count': len(records),
            })

            if not receive_invoice_apply_id:
                cls._attach_context(result)
                raise AssertionError(f'applyPage 响应中未找到 receive_invoice_apply_id: {apply_page_data}')

        # Step 3: allocationInvoiceFee - 登记发票到申请
        with allure.step('登记发票到申请（allocationInvoiceFee）'):
            # un_amount 来自 applyPage 第一条记录的 invoice_unused_amount
            un_amount = first.get("invoice_unused_amount") or first.get("turn_cost_cny") or invoice_amount
            invoice_arr = [{
                "receive_invoice_id": str(receive_invoice_id),
                "invoice_amount_use": str(un_amount),
            }]
            alloc_resp = InvoiceUploadApi.allocation_invoice_fee(
                receive_invoice_apply_id=receive_invoice_apply_id,
                invoice_arr=invoice_arr,
            )
            alloc_data = alloc_resp.json()
            result['alloc_resp'] = alloc_resp
            result['alloc_data'] = alloc_data
            result['steps'].append({
                'name': '登记发票到申请',
                'code': alloc_data.get('code'),
                'msg': alloc_data.get('msg'),
                'receive_invoice_apply_id': receive_invoice_apply_id,
            })

        cls._attach_context(result)
        return result

        # Step 3: allocationInvoiceFee - 登记发票到申请
        with allure.step('登记发票到申请（allocationInvoiceFee）'):
            # 使用 detail_data 中的 un_amount 作为登记金额
            un_amount = detail_data.get("data", {}).get("un_amount", invoice_amount) or invoice_amount
            invoice_arr = [{
                "receive_invoice_id": str(receive_invoice_id),
                "invoice_amount_use": str(un_amount),
            }]
            alloc_resp = InvoiceUploadApi.allocation_invoice_fee(
                receive_invoice_apply_id=receive_invoice_apply_id,
                invoice_arr=invoice_arr,
            )
            alloc_data = alloc_resp.json()
            result['alloc_resp'] = alloc_resp
            result['alloc_data'] = alloc_data
            result['steps'].append({
                'name': '登记发票到申请',
                'code': alloc_data.get('code'),
                'msg': alloc_data.get('msg'),
                'receive_invoice_apply_id': receive_invoice_apply_id,
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_generate_fee_confirm(
        cls,
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

        cls._attach_context(result)
        return result

    @classmethod
    def record_supplier_advance(
        cls,
        order_id: str,
        bl_no: str,
    ) -> Dict[str, Any]:
        """
        录供应商垫付申请审批（发起审批 → 查询审批ID → 审批通过）

        Args:
            order_id: 业务订单ID
            bl_no   : 提单号（用于查询筛选）

        Returns:
            {
                'order_id': str,
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

        # 1) 发起供应商垫付申请审批
        with allure.step('发起供应商垫付申请审批'):
            send_resp = AuditApi.send_add_special_payment_flag(order_id=order_id)
            send_data = send_resp.json()
            result['send_resp'] = send_resp
            result['send_data'] = send_data
            result['steps'].append({
                'name': '发起供应商垫付申请审批',
                'code': send_data.get('code'),
                'msg': send_data.get('msg'),
            })

        # 2) 查询审批ID
        with allure.step('查询供应商垫付申请审批ID'):
            query_resp = AuditApi.query_pending_audits(
                audit_type='addSpecialPaymentFlag',
                audit_status=['1'],
                page_no=1,
                page_size=1,
                active_tab='examine_wait',
                bl_no=bl_no,
                sort_field='expedite_num',
                sort_order='desc',
            )
            query_data = query_resp.json()
            records = query_data.get('data', {}).get('data', [])
            first = records[0] if records else {}
            audit_id = first.get('audit_id', '')
            result['query_resp'] = query_resp
            result['query_data'] = query_data
            result['audit_id'] = audit_id
            result['steps'].append({
                'name': '查询供应商垫付申请审批ID',
                'code': query_data.get('code'),
                'msg': query_data.get('msg'),
                'audit_id': audit_id,
            })

        # 3) 审批通过
        with allure.step('供应商垫付申请审批通过'):
            approve_resp = AuditApi.audit_execute(
                audit_ids=[audit_id] if audit_id else [],
                audit_status=2,
            )
            approve_data = approve_resp.json()
            result['approve_resp'] = approve_resp
            result['approve_data'] = approve_data
            result['steps'].append({
                'name': '供应商垫付申请审批通过',
                'code': approve_data.get('code'),
                'msg': approve_data.get('msg'),
            })

        cls._attach_context(result)
        return result

    @classmethod
    def record_invoice_apply(
        cls,
        order_id: str,
        bl_no: str,
    ) -> Dict[str, Any]:
        """
        录未放款开票申请审批（发起审批 → 查询审批ID → 审批通过）

        Args:
            order_id: 业务订单ID
            bl_no   : 提单号（用于查询筛选）

        Returns:
            {
                'order_id': str,
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

        # 1) 发起未放款开票申请审批
        with allure.step('发起未放款开票申请审批'):
            send_resp = AuditApi.send_add_loan_before_invoice(order_id=order_id)
            send_data = send_resp.json()
            result['send_resp'] = send_resp
            result['send_data'] = send_data
            result['steps'].append({
                'name': '发起未放款开票申请审批',
                'code': send_data.get('code'),
                'msg': send_data.get('msg'),
            })

        # 2) 查询审批ID
        with allure.step('查询未放款开票申请审批ID'):
            query_resp = AuditApi.query_pending_audits(
                audit_type='addLoanBeforeInvoiceApply',
                audit_status=['1'],
                page_no=1,
                page_size=1,
                active_tab='examine_wait',
                bl_no=bl_no,
                sort_field='expedite_num',
                sort_order='desc',
            )
            query_data = query_resp.json()
            records = query_data.get('data', {}).get('data', [])
            first = records[0] if records else {}
            audit_id = first.get('audit_id', '')
            result['query_resp'] = query_resp
            result['query_data'] = query_data
            result['audit_id'] = audit_id
            result['steps'].append({
                'name': '查询未放款开票申请审批ID',
                'code': query_data.get('code'),
                'msg': query_data.get('msg'),
                'audit_id': audit_id,
            })

        # 3) 审批通过
        with allure.step('未放款开票申请审批通过'):
            approve_resp = AuditApi.audit_execute(
                audit_ids=[audit_id] if audit_id else [],
                audit_status=2,
            )
            approve_data = approve_resp.json()
            result['approve_resp'] = approve_resp
            result['approve_data'] = approve_data
            result['steps'].append({
                'name': '未放款开票申请审批通过',
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
                - 'invoice_apply'      新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批 + 订单锁定审批 + 未放款开票申请审批
                - 'supplier_advance'   新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批
                - 'fee_notice'         新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 生成费用通知单
                - 'fee_confirm'        新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单 + 录费用 + 资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 生成费用通知单 + 生成费用确认单
                - 'receive_account'   新建 + ... + 生成费用通知单 + 生成费用确认单 + 发起应收对账批次
                - 'confirm_account'  新建 + ... + 发起应收对账批次 + 确认应收对账
                - 'invoice_batch'    新建 + ... + 确认应收对账 + 发起应收开票批次审批
                - 'invoice_batch_audit' 新建 + ... + 发起应收开票批次审批 + 审核生成开票申请
                - 'invoice_upload'   新建 + ... + 审核生成开票申请 + 发票上传与登记
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
        if stop_at in ('generate_sub_order', 'record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
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
        if stop_at in ('record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step(f'[{stop_at}] Step8: 录费用'):
                order_id = after_submit_order.get('order_id')
                audit_after = stop_at in ('record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload')
                fee_result = cls.record_fee(
                    order_id=order_id,
                    fee_configs=fee_configs or [],
                    audit_after_fee=audit_after,
                )
                result['record_fee_results'] = fee_result['results']
                result['steps'].extend(fee_result['steps'])

        # assetPush 已在 record_fee 内部完成（audit_after_fee=True）

        # Step 10: 订单锁定审批
        if stop_at in ('order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step(f'[{stop_at}] Step10: 订单锁定审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起订单锁定审批')
                lock_result = cls.record_order_lock(order_id=order_id, bl_no=bl_no)
                result['order_lock_result'] = lock_result
                result['steps'].extend(lock_result['steps'])

        # Step 11: 未放款开票申请审批
        if stop_at in ('invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[invoice_apply] Step11: 未放款开票申请审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起未放款开票申请审批')
                invoice_result = cls.record_invoice_apply(order_id=order_id, bl_no=bl_no)
                result['invoice_apply_result'] = invoice_result
                result['steps'].extend(invoice_result['steps'])

        # Step 12: 供应商垫付申请审批
        if stop_at in ('supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[supplier_advance] Step12: 供应商垫付申请审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起供应商垫付申请审批')
                advance_result = cls.record_supplier_advance(order_id=order_id, bl_no=bl_no)
                result['supplier_advance_result'] = advance_result
                result['steps'].extend(advance_result['steps'])

        # Step 13: 生成费用通知单
        if stop_at in ('fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[fee_notice] Step13: 生成费用通知单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成费用通知单')
                notice_result = cls.record_generate_fee_notice(order_id=order_id)
                result['fee_notice_result'] = notice_result
                result['steps'].extend(notice_result['steps'])

        # Step 14: 生成费用确认单
        if stop_at in ('fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[fee_confirm] Step14: 生成费用确认单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成费用确认单')
                confirm_result = cls.record_generate_fee_confirm(order_id=order_id)
                result['fee_confirm_result'] = confirm_result
                result['steps'].extend(confirm_result['steps'])

        # Step 15: 发起应收对账批次
        if stop_at in ('receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[receive_account] Step15: 发起应收对账批次'):
                # 从 fee_confirm_result 中提取结算对象信息
                confirm_result = result.get('fee_confirm_result')
                if not confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('fee_confirm_result 不存在，无法发起应收对账批次')

                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起应收对账批次')

                # 从 fee_confirm 结果中提取结算对象信息
                fee_confirm_data = confirm_result.get('data', {}).get('data', {})

                # put_settle_object_id 从 fee.yaml 客户配置中提取（托单结算对象）
                put_settle_object_id = BookRealAmountData.get_customer_settle_object_id()
                # put_settle_object / main_id 从 after_submit_order 中提取
                submit_order = result.get('after_submit_order', {})
                put_settle_object = submit_order.get('put_settle_object', '')
                # main_id 优先取 order 数据，没有则回退 YAML 默认值
                main_id = submit_order.get('main_id') or _default_main_id()

                if not put_settle_object_id:
                    cls._attach_context(result)
                    raise AssertionError('fee.yaml 客户费用配置中缺少 settle_object_id，无法发起应收对账批次')

                receive_result = cls.record_receive_account(
                    bl_no=bl_no,
                    put_settle_object_id=put_settle_object_id,
                    main_id=main_id,
                    put_settle_object=put_settle_object,
                )
                result['receive_account_result'] = receive_result
                result['steps'].extend(receive_result['steps'])

        # Step 16: 确认应收对账
        if stop_at in ('confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[confirm_account] Step16: 确认应收对账'):
                receive_result = result.get('receive_account_result')
                if not receive_result:
                    cls._attach_context(result)
                    raise AssertionError('receive_account_result 不存在，无法确认应收对账')

                receive_account_id = receive_result.get('receive_account_id')
                if not receive_account_id:
                    cls._attach_context(result)
                    raise AssertionError('receive_account_id 不存在，无法确认应收对账')

                confirm_result = cls.record_confirm_account(
                    receive_account_id=receive_account_id,
                    bl_no=bl_no,
                )
                result['confirm_account_result'] = confirm_result
                result['steps'].extend(confirm_result['steps'])

        # Step 17: 发起应收开票批次审批
        if stop_at in ('invoice_batch', 'invoice_batch_audit', 'invoice_upload'):
            with allure.step('[invoice_batch] Step17: 发起应收开票批次审批'):
                confirm_result = result.get('confirm_account_result')
                if not confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('confirm_account_result 不存在，无法发起应收开票批次审批')

                # 从 fee_confirm_result 中提取结算对象信息
                fee_confirm_result = result.get('fee_confirm_result')
                if not fee_confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('fee_confirm_result 不存在，无法发起应收开票批次审批')

                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起应收开票批次审批')

                # put_settle_object_id 从 fee.yaml 客户配置中提取（托单结算对象）
                put_settle_object_id = BookRealAmountData.get_customer_settle_object_id()
                submit_order = result.get('after_submit_order', {})
                put_settle_object = submit_order.get('put_settle_object', '')
                main_id = submit_order.get('main_id') or _default_main_id()
                main_name = submit_order.get('main_name', '')

                if not put_settle_object_id:
                    cls._attach_context(result)
                    raise AssertionError('fee.yaml 客户费用配置中缺少 settle_object_id，无法发起应收开票批次审批')

                # 从 fee_confirm_result 中提取费用行数据，构建 order_fee_real_ids
                fee_confirm_data = fee_confirm_result.get('data', {}).get('data', {})
                fee_list = fee_confirm_data.get('fee_list', []) or []

                order_fee_real_ids = [str(item.get('order_fee_real_id', '')) for item in fee_list]
                order_sub_ids = [str(after_submit_order.get('order_sub_id', ''))]
                order_sub_customer_ids = [str(after_submit_order.get('customer_id', ''))]

                invoice_result = cls.record_invoice_batch(
                    bl_no=bl_no,
                    put_settle_object_id=put_settle_object_id,
                    main_id=main_id,
                    put_settle_object=put_settle_object,
                    main_name=main_name,
                    order_fee_real_ids=order_fee_real_ids,
                    order_sub_ids=order_sub_ids,
                    order_sub_customer_ids=order_sub_customer_ids,
                )
                result['invoice_batch_result'] = invoice_result
                result['steps'].extend(invoice_result['steps'])

        # Step 18: 审核生成开票申请（stop_at 为 invoice_batch_audit 或 invoice_upload 时都需执行）
        if stop_at in ('invoice_batch_audit', 'invoice_upload'):
            with allure.step('[invoice_batch_audit] Step18: 审核生成开票申请'):
                invoice_batch_result = result.get('invoice_batch_result')
                if not invoice_batch_result:
                    cls._attach_context(result)
                    raise AssertionError('invoice_batch_result 不存在，无法审核生成开票申请')

                batch_id = invoice_batch_result.get('batch_id')
                if not batch_id:
                    cls._attach_context(result)
                    raise AssertionError('batch_id 不存在，无法审核生成开票申请')

                audit_result = cls.record_invoice_batch_audit(batch_id=batch_id)
                result['invoice_batch_audit_result'] = audit_result
                result['steps'].extend(audit_result['steps'])

        # Step 19: 发票上传与登记
        if stop_at == 'invoice_upload':
            with allure.step('[invoice_upload] Step19: 发票上传与登记'):
                import logging
                _log = logging.getLogger(__name__)
                invoice_batch_result = result.get('invoice_batch_result')
                if not invoice_batch_result:
                    cls._attach_context(result)
                    raise AssertionError('invoice_batch_result 不存在，无法上传发票')

                batch_id = invoice_batch_result.get('batch_id')
                _log.info(f"[LK17 DEBUG] batch_id={batch_id}, bl_no={bl_no}")

                fee_notice_result = result.get('fee_notice_result', {})
                fee_file_info = fee_notice_result.get('file_info', {})
                invoice_file_path = f"{TEST_DATA_DIR}/invoice.pdf"
                upload_result = cls.record_invoice_upload(
                    bl_no=bl_no,
                    fee_file_info=fee_file_info,
                    invoice_file_path=invoice_file_path,
                )
                result['invoice_upload_result'] = upload_result
                result['steps'].extend(upload_result['steps'])

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

    @classmethod
    def run_until_invoice_apply(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到未放款开票申请审批阶段（含资产推送 + 订单锁定 + 未放款开票申请）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='invoice_apply',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_supplier_advance(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到供应商垫付申请审批阶段（含资产推送 + 订单锁定 + 未放款开票申请 + 供应商垫付申请）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='supplier_advance',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_fee_notice(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到生成费用通知单阶段（含资产推送 + 订单锁定 + 未放款开票申请 + 供应商垫付申请 + 费用通知单）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='fee_notice',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_fee_confirm(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到生成费用确认单阶段（含资产推送 + 订单锁定 + 未放款开票申请 + 供应商垫付申请 + 费用通知单 + 费用确认单）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='fee_confirm',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_receive_account(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到发起应收对账批次阶段（含资产推送 + 订单锁定 + 未放款开票申请 + 供应商垫付申请 + 费用通知单 + 费用确认单 + 应收对账批次）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='receive_account',
            fee_configs=fee_configs,
        )

    @classmethod
    def run_until_confirm_account(
        cls,
        fee_configs: List[Dict[str, Any]] = None,
        bl_no: str = None,
    ) -> Dict[str, Any]:
        """执行到确认应收对账阶段（含发起应收对账批次 + 确认应收对账）"""
        return cls.full_flow(
            bl_no=bl_no,
            stop_at='confirm_account',
            fee_configs=fee_configs,
        )
