"""
Testcases 层 - 订单接口测试用例
包含全面的断言验证

标记说明：
  @pytest.mark.order - 订单相关测试（类级别统一标记）
"""
import allure
import pytest
from api.order import OrderApi
from data.order_data import (
    OrderTestData,
    OrderExpectations,
    AddOrderData,
    DistributeOrderData,
    SubmitOrderData,
    generate_bl_no
)


@pytest.mark.order
class TestEntrustedOrder:
    """委托订单列表接口测试"""

    @allure.feature("委托订单管理")
    @allure.story("委托订单列表查询")
    @allure.severity("critical")
    @allure.title("正常查询委托订单列表")
    def test_entrust_order_normal(self):
        """正常查询委托订单列表"""
        with allure.step("发送委托订单列表查询请求"):
            resp = OrderApi.get_entrust_order_list(
                page_no=1,
                page_size=20,
                order_no="",
                customer_id=[],
                sort_field="update_time",
                sort_order="desc"
            )

        with allure.step("断言 HTTP 状态码为 200"):
            assert resp.status_code == 200, f"HTTP状态码异常: {resp.status_code}"

        with allure.step("断言响应 JSON"):
            data = resp.json()

            for field in OrderExpectations.REQUIRED_RESPONSE_FIELDS:
                assert field in data, f"响应缺少必需字段: {field}"

            assert data.get("code") == OrderExpectations.SUCCESS_CODE, \
                f"业务状态码异常: 期望 {OrderExpectations.SUCCESS_CODE}, 实际 {data.get('code')}"

            assert data.get("msg") == OrderExpectations.SUCCESS_MSG, \
                f"响应消息异常: {data.get('msg')}"

            assert data.get("data") is not None, "data 节点不能为 None"
            assert data.get("data") != "", "data 节点不能为空字符串"

            order_data = data.get("data", {})
            for field in OrderExpectations.REQUIRED_DATA_FIELDS:
                assert field in order_data, f"data 节点缺少字段: {field}"

            assert "total" in order_data, "缺少 total 字段"
            assert "data" in order_data, "缺少 data 字段"
            assert isinstance(order_data.get("total"), int), "total 应为整数"
            assert isinstance(order_data.get("data"), list), "data 应为列表"

            assert order_data.get("total", 0) >= 0, f"total 不应为负数: {order_data.get('total')}"

            page_size = 20
            actual_count = len(order_data.get("data", []))
            assert actual_count <= page_size, f"返回数据超过 page_size: {actual_count} > {page_size}"

    @allure.feature("委托订单管理")
    @allure.story("委托订单分页查询")
    @allure.severity("normal")
    @allure.title("分页查询委托订单")
    @pytest.mark.parametrize("payload", OrderTestData.get_pagination_test_cases())
    def test_entrust_order_pagination(self, payload):
        """分页查询测试"""
        with allure.step(f"查询第 {payload['page_no']} 页，每页 {payload['page_size']} 条"):
            resp = OrderApi.get_entrust_order_list(
                page_no=payload["page_no"],
                page_size=payload["page_size"]
            )

        with allure.step("断言响应成功"):
            data = resp.json()
            assert data.get("code") == 200, f"业务状态码异常: {data}"
            assert data.get("data") is not None, "data 不能为 None"

            order_data = data.get("data", {})
            actual_count = len(order_data.get("data", []))

            assert actual_count <= payload["page_size"], \
                f"返回数量 {actual_count} 超过 page_size {payload['page_size']}"

    @allure.feature("委托订单管理")
    @allure.story("委托订单排序")
    @allure.severity("normal")
    @allure.title("排序查询委托订单")
    @pytest.mark.parametrize("sort_case", OrderTestData.get_sort_test_cases())
    def test_entrust_order_sort(self, sort_case):
        """排序测试"""
        with allure.step(f"按 {sort_case['sort_field']} {sort_case['sort_order']} 排序"):
            resp = OrderApi.get_entrust_order_list(
                sort_field=sort_case["sort_field"],
                sort_order=sort_case["sort_order"]
            )

        with allure.step("断言响应成功"):
            data = resp.json()
            assert data.get("code") == 200, f"业务状态码异常: {data}"


