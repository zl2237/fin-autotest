"""
应收对账步骤：
- record_receive_account   发起应收对账批次（query → check → submit）
- record_confirm_account   确认应收对账（detail → confirm_list → confirm → page 验证）
"""
from typing import Any, Dict

import allure

from api.receive.receive_account_api import FinanceApi
from data.receive import (
    ACTION_CHECK,
    ACTION_SUBMIT,
    CONFIRM_TYPE_PENDING,
    ReceiveAccountData,
)


def record_receive_account(
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
    from data.receive import RECEIVE_ACCOUNT_MAIN_NAME

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

    return result


def record_confirm_account(
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

    return result
