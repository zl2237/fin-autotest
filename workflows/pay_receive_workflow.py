"""
订单流程编排 - pay_receive 工作流（默认：订单 → 应付 → 应收）

本文件按链路依赖树语义，将应付阶段（21~25）前置到应收阶段（13~18）之前执行。
与 receive_pay_workflow.py 共同覆盖两类 workflow 类型。
"""
import logging
from typing import Any, Dict, List

import allure

from workflows.order_workflow import OrderWorkflow
from workflows.pay_workflow import PayWorkflow
from workflows.receive_workflow import ReceiveWorkflow


_log = logging.getLogger(__name__)


class PayReceiveWorkflow:
    """
    默认 workflow：订单 → 应付 → 应收

    流程阶段：新建 → 分发 → [暂存] → 提交 → 生成子订单 → 录费用 → 审批流程
              → 应付对账 → 应付开票 → 付款需求 → 应收对账 → 应收开票 → 应收核销

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

    @classmethod
    def run(cls, bl_no: str = None, stop_at: str = 'submit', skip_stash: bool = False, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行完整流程：订单 → 应付 → 应收，stop_at 控制停止阶段

        Args:
            bl_no: 提单号，默认自动生成
            stop_at: 执行到哪个阶段后停止，可选值：
                - 'create'              仅新建
                - 'distribute'         新建 + 分发
                - 'stash'              新建 + 分发 + 查询 + 暂存
                - 'submit'             新建 + 分发 + 查询 + 暂存 + 提交（默认）
                - 'generate_sub_order' 新建 + 分发 + 查询 + 暂存 + 提交 + 生成子订单
                - 'record_fee'         新建 + ... + 生成子订单 + 录费用
                - 'record_audit'       新建 + ... + 录费用 + 资产推送审批
                - 'order_lock'         新建 + ... + 资产推送审批 + 订单锁定审批
                - 'invoice_apply'      新建 + ... + 订单锁定审批 + 未放款开票申请审批
                - 'supplier_advance'   新建 + ... + 未放款开票申请审批 + 供应商垫付申请审批
                - 'fee_notice'         新建 + ... + 供应商垫付申请审批 + 生成费用通知单
                - 'fee_confirm'        新建 + ... + 生成费用通知单 + 生成费用确认单
                - 'payable'            新建 + ... + 生成费用确认单 + 发起应付对账批次
                - 'confirm_payable'    新建 + ... + 发起应付对账批次 + 确认应付对账
                - 'payable_invoice_apply' 新建 + ... + 确认应付对账 + 发起应付开票批次申请
                - 'payable_invoice_register' 新建 + ... + 发起应付开票批次申请 + 应付发票上传与登记
                - 'pay_demand'         新建 + ... + 应付发票上传与登记 + 发起付款需求
                - 'pay_demand_audit'   新建 + ... + 发起付款需求 + 审核生成付款单
                - 'pay_writeoff'       新建 + ... + 审核生成付款单 + 付款单核销
                - 'receive_account'    新建 + ... + 付款单核销 + 发起应收对账批次
                - 'confirm_account'    新建 + ... + 发起应收对账批次 + 确认应收对账
                - 'invoice_batch'      新建 + ... + 确认应收对账 + 发起应收开票批次审批
                - 'invoice_batch_audit' 新建 + ... + 发起应收开票批次审批 + 审核生成开票申请
                - 'invoice_upload'     新建 + ... + 审核生成开票申请 + 发票上传与登记
                - 'receive_writeoff'   新建 + ... + 发票上传与登记 + 应收核销
            skip_stash: 是否跳过暂存
            fee_configs: 录费用配置列表（stop_at='record_fee' 时使用）

        Returns:
            与 OrderWorkflow.run 相同的 result 结构，并追加应付/应收阶段结果
        """
        if stop_at in ('create', 'distribute', 'stash', 'submit', 'generate_sub_order', 'record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm'):
            return OrderWorkflow.run(bl_no=bl_no, stop_at=stop_at, skip_stash=skip_stash, fee_configs=fee_configs)

        order_result = OrderWorkflow.run(bl_no=bl_no, stop_at='fee_confirm', skip_stash=skip_stash, fee_configs=fee_configs)

        pay_stops = ('payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit', 'pay_writeoff')
        receive_stops = ('receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff')

        # pay_receive: 应付 → 应收
        # 如果 stop_at 在应收阶段，需要先把应付跑完（stop_at='pay_writeoff'），再跑应收
        if stop_at in receive_stops:
            order_result = PayWorkflow.run(bl_no=bl_no, stop_at='pay_writeoff', fee_configs=fee_configs, order_result=order_result)
            order_result = ReceiveWorkflow.run(bl_no=bl_no, stop_at=stop_at, fee_configs=fee_configs, order_result=order_result)
            return order_result
        if stop_at in pay_stops:
            order_result = PayWorkflow.run(bl_no=bl_no, stop_at=stop_at, fee_configs=fee_configs, order_result=order_result)
            return order_result

        raise ValueError(f"不支持的 stop_at: {stop_at}")

    # =====================
    # 快捷方法
    # =====================

    @classmethod
    def run_until_create(cls, bl_no: str = None) -> Dict[str, Any]:
        """仅执行到新建阶段"""
        return cls.run(bl_no=bl_no, stop_at='create')

    @classmethod
    def run_until_distribute(cls, bl_no: str = None) -> Dict[str, Any]:
        """仅执行到分发阶段"""
        return cls.run(bl_no=bl_no, stop_at='distribute')

    @classmethod
    def run_until_stash(cls, bl_no: str = None) -> Dict[str, Any]:
        """执行到暂存阶段"""
        return cls.run(bl_no=bl_no, stop_at='stash')

    @classmethod
    def run_until_generate_sub_order(cls, bl_no: str = None) -> Dict[str, Any]:
        """执行到生成子订单阶段"""
        return cls.run(bl_no=bl_no, stop_at='generate_sub_order')

    @classmethod
    def run_until_record_fee(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到录费用阶段"""
        return cls.run(bl_no=bl_no, stop_at='record_fee', fee_configs=fee_configs)

    @classmethod
    def run_until_record_audit(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到资产推送审批阶段"""
        return cls.run(bl_no=bl_no, stop_at='record_audit', fee_configs=fee_configs)

    @classmethod
    def run_until_order_lock(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到订单锁定审批阶段"""
        return cls.run(bl_no=bl_no, stop_at='order_lock', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_apply(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到未放款开票申请审批阶段"""
        return cls.run(bl_no=bl_no, stop_at='invoice_apply', fee_configs=fee_configs)

    @classmethod
    def run_until_supplier_advance(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到供应商垫付申请审批阶段"""
        return cls.run(bl_no=bl_no, stop_at='supplier_advance', fee_configs=fee_configs)

    @classmethod
    def run_until_fee_notice(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到生成费用通知单阶段"""
        return cls.run(bl_no=bl_no, stop_at='fee_notice', fee_configs=fee_configs)

    @classmethod
    def run_until_fee_confirm(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到生成费用确认单阶段"""
        return cls.run(bl_no=bl_no, stop_at='fee_confirm', fee_configs=fee_configs)

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

    @classmethod
    def run_until_receive_account(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到发起应收对账批次阶段"""
        return cls.run(bl_no=bl_no, stop_at='receive_account', fee_configs=fee_configs)

    @classmethod
    def run_until_confirm_account(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到确认应收对账阶段"""
        return cls.run(bl_no=bl_no, stop_at='confirm_account', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_batch(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到发起应收开票批次阶段"""
        return cls.run(bl_no=bl_no, stop_at='invoice_batch', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_batch_audit(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到审核生成开票申请阶段"""
        return cls.run(bl_no=bl_no, stop_at='invoice_batch_audit', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_upload(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到发票上传与登记阶段"""
        return cls.run(bl_no=bl_no, stop_at='invoice_upload', fee_configs=fee_configs)

    @classmethod
    def run_until_receive_writeoff(cls, bl_no: str = None, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行到应收核销阶段"""
        return cls.run(bl_no=bl_no, stop_at='receive_writeoff', fee_configs=fee_configs)