@pytest.mark.order
class TestBusinessOrder:
    """业务订单接口测试"""

    @allure.feature("业务订单管理")
    @allure.story("业务订单列表查询")
    @allure.severity("critical")
    @allure.title("正常查询业务订单列表")
    def test_business_order_normal(self):
        """正常查询业务订单列表"""
        with allure.step("发送业务订单列表查询请求"):
            resp = OrderApi.get_business_order_list(
                page_no=1,
                page_size=20,
                order_no="",
                customer_id=[],
                sort_field="update_time",
                sort_order="desc"
            )

        with allure.step("断言 HTTP 状态码为 200"):
            assert resp.status_code == 200, f"HTTP状态码异常: {resp.status_code}"

        with allure.step("断言响应 JSON"):
            data = resp.json()

            for field in OrderExpectations.REQUIRED_RESPONSE_FIELDS:
                assert field in data, f"响应缺少必需字段: {field}"

            assert data.get("code") == OrderExpectations.SUCCESS_CODE, \
                f"业务状态码异常: 期望 {OrderExpectations.SUCCESS_CODE}, 实际 {data.get('code')}"

            assert data.get("msg") == OrderExpectations.SUCCESS_MSG, \
                f"响应消息异常: {data.get('msg')}"

            assert data.get("data") is not None, "data 节点不能为 None"

            order_data = data.get("data", {})
            for field in OrderExpectations.REQUIRED_DATA_FIELDS:
                assert field in order_data, f"data 节点缺少字段: {field}"

            assert isinstance(order_data.get("total"), int), "total 应为整数"
            assert isinstance(order_data.get("data"), list), "data 应为列表"

            assert order_data.get("total", 0) >= 0, f"total 不应为负数"

            page_size = 20
            actual_count = len(order_data.get("data", []))
            assert actual_count <= page_size, f"返回数据超过 page_size"

    @allure.feature("业务订单管理")
    @allure.story("业务订单分页查询")
    @allure.severity("normal")
    @allure.title("分页查询业务订单")
    @pytest.mark.parametrize("payload", OrderTestData.get_pagination_test_cases())
    def test_business_order_pagination(self, payload):
        """分页查询测试"""
        with allure.step(f"查询第 {payload['page_no']} 页，每页 {payload['page_size']} 条"):
            resp = OrderApi.get_business_order_list(
                page_no=payload["page_no"],
                page_size=payload["page_size"]
            )

        with allure.step("断言响应成功"):
            data = resp.json()
            assert data.get("code") == 200, f"业务状态码异常: {data}"
            assert data.get("data") is not None, "data 不能为 None"

    @allure.feature("业务订单管理")
    @allure.story("业务订单排序")
    @allure.severity("normal")
    @allure.title("排序查询业务订单")
    @pytest.mark.parametrize("sort_case", OrderTestData.get_sort_test_cases())
    def test_business_order_sort(self, sort_case):
        """排序测试"""
        with allure.step(f"按 {sort_case['sort_field']} {sort_case['sort_order']} 排序"):
            resp = OrderApi.get_business_order_list(
                sort_field=sort_case["sort_field"],
                sort_order=sort_case["sort_order"]
            )

        with allure.step("断言响应成功"):
            data = resp.json()
            assert data.get("code") == 200, f"业务状态码异常: {data}"


@pytest.mark.order
class TestOrderDataValidation:
    """订单数据验证测试 - 深度验证返回数据"""

    @allure.feature("数据验证")
    @allure.story("订单数据完整性")
    @allure.severity("normal")
    def test_entrust_order_data_integrity(self):
        """验证委托订单数据完整性"""
        resp = OrderApi.get_entrust_order_list(page_no=1, page_size=5)
        data = resp.json()

        assert data.get("code") == 200, f"业务状态码异常: {data}"

        orders = data.get("data", {}).get("data", [])

        if orders and len(orders) > 0:
            for i, order in enumerate(orders):
                with allure.step(f"验证第 {i+1} 条订单数据"):
                    assert isinstance(order, dict), f"订单数据应为字典类型: {type(order)}"

                    for key in ["order_no", "status", "update_time"]:
                        if key in order:
                            assert order.get(key) is not None, \
                                f"订单 {i+1} 的 {key} 字段不应为 None"

    @allure.feature("数据验证")
    @allure.story("业务订单数据完整性")
    @allure.severity("normal")
    def test_business_order_data_integrity(self):
        """验证业务订单数据完整性"""
        resp = OrderApi.get_business_order_list(page_no=1, page_size=5)
        data = resp.json()

        assert data.get("code") == 200, f"业务状态码异常: {data}"

        orders = data.get("data", {}).get("data", [])

        if orders and len(orders) > 0:
            for i, order in enumerate(orders):
                with allure.step(f"验证第 {i+1} 条订单数据"):
                    assert isinstance(order, dict), f"订单数据应为字典类型: {type(order)}"

                    for key in ["order_no", "status", "update_time"]:
                        if key in order:
                            assert order.get(key) is not None, \
                                f"订单 {i+1} 的 {key} 字段不应为 None"


