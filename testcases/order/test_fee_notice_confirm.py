"""
链路测试 - 费用通知单 / 费用确认单（link11~12）

  link11 - 生成费用通知单
  link12 - 生成费用确认单
"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no


def _build_fee_config():
    return {
        'to_customer_fees': BookRealAmountData.get_customer_standard_fees(),
        'to_supplier_fees': BookRealAmountData.get_supplier_standard_fees(),
    }


def _assert_audit_chain_ok(result):
    """link11/12 共用的"录费用+资产推送+订单锁定+开票申请+供应商垫付"链式断言。"""
    assert result['create_data']['code'] == 200, f'新建失败: {result["create_data"]}'
    assert result['distribute_data']['code'] == 200, f'分发失败: {result["distribute_data"]}'
    gen_data = result['generate_sub_data']
    assert gen_data['code'] == 200, f'生成子订单失败: {gen_data}'
    assert len(result['record_fee_results']) == 1
    fee_1 = result['record_fee_results'][0]
    assert fee_1['resp'].status_code == 200
    assert fee_1['data']['code'] == 200
    assert fee_1.get('audit_send_resp') is not None
    assert fee_1['audit_send_resp'].status_code == 200
    assert fee_1['audit_send_data']['code'] == 200, f'发起审批失败: {fee_1["audit_send_data"]}'
    assert fee_1.get('audit_id'), 'audit_id 不应为空'
    assert fee_1['audit_approve_resp'].status_code == 200
    assert fee_1['audit_approve_data']['code'] == 200, f'审批通过失败: {fee_1["audit_approve_data"]}'

    lock_result = result['order_lock_result']
    assert lock_result is not None
    assert lock_result['container']
    assert lock_result['send_resp'].status_code == 200
    assert lock_result['send_data']['code'] == 200, f'订单锁定发起失败: {lock_result["send_data"]}'
    assert lock_result.get('audit_id')
    assert lock_result['approve_resp'].status_code == 200
    assert lock_result['approve_data']['code'] == 200, f'订单锁定审批通过失败: {lock_result["approve_data"]}'

    invoice_result = result['invoice_apply_result']
    assert invoice_result is not None
    assert invoice_result['send_resp'].status_code == 200
    assert invoice_result['send_data']['code'] == 200, f'未放款开票申请发起失败: {invoice_result["send_data"]}'
    assert invoice_result.get('audit_id')
    assert invoice_result['approve_resp'].status_code == 200
    assert invoice_result['approve_data']['code'] == 200, f'未放款开票申请审批通过失败: {invoice_result["approve_data"]}'

    advance_result = result['supplier_advance_result']
    assert advance_result is not None
    assert advance_result['send_resp'].status_code == 200
    assert advance_result['send_data']['code'] == 200, f'供应商垫付申请发起失败: {advance_result["send_data"]}'
    assert advance_result.get('audit_id')
    assert advance_result['approve_resp'].status_code == 200
    assert advance_result['approve_data']['code'] == 200, f'供应商垫付申请审批通过失败: {advance_result["approve_data"]}'


def _assert_fee_notice_ok(result):
    """link11/12 共用的费用通知单断言。"""
    notice_result = result['fee_notice_result']
    assert notice_result is not None, '费用通知单结果不应为空'
    assert notice_result['resp'].status_code == 200
    assert notice_result['data']['code'] == 200, f'费用通知单 code 不为 200: {notice_result["data"]}'
    assert notice_result['data'].get('msg') == '成功', f'费用通知单 msg 不为"成功": {notice_result["data"]}'
    notice_file = notice_result['file_info']
    assert notice_file, f'费用通知单 file_info 不应为空: {notice_result["data"]}'
    assert notice_file.get('file_id')
    assert notice_file.get('file_name')
    assert notice_file.get('file_type', '').upper() == 'PDF'
    assert notice_file.get('file_url')
    assert notice_file.get('original_name')


# =============================================================================
# 链路11：生成费用通知单
# =============================================================================
@pytest.mark.order11
class TestOrder11GenerateFeeNotice:
    """链路11：生成费用通知单"""

    @allure.feature("链路测试")
    @allure.story("链路11：生成费用通知单")
    @allure.severity("critical")
    @allure.title("链路11：生成费用通知单")
    def test_link11_generate_fee_notice(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 生成费用通知单），链路停在 fee_notice 阶段"""
        bl_no = generate_bl_no(11)

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批→供应商垫付申请审批→生成费用通知单）'):
            result = OrderWorkflow.run(
                stop_at='fee_notice',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：审批链路全部成功'):
            _assert_audit_chain_ok(result)

        with allure.step('断言：生成费用通知单成功'):
            _assert_fee_notice_ok(result)

        with allure.step('断言：file_id 非空且为字符串'):
            file_info = result['fee_notice_result']['file_info']
            assert file_info.get('file_id'), f'file_id 不应为空: {file_info}'
            assert isinstance(file_info['file_id'], str), f'file_id 应为 str，实际: {type(file_info["file_id"])}'

        with allure.step('断言：file_name 非空且为字符串'):
            assert file_info.get('file_name'), f'file_name 不应为空: {file_info}'
            assert isinstance(file_info['file_name'], str), f'file_name 应为 str，实际: {type(file_info["file_name"])}'

        with allure.step('断言：file_type 非空且为字符串'):
            assert file_info.get('file_type'), f'file_type 不应为空: {file_info}'
            assert isinstance(file_info['file_type'], str), f'file_type 应为 str，实际: {type(file_info["file_type"])}'
            assert file_info['file_type'].upper() == 'PDF', f'file_type 应为 PDF，实际: {file_info["file_type"]}'

        with allure.step('断言：file_url 非空且为字符串'):
            assert file_info.get('file_url'), f'file_url 不应为空: {file_info}'
            assert isinstance(file_info['file_url'], str), f'file_url 应为 str，实际: {type(file_info["file_url"])}'

        with allure.step('断言：original_name 非空且为字符串'):
            assert file_info.get('original_name'), f'original_name 不应为空: {file_info}'
            assert isinstance(file_info['original_name'], str), f'original_name 应为 str，实际: {type(file_info["original_name"])}'

        with allure.step('断言：file_name 包含"费用通知单"关键字'):
            assert '费用通知单' in file_info['file_name'], \
                f'file_name 应包含"费用通知单"，实际: {file_info["file_name"]}'

        with allure.step('断言：file_name 以 bl_no 为前缀'):
            assert file_info['file_name'].startswith(bl_no), \
                f'file_name 应以 bl_no="{bl_no}" 为前缀，实际: {file_info["file_name"]}'

        with allure.step('断言：file_url 以 .pdf 结尾'):
            assert file_info['file_url'].endswith('.pdf'), \
                f'file_url 应以.pdf 结尾，实际: {file_info["file_url"]}'

        with allure.step('断言：request_id 非空且为字符串'):
            data = result['fee_notice_result']['data']
            assert data.get('request_id'), f'request_id 不应为空: {data}'
            assert isinstance(data['request_id'], str), f'request_id 应为 str，实际: {type(data["request_id"])}'

        with allure.step('断言：链路停在 fee_notice 阶段'):
            assert result['stop_at'] == 'fee_notice'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
            ]:
                assert name in step_names, f'steps 缺少: {name}'


