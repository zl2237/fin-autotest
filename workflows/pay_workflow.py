"""
应付流程编排 - 串联订单应付阶段 API，自动处理数据依赖

本文件只负责按 stop_at 编排，订单前置流程由 OrderWorkflow.run(stop_at=...) 提供。
"""
import logging
from typing import Any, Dict, List

import allure

from workflows.order_workflow import OrderWorkflow
from workflows.pay import (
    confirm_payable_account as _confirm_payable_account,
    record_pay_demand as _record_pay_demand,
    audit_pay_demand as _audit_pay_demand,
    record_payable_account as _record_payable_account,
    record_payable_invoice_apply as _record_payable_invoice_apply,
    record_payable_invoice_upload as _record_payable_invoice_upload,
    writeoff_pay_demand as _writeoff_pay_demand,
)


_log = logging.getLogger(__name__)


class PayWorkflow:
    """
    应付完整生命周期编排

    流程阶段：发起应付对账 → 确认应付对账 → 发起应付开票批次申请
             → 应付发票上传与登记 → 发起付款需求 → 审核生成付款单 → 付款单核销
    """

    @classmethod
    def _attach_context(cls, result: Dict[str, Any]):
        allure.attach(
            str(result),
            name="Workflow 执行结果",
            attachment_type=allure.attachment_type.JSON
        )

    @classmethod
    def run(cls, bl_no: str = None, stop_at: str = 'pay_writeoff', fee_configs: List[Dict[str, Any]] = None, order_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行完整应付流程，stop_at 控制停止阶段

        Args:
            bl_no: 提单号，默认自动生成
            stop_at: 执行到哪个阶段后停止，可选值：
                - 'payable'            发起应付对账批次
                - 'confirm_payable'    发起应付对账批次 + 确认应付对账
                - 'payable_invoice_apply' 发起应付对账批次 + 确认应付对账 + 发起应付开票批次申请
                - 'payable_invoice_register' 发起应付对账批次 + 确认应付对账 + 发起应付开票批次申请 + 应付发票上传与登记
                - 'pay_demand'         发起应付对账批次 + 确认应付对账 + 发起应付开票批次申请 + 应付发票上传与登记 + 发起付款需求
                - 'pay_demand_audit'   发起应付对账批次 + 确认应付对账 + 发起应付开票批次申请 + 应付发票上传与登记 + 发起付款需求 + 审核生成付款单
                - 'pay_writeoff'       发起应付对账批次 + 确认应付对账 + 发起应付开票批次申请 + 应付发票上传与登记 + 发起付款需求 + 审核生成付款单 + 付款单核销（默认）
            fee_configs: 录费用配置列表（当前未使用，保留扩展）
            order_result: 订单阶段结果，如果提供则跳过订单流程

        Returns:
            应付阶段执行结果
        """
        if order_result is None:
            if bl_no is None:
                bl_no = OrderWorkflow.run(stop_at='fee_confirm')['bl_no']
            order_result = OrderWorkflow.run(stop_at='fee_confirm', bl_no=bl_no)
        else:
            bl_no = bl_no or order_result['bl_no']

        after_submit_order = order_result.get('after_submit_order', {})
        result = {
            'bl_no': bl_no,
            'steps': [],
        }
        result.update(order_result)
        result['stop_at'] = stop_at

        # Step 1: 发起应付对账批次
        if stop_at in ('payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit', 'pay_writeoff'):
            with allure.step('[payable] Step1: 发起应付对账批次'):
                payable_result = _record_payable_account(bl_no=bl_no)
                result['payable_account_result'] = payable_result
                result['steps'].extend(payable_result['steps'])

        # Step 2: 确认应付对账
        if stop_at in ('confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit', 'pay_writeoff'):
            with allure.step('[confirm_payable] Step2: 确认应付对账'):
                payable_result = result.get('payable_account_result')
                if not payable_result:
                    cls._attach_context(result)
                    raise AssertionError('payable_account_result 不存在，无法确认应付对账')
                pay_account_id = payable_result.get('pay_account_id')
                confirm_result = _confirm_payable_account(
                    bl_no=bl_no,
                    pay_account_id=pay_account_id,
                )
                result['confirm_payable_result'] = confirm_result
                result['steps'].extend(confirm_result['steps'])

        # Step 3: 发起应付开票批次申请
        if stop_at in ('payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit', 'pay_writeoff'):
            with allure.step('[payable_invoice_apply] Step3: 发起应付开票批次申请'):
                confirm_result = result.get('confirm_payable_result')
                if not confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('confirm_payable_result 不存在，无法发起应付开票批次申请')

                submit_order = result.get('after_submit_order', {})
                main_id = (
                    confirm_result.get('main_id')
                    or submit_order.get('main_id')
                )
                main_name = (
                    confirm_result.get('main_name')
                    or submit_order.get('main_name')
                )
                pay_settle_object = (
                    confirm_result.get('pay_settle_object')
                    or submit_order.get('pay_settle_object')
                )
                pay_settle_object_id = (
                    confirm_result.get('pay_settle_object_id')
                    or submit_order.get('pay_settle_object_id')
                )

                invoice_result = _record_payable_invoice_apply(
                    bl_no=bl_no,
                    main_id=main_id,
                    main_name=main_name,
                    pay_settle_object=pay_settle_object,
                    pay_settle_object_id=pay_settle_object_id,
                )
                result['payable_invoice_apply_result'] = invoice_result
                result['steps'].extend(invoice_result['steps'])

        # Step 4: 应付发票上传与登记
        if stop_at in ('payable_invoice_register', 'pay_demand', 'pay_demand_audit', 'pay_writeoff'):
            with allure.step('[payable_invoice_register] Step4: 应付发票上传与登记'):
                invoice_apply_result = result.get('payable_invoice_apply_result')
                if not invoice_apply_result:
                    cls._attach_context(result)
                    raise AssertionError(
                        'payable_invoice_apply_result 不存在，无法继续应付发票上传与登记'
                    )
                upload_result = _record_payable_invoice_upload(bl_no=bl_no)
                result['payable_invoice_register_result'] = upload_result
                result['steps'].extend(upload_result['steps'])

        # Step 5: 发起付款需求
        if stop_at in ('pay_demand', 'pay_demand_audit', 'pay_writeoff'):
            with allure.step('[pay_demand] Step5: 发起付款需求'):
                invoice_apply_result = result.get('payable_invoice_apply_result', {})
                confirm_result = result.get('confirm_payable_result', {})
                payable_result = result.get('payable_account_result', {})
                submit_order = result.get('after_submit_order', {})

                main_id = (
                    invoice_apply_result.get('main_id')
                    or confirm_result.get('main_id')
                    or payable_result.get('main_id')
                    or submit_order.get('main_id')
                )
                pay_settle_object_id = (
                    invoice_apply_result.get('pay_settle_object_id')
                    or confirm_result.get('pay_settle_object_id')
                    or payable_result.get('pay_settle_object_id')
                    or submit_order.get('pay_settle_object_id')
                )
                main_name = (
                    invoice_apply_result.get('main_name')
                    or confirm_result.get('main_name')
                    or payable_result.get('main_name')
                    or submit_order.get('main_name')
                )
                pay_settle_object = (
                    invoice_apply_result.get('pay_settle_object')
                    or confirm_result.get('pay_settle_object')
                    or payable_result.get('pay_settle_object')
                    or submit_order.get('pay_settle_object')
                )

                demand_result = _record_pay_demand(
                    bl_no=bl_no,
                    main_id=main_id,
                    main_name=main_name,
                    pay_settle_object_id=pay_settle_object_id,
                    pay_settle_object=pay_settle_object,
                )
                result['pay_demand_result'] = demand_result
                result['steps'].extend(demand_result['steps'])

        # Step 6: 审核生成付款单
        if stop_at in ('pay_demand_audit', 'pay_writeoff'):
            with allure.step('[pay_demand_audit] Step6: 审核生成付款单'):
                audit_result = _audit_pay_demand(bl_no=bl_no)
                result['pay_demand_audit_result'] = audit_result
                result['steps'].extend(audit_result['steps'])

        # Step 7: 付款单核销
        if stop_at == 'pay_writeoff':
            with allure.step('[pay_writeoff] Step7: 付款单核销'):
                writeoff_result = _writeoff_pay_demand(bl_no=bl_no)
                result['pay_writeoff_result'] = writeoff_result
                result['steps'].extend(writeoff_result['steps'])

        cls._attach_context(result)
        return result

    # =====================
    # 快捷方法
    # =====================

    @classmethod
    def run_until_payable_account(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到发起应付对账批次阶段"""
        return cls.run(bl_no=bl_no, stop_at='payable', fee_configs=fee_configs)

    @classmethod
    def run_until_confirm_payable(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到确认应付对账阶段"""
        return cls.run(bl_no=bl_no, stop_at='confirm_payable', fee_configs=fee_configs)

    @classmethod
    def run_until_payable_invoice_apply(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到发起应付开票批次申请阶段"""
        return cls.run(bl_no=bl_no, stop_at='payable_invoice_apply', fee_configs=fee_configs)

    @classmethod
    def run_until_payable_invoice_register(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到应付发票上传与登记阶段"""
        return cls.run(bl_no=bl_no, stop_at='payable_invoice_register', fee_configs=fee_configs)

    @classmethod
    def run_until_pay_demand(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到发起付款需求阶段"""
        return cls.run(bl_no=bl_no, stop_at='pay_demand', fee_configs=fee_configs)

    @classmethod
    def run_until_pay_demand_audit(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到审核生成付款单阶段"""
        return cls.run(bl_no=bl_no, stop_at='pay_demand_audit', fee_configs=fee_configs)

    @classmethod
    def run_until_pay_writeoff(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到付款单核销阶段"""
        return cls.run(bl_no=bl_no, stop_at='pay_writeoff', fee_configs=fee_configs)