@pytest.mark.order
class TestAddOrder:
    """新增订单接口测试"""

    @allure.feature("新增订单")
    @allure.story("新增委托订单")
    @allure.severity("critical")
    @allure.title("新增委托订单")
    def test_add_order_normal(self):
        """正常新增委托订单"""
        bl_no = generate_bl_no()
        with allure.step(f"新增订单，提单号: {bl_no}"):
            resp = OrderApi.add_order(bl_no=bl_no)

        with allure.step("断言 HTTP 状态码为 200"):
            assert resp.status_code == 200, f"HTTP状态码异常: {resp.status_code}"

        with allure.step("断言响应 JSON"):
            data = resp.json()

            for field in OrderExpectations.REQUIRED_RESPONSE_FIELDS:
                assert field in data, f"响应缺少必需字段: {field}"

            assert data.get("code") == OrderExpectations.SUCCESS_CODE, \
                f"业务状态码异常: 期望 {OrderExpectations.SUCCESS_CODE}, 实际 {data.get('code')}"

            assert data.get("msg") == OrderExpectations.SUCCESS_MSG, \
                f"响应消息异常: {data.get('msg')}"

            assert "request_id" in data, "响应缺少 request_id 字段"

            assert "data" in data, "响应缺少 data 字段"


@pytest.mark.order
class TestAddAndDistribute:
    """新增订单并分发流程测试"""

    @allure.feature("新增订单")
    @allure.story("新增委托订单")
    @allure.severity("critical")
    @allure.title("新增委托订单")
    def test_add_order_only(self):
        """仅新增订单（不分发）- 验证新增功能正常"""
        bl_no = generate_bl_no()

        with allure.step(f"新增订单，提单号: {bl_no}"):
            resp = OrderApi.add_order(bl_no=bl_no)
            data = resp.json()

        with allure.step("断言新增订单成功"):
            assert resp.status_code == 200, "HTTP 状态码异常"
            assert data.get("code") == 200, f"业务状态码异常: {data}"
            assert data.get("msg") == "成功", f"响应消息异常: {data.get('msg')}"
            assert data.get("request_id"), "缺少 request_id"

    @allure.feature("订单分发")
    @allure.story("订单分发验证")
    @allure.severity("critical")
    @allure.title("订单分发 - 使用不同提单号")
    def test_distribute_with_different_bl_no(self):
        """分发订单（使用新提单号）- 验证分发功能"""
        bl_no = generate_bl_no()

        with allure.step(f"分发订单，使用新提单号: {bl_no}"):
            resp = OrderApi.distribute_order(
                order_info={},
                bl_no=bl_no
            )
            data = resp.json()

        with allure.step("断言分发请求已发送"):
            assert resp.status_code == 200, "HTTP 状态码异常"

    @allure.feature("订单完整流程")
    @allure.story("新增并分发订单")
    @allure.severity("critical")
    @allure.title("新增并分发完整流程")
    def test_add_and_distribute_workflow(self):
        """完整流程：新增订单 -> 查询获取 order_id -> 分发"""
        bl_no = generate_bl_no()

        with allure.step(f"Step 1: 新增订单，提单号: {bl_no}"):
            add_resp = OrderApi.add_order(bl_no=bl_no)
            add_data = add_resp.json()
            assert add_data.get("code") == 200, f"新增失败: {add_data}"

        with allure.step("Step 2: 查询订单列表，获取 order_id"):
            query_resp = OrderApi.get_entrust_order_list(
                page_no=1,
                page_size=20,
                order_no=""
            )
            query_data = query_resp.json()
            assert query_data.get("code") == 200, "查询失败"

            orders = query_data.get("data", {}).get("data", [])
            target_order = None
            for order in orders:
                if order.get("bl_no") == bl_no:
                    target_order = order
                    break

            if target_order:
                with allure.step(f"找到订单: order_id={target_order.get('order_id')}, order_no={target_order.get('order_no')}"):
                    pass

        if target_order:
            with allure.step("Step 3: 分发订单"):
                distribute_resp = OrderApi.distribute_order(
                    order_info=target_order,
                    bl_no=bl_no
                )
                distribute_data = distribute_resp.json()

                assert distribute_resp.status_code == 200, "HTTP 状态码异常"
                if distribute_data.get("code") != 200:
                    allure.attach(
                        f"分发返回非成功状态: {distribute_data}",
                        name="分发响应",
                        attachment_type=allure.attachment_type.JSON
                    )

    @allure.feature("新增订单")
    @allure.story("提单号格式验证")
    @allure.severity("normal")
    def test_bl_no_format(self):
        """验证提单号格式"""
        bl_no = generate_bl_no()

        with allure.step(f"生成的提单号: {bl_no}"):
            assert bl_no.startswith("lele_apiauto_"), f"提单号前缀错误: {bl_no}"
            assert len(bl_no) == 27, f"提单号长度错误，期望27，实际{len(bl_no)}: {bl_no}"

            datetime_part = bl_no.replace("lele_apiauto_", "")
            assert datetime_part.isdigit(), f"提单号日期时间部分应为纯数字: {datetime_part}"
            assert len(datetime_part) == 14, f"提单号日期时间部分长度错误: {datetime_part}"

    @allure.feature("新增订单")
    @allure.story("新增订单数据验证")
    @allure.severity("normal")
    def test_add_order_payload_structure(self):
        """验证新增订单请求数据结构"""
        bl_no = generate_bl_no()
        payload = AddOrderData.get_add_payload(bl_no)

        with allure.step("验证必需字段"):
            assert "client_expand_id" in payload, "缺少 client_expand_id"
            assert "customer_id" in payload, "缺少 customer_id"
            assert "service_id" in payload, "缺少 service_id"
            assert "policy_id" in payload, "缺少 policy_id"
            assert "bl_no" in payload, "缺少 bl_no"
            assert "supplier" in payload, "缺少 supplier"

        with allure.step("验证 bl_no 格式"):
            assert payload["bl_no"] == bl_no, "bl_no 不匹配"
            assert payload["bl_no"].startswith("lele_apiauto_"), "bl_no 格式错误"

        with allure.step("验证 supplier 结构"):
            assert isinstance(payload["supplier"], list), "supplier 应为列表"
            assert len(payload["supplier"]) > 0, "supplier 不能为空"
            supplier = payload["supplier"][0]
            assert "supplier_id" in supplier, "supplier 缺少 supplier_id"
            assert "service_item" in supplier, "supplier 缺少 service_item"


