"""
smoke：验证 receive_pay 目录下 workflow/helpers 可导入。
"""
import allure
import pytest

from workflows.receive_pay_workflow import ReceivePayWorkflow
from testcases.receive_pay.helpers import _build_fee_config


@pytest.mark.order_receive_pay1
def test_receive_pay_import_smoke():
    config = _build_fee_config()
    assert config['to_customer_fees']
    assert config['to_supplier_fees']
