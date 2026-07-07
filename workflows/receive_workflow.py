"""
应收流程编排 - 串联订单应收阶段 API，自动处理数据依赖

本文件只负责按 stop_at 编排，订单前置流程由 OrderWorkflow.run(stop_at=...) 提供。
"""
import logging
import time
from typing import Any, Dict, List

import allure

from api.receive.receive_account_api import _default_main_id
from config.settings import TEST_DATA_DIR
from data.order import BookRealAmountData
from data.receive import INVOICE_UPLOAD_INVOICE_FILENAME
from workflows.order_workflow import OrderWorkflow
from workflows.receive import (
    record_confirm_account as _record_confirm_account,
    record_invoice_batch as _record_invoice_batch,
    record_invoice_batch_audit as _record_invoice_batch_audit,
    record_invoice_upload as _record_invoice_upload,
    record_receive_account as _record_receive_account,
    record_receive_writeoff as _record_receive_writeoff,
)


_log = logging.getLogger(__name__)


class ReceiveWorkflow:
    """
    应收完整生命周期编排

    流程阶段：发起应收对账 → 确认应收对账 → 发起应收开票批次审批
             → 审核生成开票申请 → 发票上传与登记 → 应收核销
    """

    @classmethod
    def _attach_context(cls, result: Dict[str, Any]):
        allure.attach(
            str(result),
            name="Workflow 执行结果",
            attachment_type=allure.attachment_type.JSON
        )

    @classmethod
    def run(cls, bl_no: str = None, stop_at: str = 'receive_writeoff', fee_configs: List[Dict[str, Any]] = None, order_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行完整应收流程，stop_at 控制停止阶段

        Args:
            bl_no: 提单号，默认自动生成
            stop_at: 执行到哪个阶段后停止，可选值：
                - 'receive_account'    发起应收对账批次
                - 'confirm_account'    发起应收对账批次 + 确认应收对账
                - 'invoice_batch'      发起应收对账批次 + 确认应收对账 + 发起应收开票批次审批
                - 'invoice_batch_audit' 发起应收对账批次 + 确认应收对账 + 发起应收开票批次审批 + 审核生成开票申请
                - 'invoice_upload'     发起应收对账批次 + 确认应收对账 + 发起应收开票批次审批 + 审核生成开票申请 + 发票上传与登记
                - 'receive_writeoff'   发起应收对账批次 + 确认应收对账 + 发起应收开票批次审批 + 审核生成开票申请 + 发票上传与登记 + 应收核销（默认）
            fee_configs: 录费用配置列表（当前未使用，保留扩展）
            order_result: 订单阶段结果，如果提供则跳过订单流程

        Returns:
            应收阶段执行结果
        """
        if order_result is None:
            if bl_no is None:
                bl_no = OrderWorkflow.run(stop_at='fee_confirm')['bl_no']
            order_result = OrderWorkflow.run(stop_at='fee_confirm', bl_no=bl_no)
        else:
            bl_no = bl_no or order_result['bl_no']

        after_submit_order = order_result.get('after_submit_order', {})
        fee_confirm_result = order_result.get('fee_confirm_result', {})

        result = {
            'bl_no': bl_no,
            'steps': [],
        }
        result.update(order_result)
        result['stop_at'] = stop_at

        # Step 1: 发起应收对账批次
        if stop_at in ('receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff'):
            with allure.step('[receive_account] Step1: 发起应收对账批次'):
                confirm_result = result.get('fee_confirm_result')
                if not confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('fee_confirm_result 不存在，无法发起应收对账批次')

                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起应收对账批次')

                fee_confirm_data = confirm_result.get('data', {}).get('data', {})
                put_settle_object_id = BookRealAmountData.get_customer_settle_object_id()
                submit_order = result.get('after_submit_order', {})
                put_settle_object = submit_order.get('put_settle_object', '')
                main_id = submit_order.get('main_id') or _default_main_id()

                if not put_settle_object_id:
                    cls._attach_context(result)
                    raise AssertionError('fee.yaml 客户费用配置中缺少 settle_object_id，无法发起应收对账批次')

                receive_result = _record_receive_account(
                    bl_no=bl_no,
                    put_settle_object_id=put_settle_object_id,
                    main_id=main_id,
                    put_settle_object=put_settle_object,
                )
                result['receive_account_result'] = receive_result
                result['steps'].extend(receive_result['steps'])

        # Step 2: 确认应收对账
        if stop_at in ('confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff'):
            with allure.step('[confirm_account] Step2: 确认应收对账'):
                receive_result = result.get('receive_account_result')
                if not receive_result:
                    cls._attach_context(result)
                    raise AssertionError('receive_account_result 不存在，无法确认应收对账')

                receive_account_id = receive_result.get('receive_account_id')
                if not receive_account_id:
                    cls._attach_context(result)
                    raise AssertionError('receive_account_id 不存在，无法确认应收对账')

                confirm_result = _record_confirm_account(
                    receive_account_id=receive_account_id,
                    bl_no=bl_no,
                )
                result['confirm_account_result'] = confirm_result
                result['steps'].extend(confirm_result['steps'])

        # Step 3: 发起应收开票批次审批
        if stop_at in ('invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff'):
            with allure.step('[invoice_batch] Step3: 发起应收开票批次审批'):
                confirm_result = result.get('confirm_account_result')
                if not confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('confirm_account_result 不存在，无法发起应收开票批次审批')

                fee_confirm_result = result.get('fee_confirm_result')
                if not fee_confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('fee_confirm_result 不存在，无法发起应收开票批次审批')

                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起应收开票批次审批')

                put_settle_object_id = BookRealAmountData.get_customer_settle_object_id()
                submit_order = result.get('after_submit_order', {})
                put_settle_object = submit_order.get('put_settle_object', '')
                main_id = submit_order.get('main_id') or _default_main_id()
                main_name = submit_order.get('main_name', '')

                if not put_settle_object_id:
                    cls._attach_context(result)
                    raise AssertionError('fee.yaml 客户费用配置中缺少 settle_object_id，无法发起应收开票批次审批')

                fee_confirm_data = fee_confirm_result.get('data', {}).get('data', {})
                fee_list = fee_confirm_data.get('fee_list', []) or []

                order_fee_real_ids = [str(item.get('order_fee_real_id', '')) for item in fee_list]
                order_sub_ids = [str(after_submit_order.get('order_sub_id', ''))]
                order_sub_customer_ids = [str(after_submit_order.get('customer_id', ''))]

                invoice_result = _record_invoice_batch(
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

        # Step 4: 审核生成开票申请（stop_at 为 invoice_batch_audit 或 invoice_upload 时都需执行）
        if stop_at in ('invoice_batch_audit', 'invoice_upload', 'receive_writeoff'):
            with allure.step('[invoice_batch_audit] Step4: 审核生成开票申请'):
                invoice_batch_result = result.get('invoice_batch_result')
                if not invoice_batch_result:
                    cls._attach_context(result)
                    raise AssertionError('invoice_batch_result 不存在，无法审核生成开票申请')

                batch_id = invoice_batch_result.get('batch_id')
                if not batch_id:
                    cls._attach_context(result)
                    raise AssertionError('batch_id 不存在，无法审核生成开票申请')

                audit_result = _record_invoice_batch_audit(batch_id=batch_id)
                result['invoice_batch_audit_result'] = audit_result
                result['steps'].extend(audit_result['steps'])

        # Step 5: 发票上传与登记
        if stop_at in ('invoice_upload', 'receive_writeoff'):
            with allure.step('[invoice_upload] Step5: 发票上传与登记'):
                invoice_batch_result = result.get('invoice_batch_result')
                if not invoice_batch_result:
                    cls._attach_context(result)
                    raise AssertionError('invoice_batch_result 不存在，无法上传发票')

                batch_id = invoice_batch_result.get('batch_id')
                _log.info(f"[LK17 DEBUG] batch_id={batch_id}, bl_no={bl_no}")

                fee_notice_result = result.get('fee_notice_result', {})
                fee_file_info = fee_notice_result.get('file_info', {})
                invoice_file_path = f"{TEST_DATA_DIR}/{INVOICE_UPLOAD_INVOICE_FILENAME}"
                upload_result = _record_invoice_upload(
                    bl_no=bl_no,
                    fee_file_info=fee_file_info,
                    invoice_file_path=invoice_file_path,
                )
                result['invoice_upload_result'] = upload_result
                result['steps'].extend(upload_result['steps'])

        # Step 6: 应收核销（feeTakePage + writeoffBatch）
        if stop_at in ('receive_writeoff',):
            with allure.step('[receive_writeoff] Step6: 应收核销'):
                from data.receive import (
                    RECEIVE_WRITEOFF_MAIN_ID as _RW_MAIN_ID,
                    RECEIVE_WRITEOFF_MAIN_NAME as _RW_MAIN_NAME,
                )
                submit_order = result.get('after_submit_order', {})
                writeoff_main_id = submit_order.get('main_id') or _RW_MAIN_ID
                writeoff_main_name = submit_order.get('main_name') or _RW_MAIN_NAME

                writeoff_result = _record_receive_writeoff(
                    bl_no=bl_no,
                    main_id=writeoff_main_id,
                    main_name=writeoff_main_name,
                )
                result['receive_writeoff_result'] = writeoff_result
                result['steps'].extend(writeoff_result['steps'])

        cls._attach_context(result)
        return result

    # =====================
    # 快捷方法
    # =====================

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