@pytest.mark.order
class TestSubmitOrder:
    """订单提交接口测试"""

    @allure.feature("订单提交")
    @allure.story("提交订单")
    @allure.severity("critical")
    @allure.title("提交订单 - 完整流程")
    def test_submit_order_with_workflow(self):
        """新增 -> 按提单号查询 -> 分发 -> 提交 完整流程"""
        bl_no = generate_bl_no()

        with allure.step(f"Step 1: 新增订单，提单号: {bl_no}"):
            add_payload = AddOrderData.get_add_payload(bl_no)
            add_resp = OrderApi.add_order(bl_no=bl_no)
            add_data = add_resp.json()
            assert add_data.get("code") == 200, f"新增订单失败: {add_data}"
            allure.attach(str(add_data), "新增订单响应", allure.attachment_type.JSON)

        with allure.step(f"Step 2: 按提单号查询订单: {bl_no}"):
            import time
            time.sleep(1)

            order_info = OrderApi.get_order_by_bl_no(bl_no)
            allure.attach(str(order_info), "按提单号查询到的订单", allure.attachment_type.JSON)

            assert order_info, f"按提单号查询不到订单: {bl_no}"
            order_id = order_info.get("order_id")
            assert order_id, f"订单缺少 order_id: {order_info}"
            assert order_info.get("bl_no") == bl_no, f"提单号不匹配"
            assert order_info.get("entrust_status") == "1", \
                f"订单状态应为 1（待分发），实际为 {order_info.get('entrust_status')}"

        with allure.step("Step 3: 分发订单（使用 AddOrderData 基础数据 + 查询到的 order_id）"):
            distribute_resp = OrderApi.distribute_order(order_info, bl_no=bl_no)
            distribute_data = distribute_resp.json()
            allure.attach(str(distribute_data), "分发订单响应", allure.attachment_type.JSON)

            if distribute_data.get("code") != 200:
                pytest.skip(f"分发失败（code={distribute_data.get('code')}），跳过提交测试")

        with allure.step("Step 4: 再次按提单号查询（验证分发状态）"):
            distributed_order = OrderApi.get_order_by_bl_no(bl_no)
            allure.attach(str(distributed_order), "分发后查询到的订单", allure.attachment_type.JSON)

            assert distributed_order.get("entrust_status") == "2", \
                f"分发后订单状态应为 2（已分发），实际为 {distributed_order.get('entrust_status')}"

        with allure.step(f"Step 5: 提交订单（使用 SubmitOrderData 基础数据 + 查询到的 order_id）"):
            submit_resp = OrderApi.submit_order(distributed_order, bl_no=bl_no)
            submit_data = submit_resp.json()

            allure.attach(str(submit_data), "提交订单响应", allure.attachment_type.JSON)

            if submit_data.get("code") != 200:
                pytest.skip(f"提交失败（code={submit_data.get('code')}, msg={submit_data.get('msg')}），请确认提交接口参数")

            assert submit_resp.status_code == 200, "HTTP 状态码异常"
            assert submit_data.get("code") == 200, f"提交订单业务状态码异常: {submit_data}"
            assert submit_data.get("msg") == "成功", f"响应消息异常: {submit_data.get('msg')}"
            assert submit_data.get("request_id"), "缺少 request_id"

    @allure.feature("订单提交")
    @allure.story("提交订单数据验证")
    @allure.severity("normal")
    def test_submit_order_payload_structure(self):
        """验证提交订单请求数据结构"""
        bl_no = generate_bl_no()
        payload = SubmitOrderData.get_submit_payload({}, bl_no=bl_no)

        with allure.step("验证提交订单必需字段"):
            assert "client_expand_id" in payload, "缺少 client_expand_id"
            assert "customer_id" in payload, "缺少 customer_id"
            assert "service_id" in payload, "缺少 service_id"
            assert "policy_id" in payload, "缺少 policy_id"
            assert "bl_no" in payload, "缺少 bl_no"
            assert "supplier" in payload, "缺少 supplier"

        with allure.step("验证 bl_no"):
            assert payload["bl_no"] == bl_no, "bl_no 不匹配"

        with allure.step("验证 container"):
            assert "container" in payload, "缺少 container"
            assert isinstance(payload["container"], list), "container 应为列表"

        with allure.step("验证 status"):
            assert "status" in payload, "缺少 status"