# =============================================================================
# 链路12：生成费用确认单
# =============================================================================
@pytest.mark.order12
class TestOrder12GenerateFeeConfirm:
    """链路12：生成费用确认单"""

    @allure.feature("链路测试")
    @allure.story("链路12：生成费用确认单")
    @allure.severity("critical")
    @allure.title("链路12：生成费用确认单")
    def test_link12_generate_fee_confirm(self):
        """验证：完整链路（包含资产推送审批 + 订单锁定审批 + 未放款开票申请审批 + 供应商垫付申请审批 + 费用通知单 + 费用确认单），链路停在 fee_confirm 阶段"""
        bl_no = generate_bl_no(12)

        with allure.step('执行链路（新建→分发→查询→暂存→提交→生成子订单→录费用→资产推送审批→订单锁定审批→未放款开票申请审批→供应商垫付申请审批→生成费用通知单→生成费用确认单）'):
            result = OrderWorkflow.run(
                stop_at='fee_confirm',
                bl_no=bl_no,
                fee_configs=[_build_fee_config()],
            )

        with allure.step('断言：审批链路全部成功'):
            _assert_audit_chain_ok(result)

        with allure.step('断言：生成费用通知单成功'):
            _assert_fee_notice_ok(result)

        with allure.step('断言：生成费用确认单成功'):
            confirm_result = result['fee_confirm_result']
            assert confirm_result is not None, '费用确认单结果不应为空'
            assert confirm_result['resp'].status_code == 200, \
                f'HTTP 状态码异常: {confirm_result["resp"].status_code}'
            data = confirm_result['data']
            assert data['code'] == 200, f'响应 code 不为 200: {data}'
            assert data.get('msg') == '成功', f'响应 msg 不为"成功": {data.get("msg")}'
            assert data.get('data') is not None, f'data.data 不应为 None: {data}'
            file_info = confirm_result['file_info']
            assert file_info, f'data.file_name 不应为空: {data.get("data")}'
            assert file_info.get('file_id'), f'file_id 不应为空: {file_info}'
            assert isinstance(file_info['file_id'], str), f'file_id 应为 str，实际: {type(file_info["file_id"])}'
            assert file_info.get('file_name'), f'file_name 不应为空: {file_info}'
            assert isinstance(file_info['file_name'], str), f'file_name 应为 str，实际: {type(file_info["file_name"])}'
            assert file_info.get('file_type'), f'file_type 不应为空: {file_info}'
            assert isinstance(file_info['file_type'], str), f'file_type 应为 str，实际: {type(file_info["file_type"])}'
            assert file_info['file_type'].upper() == 'PDF', f'file_type 应为 PDF，实际: {file_info["file_type"]}'
            assert file_info.get('file_url'), f'file_url 不应为空: {file_info}'
            assert isinstance(file_info['file_url'], str), f'file_url 应为 str，实际: {type(file_info["file_url"])}'
            assert file_info.get('original_name'), f'original_name 不应为空: {file_info}'
            assert isinstance(file_info['original_name'], str), f'original_name 应为 str，实际: {type(file_info["original_name"])}'
            assert '费用确认单' in file_info['file_name'], \
                f'file_name 应包含"费用确认单"，实际: {file_info["file_name"]}'
            assert file_info['file_name'].startswith(bl_no), \
                f'file_name 应以 bl_no="{bl_no}" 为前缀，实际: {file_info["file_name"]}'
            assert file_info['file_url'].endswith('.pdf'), \
                f'file_url 应以.pdf 结尾，实际: {file_info["file_url"]}'
            assert data.get('request_id'), f'request_id 不应为空: {data}'
            assert isinstance(data['request_id'], str), f'request_id 应为 str，实际: {type(data["request_id"])}'

        with allure.step('断言：链路停在 fee_confirm 阶段'):
            assert result['stop_at'] == 'fee_confirm'

        with allure.step('断言：steps 记录完整'):
            step_names = [s['name'] for s in result['steps']]
            for name in [
                '新建订单', '按提单号查询', '分发订单', '查询订单',
                '暂存订单', '查询订单（暂存后）', '提交订单', '查询订单（提交后）',
                '生成子订单',
                '录费用(1)', '发起审批(1)', '查询审批ID(1)', '审批通过(1)',
                '获取箱型信息',
                '发起订单锁定审批', '查询订单锁定审批ID', '订单锁定审批通过',
                '发起未放款开票申请审批', '查询未放款开票申请审批ID', '未放款开票申请审批通过',
                '发起供应商垫付申请审批', '查询供应商垫付申请审批ID', '供应商垫付申请审批通过',
                '生成费用通知单',
                '生成费用确认单',
            ]:
                assert name in step_names, f'steps 缺少: {name}'
