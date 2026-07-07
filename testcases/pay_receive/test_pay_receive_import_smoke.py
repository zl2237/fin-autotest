"""
smoke：验证 pay_receive 目录下 workflow/helpers 可导入。
"""
import allure
import pytest

from workflows.pay_receive_workflow import PayReceiveWorkflow
from testcases.pay_receive.helpers import _build_fee_config


@pytest.mark.order_pay_receive1
def test_pay_receive_import_smoke():
    config = _build_fee_config()
    assert config['to_customer_fees']
    assert config['to_supplier_fees']
