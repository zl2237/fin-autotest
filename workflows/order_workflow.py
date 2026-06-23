"""
订单流程编排 - 串联订单各阶段 API，自动处理数据依赖

本文件仅保留编排门面：_attach_context / full_flow / run / run_until_xxx。
各业务子步骤（新建+分发、暂存、提交、生成子订单、审批、费用、应收对账、发票、核销）
已拆到 workflows/steps/ 子包按业务域分模块实现，本文件只负责按 stop_at 编排。
"""
import logging
import time
from typing import Any, Dict, List

import allure

from api.receive.receive_account_api import _default_main_id
from api.order import OrderApi
from config.settings import TEST_DATA_DIR
from data.order import (
    BookRealAmountData,
    generate_bl_no,
)
from data.receive import INVOICE_UPLOAD_INVOICE_FILENAME
from workflows.receive import (
    record_confirm_account as _record_confirm_account,
    record_invoice_batch as _record_invoice_batch,
    record_invoice_batch_audit as _record_invoice_batch_audit,
    record_invoice_upload as _record_invoice_upload,
    record_receive_account as _record_receive_account,
    record_receive_writeoff as _record_receive_writeoff,
)
from workflows.pay import (
    record_payable_account as _record_payable_account,
    confirm_payable_account as _confirm_payable_account,
    record_payable_invoice_apply as _record_payable_invoice_apply,
    record_payable_invoice_upload as _record_payable_invoice_upload,
    record_pay_demand as _record_pay_demand,
    audit_pay_demand as _audit_pay_demand,
)
from workflows.order import (
    generate_sub_order as _generate_sub_order,
    record_fee as _record_fee,
    record_generate_fee_confirm as _record_generate_fee_confirm,
    record_generate_fee_notice as _record_generate_fee_notice,
    record_invoice_apply as _record_invoice_apply,
    record_order_lock as _record_order_lock,
    record_supplier_advance as _record_supplier_advance,
    stash as _stash,
    submit as _submit,
)


