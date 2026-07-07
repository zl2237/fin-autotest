"""
订单流程编排 - 串联订单各阶段 API，自动处理数据依赖

本文件仅保留编排门面：_attach_context / run / run_until_xxx。
各业务子步骤（新建+分发、暂存、提交、生成子订单、审批、费用）
已拆到 workflows/order/ 子模块实现，本文件只负责按 stop_at 编排。
"""
import logging
import time
from typing import Any, Dict, List

import allure

from api.order import OrderApi
from config.settings import TEST_DATA_DIR
from data.order import (
    BookRealAmountData,
)
from utils import generate_bl_no
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

    流程阶段：新建 → 分发 → [查询] → [暂存] → 提交 → 生成子订单

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
    def _run(
        cls,
        bl_no: str = None,
        stop_at: str = 'submit',
        skip_stash: bool = False,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        完整订单流程：新建 → 分发 → [查询] → [暂存] → 提交 → [生成子订单] → [录费用] → [录审批]

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
                'fee_notice_result': ...,
                'fee_confirm_result': ...,
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
        if stop_at in ('generate_sub_order', 'record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm'):
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
        if stop_at in ('record_fee', 'record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm'):
            with allure.step(f'[{stop_at}] Step8: 录费用'):
                order_id = after_submit_order.get('order_id')
                audit_after = stop_at in ('record_audit', 'order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm')
                fee_result = _record_fee(
                    order_id=order_id,
                    fee_configs=fee_configs or [],
                    audit_after_fee=audit_after,
                )
                result['record_fee_results'] = fee_result['results']
                result['steps'].extend(fee_result['steps'])

        # assetPush 已在 record_fee 内部完成（audit_after_fee=True）

        # Step 10: 订单锁定审批
        if stop_at in ('order_lock', 'invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm'):
            with allure.step(f'[{stop_at}] Step10: 订单锁定审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起订单锁定审批')
                lock_result = _record_order_lock(order_id=order_id, bl_no=bl_no)
                result['order_lock_result'] = lock_result
                result['steps'].extend(lock_result['steps'])

        # Step 11: 未放款开票申请审批
        if stop_at in ('invoice_apply', 'supplier_advance', 'fee_notice', 'fee_confirm'):
            with allure.step('[invoice_apply] Step11: 未放款开票申请审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起未放款开票申请审批')
                invoice_result = _record_invoice_apply(order_id=order_id, bl_no=bl_no)
                result['invoice_apply_result'] = invoice_result
                result['steps'].extend(invoice_result['steps'])

        # Step 12: 供应商垫付申请审批
        if stop_at in ('supplier_advance', 'fee_notice', 'fee_confirm'):
            with allure.step('[supplier_advance] Step12: 供应商垫付申请审批'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法发起供应商垫付申请审批')
                advance_result = _record_supplier_advance(order_id=order_id, bl_no=bl_no)
                result['supplier_advance_result'] = advance_result
                result['steps'].extend(advance_result['steps'])

        # Step 13: 生成费用通知单
        if stop_at in ('fee_notice', 'fee_confirm'):
            with allure.step('[fee_notice] Step13: 生成费用通知单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成费用通知单')
                notice_result = _record_generate_fee_notice(order_id=order_id)
                result['fee_notice_result'] = notice_result
                result['steps'].extend(notice_result['steps'])

        # Step 14: 生成费用确认单
        if stop_at in ('fee_confirm',):
            with allure.step('[fee_confirm] Step14: 生成费用确认单'):
                order_id = after_submit_order.get('order_id')
                if not order_id:
                    cls._attach_context(result)
                    raise AssertionError('提交后查询不到订单，无法生成费用确认单')
                confirm_result = _record_generate_fee_confirm(order_id=order_id)
                result['fee_confirm_result'] = confirm_result
                result['steps'].extend(confirm_result['steps'])

        cls._attach_context(result)
        return result

    # =====================
    # 快捷方法
    # =====================

    @classmethod
    def run(cls, bl_no: str = None, stop_at: str = 'submit', skip_stash: bool = False, fee_configs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行订单流程，stop_at 控制停止阶段"""
        return cls._run(bl_no=bl_no, stop_at=stop_at, skip_stash=skip_stash, fee_configs=fee_configs)

    @classmethod
    def run_until_create(cls, bl_no: str = None) -> Dict[str, Any]:
        """仅执行到新建阶段"""
        return cls._run(bl_no=bl_no, stop_at='create')

    @classmethod
    def run_until_distribute(cls, bl_no: str = None) -> Dict[str, Any]:
        """仅执行到分发阶段"""
        return cls._run(bl_no=bl_no, stop_at='distribute')

    @classmethod
    def run_until_stash(cls, bl_no: str = None) -> Dict[str, Any]:
        """执行到暂存阶段"""
        return cls._run(bl_no=bl_no, stop_at='stash')

    @classmethod
    def run_until_submit(cls, bl_no: str = None, skip_stash: bool = False) -> Dict[str, Any]:
        """执行到提交阶段"""
        return cls._run(bl_no=bl_no, stop_at='submit', skip_stash=skip_stash)

    @classmethod
    def run_until_generate_sub_order(cls, bl_no: str = None) -> Dict[str, Any]:
        """执行到生成子订单阶段"""
        return cls._run(bl_no=bl_no, stop_at='generate_sub_order')

    @classmethod
    def run_until_record_fee(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到录费用阶段"""
        return cls._run(bl_no=bl_no, stop_at='record_fee', fee_configs=fee_configs)

    @classmethod
    def run_until_record_audit(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到资产推送审批阶段"""
        return cls._run(bl_no=bl_no, stop_at='record_audit', fee_configs=fee_configs)

    @classmethod
    def run_until_order_lock(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到订单锁定审批阶段"""
        return cls._run(bl_no=bl_no, stop_at='order_lock', fee_configs=fee_configs)

    @classmethod
    def run_until_invoice_apply(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到未放款开票申请审批阶段"""
        return cls._run(bl_no=bl_no, stop_at='invoice_apply', fee_configs=fee_configs)

    @classmethod
    def run_until_supplier_advance(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到供应商垫付申请审批阶段"""
        return cls._run(bl_no=bl_no, stop_at='supplier_advance', fee_configs=fee_configs)

    @classmethod
    def run_until_fee_notice(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到生成费用通知单阶段"""
        return cls._run(bl_no=bl_no, stop_at='fee_notice', fee_configs=fee_configs)

    @classmethod
    def run_until_fee_confirm(
        cls,
        bl_no: str = None,
        fee_configs: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行到生成费用确认单阶段"""
        return cls._run(bl_no=bl_no, stop_at='fee_confirm', fee_configs=fee_configs)
