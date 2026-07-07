"""
API 层 - 付款单核销接口封装（LK25）

涉及 4 个请求：
  1. POST /api/finance/payForm/formPage          - 查询付款单列表
  2. POST /api/finance/payWriteoff/writeoffPayFormList - 核销付款单列表
  3. POST /api/finance/payWriteoff/orderFeePage  - 查询可核销费用列表
  4. POST /api/finance/payWriteoff/writeoffBatch - 执行核销

所有枚举值、常量默认值统一从 data/pay/*.yaml 读取，勿在代码中硬编码。
"""
from typing import Any, List

from core.http_client import http
from data.pay import PayWriteoffData


class PayWriteoffApi:
    """付款单核销 API"""

    FORM_PAGE_URL = "/api/finance/payForm/formPage"
    WRITEOFF_PAY_FORM_LIST_URL = "/api/finance/payWriteoff/writeoffPayFormList"
    ORDER_FEE_PAGE_URL = "/api/finance/payWriteoff/orderFeePage"
    WRITEOFF_BATCH_URL = "/api/finance/payWriteoff/writeoffBatch"

    @classmethod
    def form_page(
        cls,
        page_no: int = None,
        page_size: int = None,
        order_no: str = None,
        create_time_start: str = None,
        create_time_end: str = None,
        status: List[str] = None,
        sort_field: str = None,
        sort_order: str = None,
    ) -> Any:
        """
        查询付款单列表（formPage）

        响应 data.data[].pay_form_id 为后续步骤必需字段。

        Args:
            page_no           : 页码（默认 1）
            page_size        : 每页数量（默认 20）
            order_no         : 订单号（默认空字符串）
            create_time_start: 创建时间开始（默认当天 00:00:00）
            create_time_end  : 创建时间结束（默认当天 23:59:59）
            status           : 付款单状态列表（默认 ["2"]=已生效）
            sort_field       : 排序字段（默认 create_time）
            sort_order       : 排序方向（默认 desc）

        Returns:
            Response 对象
        """
        payload = PayWriteoffData.get_form_page_payload(
            page_no=page_no,
            page_size=page_size,
            order_no=order_no,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
            status=status,
            sort_field=sort_field,
            sort_order=sort_order,
        )
        return http.post(cls.FORM_PAGE_URL, json=payload)

    @classmethod
    def writeoff_pay_form_list(
        cls,
        pay_form_ids: List[str],
    ) -> Any:
        """
        核销付款单列表（writeoffPayFormList）

        Args:
            pay_form_ids: 付款单ID列表（**必填**，来自 formPage 响应）

        Returns:
            Response 对象
        """
        payload = PayWriteoffData.get_writeoff_pay_form_list_payload(
            pay_form_ids=pay_form_ids,
        )
        return http.post(cls.WRITEOFF_PAY_FORM_LIST_URL, json=payload)

    @classmethod
    def order_fee_page(
        cls,
        order_fee_real_ids: List[str],
    ) -> Any:
        """
        查询可核销费用列表（orderFeePage）

        Args:
            order_fee_real_ids: 费用明细ID列表（**必填**，来自 formPage/writeoffPayFormList 响应）

        Returns:
            Response 对象
        """
        payload = PayWriteoffData.get_order_fee_page_payload(
            order_fee_real_ids=order_fee_real_ids,
        )
        return http.post(cls.ORDER_FEE_PAGE_URL, json=payload)

    @classmethod
    def writeoff_batch(
        cls,
        remark: str = None,
        bank_account: str = None,
        action: str = None,
        writeoff_object: List[dict] = None,
        writeoff_name: str = None,
        fee_match_type: str = None,
        writeoff_type: str = None,
        writeoff_mode: str = None,
        currency: str = None,
        un_writeoff_amount_usd_total: str = None,
        un_writeoff_amount_cny_total: str = None,
        use_writeoff_amount_usd_total: str = None,
        use_writeoff_amount_cny_total: str = None,
        statement: List[dict] = None,
        main_id: str = None,
        main_name: str = None,
        statement_amount_cny_total: str = None,
        statement_amount_usd_total: str = None,
        select_node_user: List[dict] = None,
    ) -> Any:
        """
        执行核销（writeoffBatch）

        Args:
            remark                       : 备注（默认空字符串）
            bank_account               : 银行账号（默认空字符串）
            action                     : 提交动作（默认 submit）
            writeoff_object            : 核销对象列表（默认 []，由 PayWriteoffData 构造）
            writeoff_name              : 核销名称（默认 固定值）
            fee_match_type             : 费用匹配类型（默认 "1"）
            writeoff_type              : 核销类型（默认 "1"）
            writeoff_mode              : 核销模式（默认空字符串）
            currency                   : 币种（默认空字符串）
            un_writeoff_amount_usd_total: 未核销金额 USD 合计（默认 "0.00"）
            un_writeoff_amount_cny_total: 未核销金额 CNY 合计（默认 "0.00"）
            use_writeoff_amount_usd_total: 已核销金额 USD 合计（默认 from writeoff_object）
            use_writeoff_amount_cny_total: 已核销金额 CNY 合计（默认 "0.00"）
            statement                  : 核销对账明细（默认 from PayWriteoffData 构造）
            main_id                   : 主体ID（默认 from writeoff_object）
            main_name                  : 主体名称（默认 from writeoff_object）
            statement_amount_cny_total : 对账金额 CNY 合计（默认 "0.00"）
            statement_amount_usd_total : 对账金额 USD 合计（默认 from statement）
            select_node_user           : 审批节点用户（默认 []）

        Returns:
            Response 对象
        """
        payload = PayWriteoffData.get_writeoff_batch_payload(
            remark=remark,
            bank_account=bank_account,
            action=action,
            writeoff_object=writeoff_object,
            writeoff_name=writeoff_name,
            fee_match_type=fee_match_type,
            writeoff_type=writeoff_type,
            writeoff_mode=writeoff_mode,
            currency=currency,
            un_writeoff_amount_usd_total=un_writeoff_amount_usd_total,
            un_writeoff_amount_cny_total=un_writeoff_amount_cny_total,
            use_writeoff_amount_usd_total=use_writeoff_amount_usd_total,
            use_writeoff_amount_cny_total=use_writeoff_amount_cny_total,
            statement=statement,
            main_id=main_id,
            main_name=main_name,
            statement_amount_cny_total=statement_amount_cny_total,
            statement_amount_usd_total=statement_amount_usd_total,
            select_node_user=select_node_user,
        )
        return http.post(cls.WRITEOFF_BATCH_URL, json=payload)