_log = logging.getLogger(__name__)


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
                - 'receive_writeoff' 新建 + ... + 发票上传与登记 + 应收核销
                - 'payable'         新建 + ... + 应收核销 + 发起应付对账批次
                - 'confirm_payable' 新建 + ... + 发起应付对账批次 + 确认应付对账
                - 'payable_invoice_apply' 新建 + ... + 确认应付对账 + 发起应付开票批次申请
                - 'payable_invoice_register' 新建 + ... + 发起应付开票批次申请 + 应付发票上传与登记
                - 'pay_demand' 新建 + ... + 应付发票上传与登记 + 发起付款需求
                - 'pay_demand_audit' 新建 + ... + 发起付款需求 + 审核生成付款单
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
                'receive_writeoff_result': ...,
                'payable_account_result': ...,   # stop_at='payable' 时存在
                'confirm_payable_result': ...,  # stop_at='confirm_payable' 时存在
                'payable_invoice_apply_result': ...,  # stop_at='payable_invoice_apply' 时存在
                'payable_invoice_register_result': ...,  # stop_at='payable_invoice_register' 时存在
                'pay_demand_result': ...,  # stop_at='pay_demand' 时存在
                'pay_demand_audit_result': ...,  # stop_at='pay_demand_audit' 时存在
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
                stash_result = _stash(current_order, bl_no=bl_no)
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
            submit_result = _submit(submit_order, bl_no=bl_no)
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
        if stop_at in ('generate_sub_order', 'record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step(f'[{stop_at}] Step7: 生成子订单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成子订单')
                gen_result = _generate_sub_order(order_id)
                result['generate_sub_resp'] = gen_result['generate_sub_resp']
                result['generate_sub_data'] = gen_result['generate_sub_data']
                result['steps'].append({
                    'name': '生成子订单',
                    'code': gen_result['generate_sub_data'].get('code'),
                    'msg': gen_result['generate_sub_data'].get('msg'),
                    'order_id': order_id,
                })

        # Step 9: 录费用（含资产推送审计）
        if stop_at in ('record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step(f'[{stop_at}] Step8: 录费用'):
                order_id = after_submit_order.get('order_id')
                audit_after = stop_at in ('record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit')
                fee_result = _record_fee(
                    order_id=order_id,
                    fee_configs=fee_configs or [],
                    audit_after_fee=audit_after,
                )
                result['record_fee_results'] = fee_result['results']
                result['steps'].extend(fee_result['steps'])

        # assetPush 已在 record_fee 内部完成（audit_after_fee=True）

        # Step 10: 订单锁定审批
        if stop_at in ('order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step(f'[{stop_at}] Step10: 订单锁定审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起订单锁定审批')
                lock_result = _record_order_lock(order_id=order_id, bl_no=bl_no)
                result['order_lock_result'] = lock_result
                result['steps'].extend(lock_result['steps'])

        # Step 11: 未放款开票申请审批
        if stop_at in ('invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[invoice_apply] Step11: 未放款开票申请审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起未放款开票申请审批')
                invoice_result = _record_invoice_apply(order_id=order_id, bl_no=bl_no)
                result['invoice_apply_result'] = invoice_result
                result['steps'].extend(invoice_result['steps'])

        # Step 12: 供应商垫付申请审批
        if stop_at in ('supplier_advance', 'fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[supplier_advance] Step12: 供应商垫付申请审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起供应商垫付申请审批')
                advance_result = _record_supplier_advance(order_id=order_id, bl_no=bl_no)
                result['supplier_advance_result'] = advance_result
                result['steps'].extend(advance_result['steps'])

        # Step 13: 生成费用通知单
        if stop_at in ('fee_notice', 'fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[fee_notice] Step13: 生成费用通知单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成费用通知单')
                notice_result = _record_generate_fee_notice(order_id=order_id)
                result['fee_notice_result'] = notice_result
                result['steps'].extend(notice_result['steps'])

        # Step 14: 生成费用确认单
        if stop_at in ('fee_confirm', 'receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[fee_confirm] Step14: 生成费用确认单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成费用确认单')
                confirm_result = _record_generate_fee_confirm(order_id=order_id)
                result['fee_confirm_result'] = confirm_result
                result['steps'].extend(confirm_result['steps'])

        # Step 15: 发起应收对账批次
        if stop_at in ('receive_account', 'confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
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

                receive_result = _record_receive_account(
                    bl_no=bl_no,
                    put_settle_object_id=put_settle_object_id,
                    main_id=main_id,
                    put_settle_object=put_settle_object,
                )
                result['receive_account_result'] = receive_result
                result['steps'].extend(receive_result['steps'])

        # Step 16: 确认应收对账
        if stop_at in ('confirm_account', 'invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[confirm_account] Step16: 确认应收对账'):
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

        # Step 17: 发起应收开票批次审批
        if stop_at in ('invoice_batch', 'invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
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

        # Step 18: 审核生成开票申请（stop_at 为 invoice_batch_audit 或 invoice_upload 时都需执行）
        if stop_at in ('invoice_batch_audit', 'invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[invoice_batch_audit] Step18: 审核生成开票申请'):
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

        # Step 19: 发票上传与登记
        if stop_at in ('invoice_upload', 'receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[invoice_upload] Step19: 发票上传与登记'):
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

        # Step 20: 应收核销（feeTakePage + writeoffBatch）
        if stop_at in ('receive_writeoff', 'payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[receive_writeoff] Step20: 应收核销'):
                # main_id / main_name 优先取 after_submit_order，没有则回退 YAML 默认值
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

        # Step 21: 应付对账（financePayList + orderPayAccountEdit）
        if stop_at in ('payable', 'confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[payable] Step21: 发起应付对账批次'):
                payable_result = _record_payable_account(bl_no=bl_no)
                result['payable_account_result'] = payable_result
                result['steps'].extend(payable_result['steps'])

        # Step 22: 确认应付对账（payAccountPage + accountConfirm）
        if stop_at in ('confirm_payable', 'payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[confirm_payable] Step22: 确认应付对账'):
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

        # Step 23: 发起应付开票批次申请（financePayList 开票 + getOrderInfoByFeeId + batchOrderEdit submit）
        if stop_at in ('payable_invoice_apply', 'payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[payable_invoice_apply] Step23: 发起应付开票批次申请'):
                confirm_result = result.get('confirm_payable_result')
                if not confirm_result:
                    cls._attach_context(result)
                    raise AssertionError('confirm_payable_result 不存在，无法发起应付开票批次申请')

                # main_id / main_name 优先取 confirm_payable → payable → 上游 submit_order
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

        # Step 24: 应付发票上传与登记（uploadFile + invoiceAdd + invoicePage + allocationInvoiceFee）
        if stop_at in ('payable_invoice_register', 'pay_demand', 'pay_demand_audit'):
            with allure.step('[payable_invoice_register] Step24: 应付发票上传与登记'):
                invoice_apply_result = result.get('payable_invoice_apply_result')
                if not invoice_apply_result:
                    cls._attach_context(result)
                    raise AssertionError(
                        'payable_invoice_apply_result 不存在，无法继续应付发票上传与登记'
                    )
                upload_result = _record_payable_invoice_upload(bl_no=bl_no)
                result['payable_invoice_register_result'] = upload_result
                result['steps'].extend(upload_result['steps'])

        # Step 25: 发起付款需求（financePayList + paymentList + demandEditByOrder）
        if stop_at in ('pay_demand', 'pay_demand_audit'):
            with allure.step('[pay_demand] Step25: 发起付款需求'):
                # 优先从 payable_invoice_apply_result 提取（最下游）
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

        # Step 26: 审核生成付款单（auditPage + auditExecute）
        if stop_at == 'pay_demand_audit':
            with allure.step('[pay_demand_audit] Step26: 审核生成付款单'):
                audit_result = _audit_pay_demand(bl_no=bl_no)
                result['pay_demand_audit_result'] = audit_result
                result['steps'].extend(audit_result['steps'])

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
        """执行到暂存阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='stash')

    @classmethod
    def run_until_generate_sub_order(cls, bl_no: str = None) -> Dict[str, Any]:
        """执行到生成子订单阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='generate_sub_order')

    @classmethod
    def run_until_record_fee(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到录费用阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='record_fee', fee_configs=fee_configs)

    @classmethod
    def run_until_record_audit(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到资产推送审批阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='record_audit', fee_configs=fee_configs)

    @classmethod
    def run_until_order_lock(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到订单锁定审批阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='order_lock', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_apply(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到未放款开票申请审批阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='invoice_apply', fee_configs=fee_configs)

    @classmethod
    def run_until_supplier_advance(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到供应商垫付申请审批阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='supplier_advance', fee_configs=fee_configs)

    @classmethod
    def run_until_fee_notice(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到生成费用通知单阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='fee_notice', fee_configs=fee_configs)

    @classmethod
    def run_until_fee_confirm(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到生成费用确认单阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='fee_confirm', fee_configs=fee_configs)

    @classmethod
    def run_until_receive_account(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到发起应收对账批次阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='receive_account', fee_configs=fee_configs)

    @classmethod
    def run_until_confirm_account(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到确认应收对账阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='confirm_account', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_batch(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到发起应收开票批次阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='invoice_batch', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_batch_audit(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到审核生成开票申请阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='invoice_batch_audit', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_upload(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到发票上传与登记阶段"""
        return cls.full_flow(bl_no=bl_no, stop_at='invoice_upload', fee_configs=fee_configs)

    @classmethod
    def run_until_receive_writeoff(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到应收核销阶段（link18 终点）"""
        return cls.full_flow(bl_no=bl_no, stop_at='receive_writeoff', fee_configs=fee_configs)

    @classmethod
    def run_until_payable_account(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到发起应付对账批次阶段（link19 终点）"""
        return cls.full_flow(bl_no=bl_no, stop_at='payable', fee_configs=fee_configs)

    @classmethod
    def run_until_confirm_payable(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到确认应付对账阶段（link20 终点）"""
        return cls.full_flow(bl_no=bl_no, stop_at='confirm_payable', fee_configs=fee_configs)

    @classmethod
    def run_until_payable_invoice_apply(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到发起应付开票批次申请阶段（link21 终点）"""
        return cls.full_flow(bl_no=bl_no, stop_at='payable_invoice_apply', fee_configs=fee_configs)

    @classmethod
    def run_until_pay_demand(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到发起付款需求阶段（link23 终点）"""
        return cls.full_flow(bl_no=bl_no, stop_at='pay_demand', fee_configs=fee_configs)

    @classmethod
    def run_until_pay_demand_audit(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到审核生成付款单阶段（link24 终点）"""
        return cls.full_flow(bl_no=bl_no, stop_at='pay_demand_audit', fee_configs=fee_configs)
