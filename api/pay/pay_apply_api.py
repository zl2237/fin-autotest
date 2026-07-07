"""
API 层 - 应付开票申请相关接口封装

涉及流程：发起应付开票申请（LK21）
  1. POST /api/finance/accountFee/financePayList         - 查询应付开票项（开票模式）
  2. POST /api/Finance/payInvoiceBatch/getOrderInfoByFeeId - 查询开票订单信息
  3. POST /api/Finance/payInvoiceBatch/batchOrderEdit     - 发起应付开票批次申请（apply_type=2）

所有枚举值、常量默认值统一从 data/pay/payable_invoice.yaml 读取，勿在代码中硬编码。
"""
from typing import Any, Dict, List

from core.http_client import http
from data.pay import PayableInvoiceData


class PayInvoiceApi:
    """应付开票申请相关 API"""

    FINANCE_PAY_LIST_URL = "/api/finance/accountFee/financePayList"
    PAY_GET_ORDER_INFO_BY_FEE_ID_URL = "/api/Finance/payInvoiceBatch/getOrderInfoByFeeId"
    PAY_BATCH_ORDER_EDIT_URL = "/api/Finance/payInvoiceBatch/batchOrderEdit"

    @classmethod
    def query_finance_pay_list_for_invoice(
        cls,
        bl_no: str,
        main_id: str = None,
        pay_settle_object_id: str = None,
        pay_settle_object: str = None,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        查询应付开票项列表（financePayList，开票模式）

        与对账模式共用同一接口，仅 search_style/batch_type 不同。
        用于 LK21 发起应付开票申请。

        注意：main_id / pay_settle_object_id / pay_settle_object 三个字段**必填**。
        优先级：显式入参 > YAML 默认值；都没有则抛 AssertionError。

        Args:
            bl_no               : 提单号（来自上游链路）
            main_id             : 主体ID（可选，缺省时从 YAML 读取）
            pay_settle_object_id: 付款结算对象ID（可选，缺省时从 YAML 读取）
            pay_settle_object   : 付款结算对象名称（可选，缺省时从 YAML 读取）
            page_no             : 页码
            page_size           : 每页数量
            create_time_start   : 创建时间开始（Unix 秒）
            create_time_end     : 创建时间结束（Unix 秒）

        Returns:
            Response 对象
        """
        payload = PayableInvoiceData.get_finance_pay_list_invoice_payload(
            bl_no=bl_no,
            main_id=main_id,
            pay_settle_object_id=pay_settle_object_id,
            pay_settle_object=pay_settle_object,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.FINANCE_PAY_LIST_URL, json=payload)

    @classmethod
    def get_order_info_by_fee_id(
        cls,
        order_fee_real_ids: List[str],
        exchange_rate: Any = None,
        usd_invoice_remark: int = None,
        style: int = None,
    ) -> Any:
        """
        查询开票订单信息（getOrderInfoByFeeId）

        响应 data 为列表，每项包含 book_supplier_id / book_supplier_name /
        order_sub_id / real_amount / fee_real_name 等字段，
        用于构建 batchOrderEdit 请求体。

        Args:
            order_fee_real_ids : 费用实付 ID 列表
            exchange_rate      : 汇率（默认 GOBI_DEFAULT_EXCHANGE_RATE）
            usd_invoice_remark : 备注模式（默认 GOBI_USD_INVOICE_REMARK=0）
            style              : 模式（默认 GOBI_STYLE=1）

        Returns:
            Response 对象
        """
        payload = PayableInvoiceData.get_order_info_by_fee_id_payload(
            order_fee_real_ids=order_fee_real_ids,
            exchange_rate=exchange_rate,
            usd_invoice_remark=usd_invoice_remark,
            style=style,
        )
        return http.post(cls.PAY_GET_ORDER_INFO_BY_FEE_ID_URL, json=payload)

    @classmethod
    def submit_pay_invoice_batch(
        cls,
        order_info_data_list: List[Dict[str, Any]],
        finance_pay_records: List[Dict[str, Any]],
        main_id: str,
        main_name: str,
        pay_settle_object: str,
        pay_settle_object_id: str,
        exchange_rate: Any = None,
        customer_id: str = None,
        customer_name: str = None,
        batch_order_remark: str = None,
        action: str = None,
    ) -> Any:
        """
        发起应付开票批次申请（batchOrderEdit，apply_type=2）

        应付方向：提交即生效，无需审批（无 link16 等价步骤）。
        响应 data 为空，code=200 即开票批次创建成功，
        后续可用于 link22 应付开票登记。

        Args:
            order_info_data_list : getOrderInfoByFeeId 响应 data 列表
            finance_pay_records  : financePayList（开票模式）响应 data 列表
            main_id              : 主体ID
            main_name            : 主体名称
            pay_settle_object    : 付款结算对象名称
            pay_settle_object_id : 付款结算对象ID
            exchange_rate        : 汇率
            customer_id          : 客户ID（可选，自动从 finance_pay_records 取）
            customer_name        : 客户名称
            batch_order_remark   : 批次备注
            action               : 操作类型（默认 submit）

        Returns:
            Response 对象
        """
        payload = PayableInvoiceData.build_batch_order_edit_pay_payload(
            order_info_data_list=order_info_data_list,
            finance_pay_records=finance_pay_records,
            main_id=main_id,
            main_name=main_name,
            pay_settle_object=pay_settle_object,
            pay_settle_object_id=pay_settle_object_id,
            exchange_rate=exchange_rate,
            customer_id=customer_id,
            customer_name=customer_name,
            batch_order_remark=batch_order_remark,
            action=action,
        )
        return http.post(cls.PAY_BATCH_ORDER_EDIT_URL, json=payload)