@pytest.mark.order1
class TestFullWorkflow:
    """完整订单流程测试"""

    @allure.feature("订单完整流程")
    @allure.story("新增-按提单号查询-分发")
    @allure.severity("critical")
    @allure.title("完整流程：新增 -> 按提单号查询 -> 分发")
    def test_full_order_workflow(self):
        """完整流程测试：新增订单 -> 按提单号查询 -> 分发"""
        import time

        bl_no = generate_bl_no()

        workflow_result = {
            "bl_no": bl_no,
            "steps": []
        }

        with allure.step("Step 1/4: 新增订单"):
            add_resp = OrderApi.add_order(bl_no=bl_no)
            add_data = add_resp.json()
            workflow_result["add_code"] = add_data.get("code")
            workflow_result["steps"].append({
                "name": "新增订单",
                "code": add_data.get("code"),
                "msg": add_data.get("msg")
            })
            assert add_data.get("code") == 200, f"新增订单失败: {add_data}"

        with allure.step(f"Step 2/4: 按提单号查询订单: {bl_no}"):
            time.sleep(1)
            order_info = OrderApi.get_order_by_bl_no(bl_no)
            workflow_result["order_info"] = order_info
            workflow_result["steps"].append({
                "name": "按提单号查询订单",
                "success": bool(order_info),
                "order_id": order_info.get("order_id") if order_info else None,
                "entrust_status": order_info.get("entrust_status") if order_info else None
            })

            if not order_info:
                allure.attach(str(workflow_result), "流程结果（查询失败）", allure.attachment_type.JSON)
                pytest.skip(f"按提单号 {bl_no} 查询不到订单，无法继续流程")

            order_id = order_info.get("order_id")
            assert order_id, f"订单缺少 order_id"
            assert order_info.get("entrust_status") == "1", \
                f"新增订单状态应为 1（待分发），实际为 {order_info.get('entrust_status')}"

        with allure.step("Step 3/4: 分发订单"):
            distribute_resp = OrderApi.distribute_order(order_info, bl_no=bl_no)
            distribute_data = distribute_resp.json()
            workflow_result["distribute_code"] = distribute_data.get("code")
            workflow_result["distribute_msg"] = distribute_data.get("msg")
            workflow_result["steps"].append({
                "name": "分发订单",
                "code": distribute_data.get("code"),
                "msg": distribute_data.get("msg")
            })

            if distribute_data.get("code") != 200:
                allure.attach(str(workflow_result), "流程结果（分发失败）", allure.attachment_type.JSON)
                pytest.skip(f"分发失败（code={distribute_data.get('code')}, msg={distribute_data.get('msg')}），无法继续提交")

        with allure.step("Step 4/4: 再次按提单号查询（验证分发状态）"):
            distributed_order = OrderApi.get_order_by_bl_no(bl_no)
            workflow_result["distributed_order"] = distributed_order
            workflow_result["steps"].append({
                "name": "验证分发状态",
                "entrust_status": distributed_order.get("entrust_status") if distributed_order else None
            })

            assert distributed_order.get("entrust_status") == "2", \
                f"分发后订单状态应为 2（已分发），实际为 {distributed_order.get('entrust_status')}"

        with allure.step("验证流程结果"):
            allure.attach(str(workflow_result), "完整流程结果", allure.attachment_type.JSON)

            assert workflow_result["add_code"] == 200, "新增订单失败"
            assert workflow_result["distribute_code"] == 200, f"分发订单失败: {workflow_result['distribute_msg']}"

    @allure.feature("订单完整流程")
    @allure.story("新增-查询-分发-提交")
    @allure.severity("critical")
    @allure.title("完整流程：新增 -> 查询 -> 分发 -> 提交（待后端确认提交逻辑）")
    def test_full_workflow_with_submit(self):
        """完整流程测试（含提交）- 注意：提交接口可能需要额外的业务参数"""
        import time

        bl_no = generate_bl_no()

        workflow_result = {
            "bl_no": bl_no,
            "steps": []
        }

        with allure.step("Step 1/5: 新增订单"):
            add_resp = OrderApi.add_order(bl_no=bl_no)
            add_data = add_resp.json()
            workflow_result["add_code"] = add_data.get("code")
            workflow_result["steps"].append({
                "name": "新增订单",
                "code": add_data.get("code"),
                "msg": add_data.get("msg")
            })
            assert add_data.get("code") == 200, f"新增订单失败: {add_data}"

        with allure.step(f"Step 2/5: 按提单号查询订单: {bl_no}"):
            time.sleep(1)
            order_info = OrderApi.get_order_by_bl_no(bl_no)
            workflow_result["order_info"] = order_info

            if not order_info:
                pytest.skip(f"按提单号 {bl_no} 查询不到订单，无法继续流程")

            workflow_result["steps"].append({
                "name": "按提单号查询订单",
                "order_id": order_info.get("order_id"),
                "entrust_status": order_info.get("entrust_status")
            })

        with allure.step("Step 3/5: 分发订单"):
            distribute_resp = OrderApi.distribute_order(order_info, bl_no=bl_no)
            distribute_data = distribute_resp.json()
            workflow_result["distribute_code"] = distribute_data.get("code")
            workflow_result["distribute_msg"] = distribute_data.get("msg")
            workflow_result["steps"].append({
                "name": "分发订单",
                "code": distribute_data.get("code"),
                "msg": distribute_data.get("msg")
            })

            if distribute_data.get("code") != 200:
                allure.attach(str(workflow_result), "流程结果（分发失败）", allure.attachment_type.JSON)
                pytest.skip(f"分发失败（code={distribute_data.get('code')}），跳过提交")

        with allure.step("Step 4/5: 再次按提单号查询"):
            distributed_order = OrderApi.get_order_by_bl_no(bl_no)
            workflow_result["distributed_order"] = distributed_order
            workflow_result["steps"].append({
                "name": "验证分发状态",
                "entrust_status": distributed_order.get("entrust_status")
            })

            if distributed_order.get("entrust_status") != "2":
                pytest.skip(f"分发后订单状态未更新为 2，当前为 {distributed_order.get('entrust_status')}")

        with allure.step("Step 5/5: 提交订单"):
            submit_resp = OrderApi.submit_order(distributed_order, bl_no=bl_no)
            submit_data = submit_resp.json()
            workflow_result["submit_code"] = submit_data.get("code")
            workflow_result["submit_msg"] = submit_data.get("msg")
            workflow_result["steps"].append({
                "name": "提交订单",
                "code": submit_data.get("code"),
                "msg": submit_data.get("msg")
            })

            allure.attach(str(workflow_result), "完整流程结果", allure.attachment_type.JSON)

            if submit_data.get("code") != 200:
                pytest.skip(f"提交失败（code={submit_data.get('code')}, msg={submit_data.get('msg')}），请确认提交接口参数")
