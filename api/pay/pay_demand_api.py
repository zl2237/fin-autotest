"""
API 层 - 发起付款需求接口封装（LK23）

涉及 3 个请求：
  1. POST /api/finance/accountFee/financePayList        - 查询应付费用列表（付款需求模式）
  2. POST /api/finance/payDemand/paymentList         - 付款需求预览
  3. POST /api/finance/payDemand/demandEditByOrder   - 提交付款需求

所有枚举值、常量默认值统一从 data/pay/*.yaml 读取，勿在代码中硬编码。
"""
from typing import Any, Dict, List

from core.http_client import http
from data.pay import PayDemandData


class PayDemandApi:
    """发起付款需求 API"""

    FINANCE_PAY_LIST_URL = "/api/finance/accountFee/financePayList"
    PAYMENT_LIST_URL = "/api/finance/payDemand/paymentList"
    DEMAND_EDIT_BY_ORDER_URL = "/api/finance/payDemand/demandEditByOrder"

    @classmethod
    def query_finance_pay_list(
        cls,
        bl_no: str,
        main_id: str = None,
        pay_settle_object_id: str = None,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        查询应付费用列表（financePayList，付款需求模式）

        响应 data.data[].amount_list[].order_fee_real_id 为后续必需字段。

        Args:
            bl_no               : 提单号（精确查询，来自上游链路）
            main_id             : 主体ID（可选）
            pay_settle_object_id: 付款结算对象ID（可选）
            page_no            : 页码（默认 1）
            page_size          : 每页数量（默认 50）
            create_time_start  : 创建时间开始（Unix 秒，默认 1 年前）
            create_time_end    : 创建时间结束（Unix 秒，默认 1 年后）

        Returns:
            Response 对象
        """
        payload = PayDemandData.get_finance_pay_list_payload(
            bl_no=bl_no,
            main_id=main_id,
            pay_settle_object_id=pay_settle_object_id,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.FINANCE_PAY_LIST_URL, json=payload)

    @classmethod
    def payment_list(
        cls,
        pay_list_data: Dict[str, Any],
        select_amount: str,
        cost_usd: str,
        cost_cny: str,
        split_dimension: List[str] = None,
    ) -> Any:
        """
        付款需求预览（paymentList）

        返回 payment_list 及汇总数据（system_exchange_rate / pay_amount_usd_total 等），
        供 Step 3 构建 demandEditByOrder 请求体。

        Args:
            pay_list_data     : financePayList 响应中的 data 字典
            select_amount    : 选中金额
            cost_usd        : 美元总额
            cost_cny        : 人民币总额
            split_dimension  : 拆分维度列表（默认从 YAML 读取）

        Returns:
            Response 对象
        """
        payload = PayDemandData.build_payment_list_payload(
            pay_list_data=pay_list_data,
            select_amount=select_amount,
            cost_usd=cost_usd,
            cost_cny=cost_cny,
            split_dimension=split_dimension,
        )
        return http.post(cls.PAYMENT_LIST_URL, json=payload)

    @classmethod
    def submit_demand(
        cls,
        pay_list_data: Dict[str, Any],
        payment_list_data: Dict[str, Any],
        split_dimension: List[str] = None,
        select_node_user: List[Dict[str, Any]] = None,
        bl_nos: List[str] = None,
    ) -> Any:
        """
        提交付款需求（demandEditByOrder）

        响应 data 通常为空，code=200 即提交成功。

        Args:
            pay_list_data       : financePayList 响应中的 data 字典
            payment_list_data   : paymentList 响应中的 data 字典
            split_dimension     : 拆分维度列表（默认从 YAML 读取）
            select_node_user    : 审批节点用户（默认从 YAML + .env 读取）
            bl_nos             : 提单号列表（默认空列表）

        Returns:
            Response 对象
        """
        payload = PayDemandData.build_demand_edit_payload(
            pay_list_data=pay_list_data,
            payment_list_data=payment_list_data,
            split_dimension=split_dimension,
            select_node_user=select_node_user,
            bl_nos=bl_nos,
        )
        return http.post(cls.DEMAND_EDIT_BY_ORDER_URL, json=payload)
