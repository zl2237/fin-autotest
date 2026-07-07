"""
API 层 - 应收核销相关接口封装

涉及流程：应收核销（LK18）
  1. POST /api/order/orderFee/feeTakePage                 - 按提单号分页查询费用实付 ID 列表
  2. POST /api/finance/receiveWriteoff/writeoffBatch      - 应收核销（依赖 step1 的 order_fee_real_id）

所有枚举值、常量默认值统一从 data/receive_writeoff.yaml 读取，勿在代码中硬编码。
"""
import time
from typing import Any, Dict, List, Optional

from core.http_client import http
from data.receive import ReceiveWriteoffData


class ReceiveWriteoffApi:
    """应收核销相关 API"""

    FEE_TAKE_PAGE_URL = "/api/order/orderFee/feeTakePage"
    WRITEOFF_BATCH_URL = "/api/finance/receiveWriteoff/writeoffBatch"

    @classmethod
    def query_order_fee_real_id_list(
        cls,
        bl_no: str,
        page_no: int = None,
        page_size: int = None,
        create_time_start: str = None,
        create_time_end: str = None,
    ) -> Any:
        """
        按提单号分页查询费用实付 ID 列表（feeTakePage）

        响应 data.data[].order_fee_real_id 为后续 writeoffBatch 所需的核心数据。

        Args:
            bl_no              : 提单号（精确查询）
            page_no            : 页码
            page_size          : 每页数量
            create_time_start  : 创建时间开始（Unix 时间戳秒）
            create_time_end    : 创建时间结束（Unix 时间戳秒）

        Returns:
            Response 对象
        """
        payload = ReceiveWriteoffData.get_fee_take_page_payload(
            bl_no=bl_no,
            page_no=page_no,
            page_size=page_size,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
        )
        return http.post(cls.FEE_TAKE_PAGE_URL, json=payload)

    @classmethod
    def submit_writeoff_batch(
        cls,
        writeoff_object: List[Dict[str, Any]],
        main_id: str = None,
        main_name: str = None,
        receipt_time: int = None,
        writeoff_name: str = None,
        audit_note: str = None,
        action: str = None,
        select_node_user: Optional[List[Dict[str, Any]]] = None,
        statement_currency: str = None,
    ) -> Any:
        """
        应收核销（writeoffBatch）

        依赖 step1（feeTakePage）返回的 order_fee_real_id 列表。
        请求体金额字段（_usd_total / _cny_total / statement_*_total）由
        ReceiveWriteoffData 根据 writeoff_object 自动按币种求和填充。

        Args:
            writeoff_object    : 核销对象列表（来自 query_order_fee_real_id_list 响应）
            main_id            : 主体ID（默认从 YAML 读取）
            main_name          : 主体名称（默认从 YAML 读取）
            receipt_time       : 收款时间（Unix 时间戳秒，默认当前时间）
            writeoff_name      : 核销批次名称
            audit_note         : 审批备注（默认空，走常规核销）
            action             : 操作类型（默认 submit）
            select_node_user   : 指定审批人列表（默认空数组）
            statement_currency : 账单币种（默认 USD）

        Returns:
            Response 对象
        """
        payload = ReceiveWriteoffData.get_writeoff_batch_payload(
            writeoff_object=writeoff_object,
            main_id=main_id,
            main_name=main_name,
            receipt_time=receipt_time,
            writeoff_name=writeoff_name,
            audit_note=audit_note,
            action=action,
            select_node_user=select_node_user,
            statement_currency=statement_currency,
        )
        return http.post(cls.WRITEOFF_BATCH_URL, json=payload)
