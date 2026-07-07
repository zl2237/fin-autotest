from flask import Blueprint, jsonify, request


# ---------------------------------------------------------------------------
# 辅助函数：必须在 WORKFLOW_MARKERS 构造之前定义
# ---------------------------------------------------------------------------

def _order_label(index: int) -> str:
    labels = {
        1: "新建", 2: "分发", 3: "暂存", 4: "提交",
        5: "生成子订单", 6: "录费用", 7: "资产推送审批",
        8: "订单锁定审批", 9: "未放款开票申请审批",
        10: "供应商垫付申请审批", 11: "生成费用通知单", 12: "生成费用确认单",
    }
    return labels.get(index, f"订单阶段{index}")


def _pay_receive_label(index: int) -> str:
    if 1 <= index <= 7:
        labels = {
            1: "发起应付对账批次", 2: "确认应付对账",
            3: "发起应付开票批次申请", 4: "应付发票上传与登记",
            5: "发起付款需求", 6: "审核生成付款单", 7: "付款单核销",
        }
        return labels.get(index, f"应付阶段{index}")
    if 8 <= index <= 13:
        labels = {
            8: "发起应收对账批次", 9: "确认应收对账",
            10: "发起应收开票批次审批", 11: "审核生成开票申请",
            12: "发票上传与登记", 13: "应收核销",
        }
        return labels.get(index, f"应收阶段{index}")
    return f"链路{index}"


def _receive_pay_label(index: int) -> str:
    if 1 <= index <= 6:
        labels = {
            1: "发起应收对账批次", 2: "确认应收对账",
            3: "发起应收开票批次审批", 4: "审核生成开票申请",
            5: "发票上传与登记", 6: "应收核销",
        }
        return labels.get(index, f"应收阶段{index}")
    if 7 <= index <= 13:
        labels = {
            7: "发起应付对账批次", 8: "确认应付对账",
            9: "发起应付开票批次申请", 10: "应付发票上传与登记",
            11: "发起付款需求", 12: "审核生成付款单", 13: "付款单核销",
        }
        return labels.get(index, f"应付阶段{index}")
    return f"链路{index}"


# ---------------------------------------------------------------------------
# 构造 marker 列表（依赖上面的辅助函数）
# ---------------------------------------------------------------------------

WORKFLOW_MARKERS = {
    "order_only": [
        {"name": f"order{i}", "description": f"链路{i}：{_order_label(i)}", "workflow_type": "order_only"}
        for i in range(1, 13)
    ],
    "pay_receive": [
        *[
            {"name": f"order_pay_receive{i}", "description": f"订单+应付链路{i}：{_pay_receive_label(i)}", "workflow_type": "pay_receive"}
            for i in range(1, 8)
        ],
        *[
            {"name": f"order_pay_receive{i}", "description": f"订单+应付+应收链路{i}：{_pay_receive_label(i)}", "workflow_type": "pay_receive"}
            for i in range(8, 14)
        ],
    ],
    "receive_pay": [
        *[
            {"name": f"order_receive_pay{i}", "description": f"订单+应收链路{i}：{_receive_pay_label(i)}", "workflow_type": "receive_pay"}
            for i in range(1, 7)
        ],
        *[
            {"name": f"order_receive_pay{i}", "description": f"订单+应收+应付链路{i}：{_receive_pay_label(i)}", "workflow_type": "receive_pay"}
            for i in range(7, 14)
        ],
    ],
}

MARKERS = [marker for group in WORKFLOW_MARKERS.values() for marker in group]

bp = Blueprint("markers", __name__)


@bp.route("/api/markers", methods=["GET"])
def list_markers():
    workflow_type = (request.args.get("workflow_type") or "").strip().lower()
    if not workflow_type or workflow_type not in WORKFLOW_MARKERS:
        return jsonify({"markers": MARKERS})
    return jsonify({"markers": WORKFLOW_MARKERS[workflow_type]})
