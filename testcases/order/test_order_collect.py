"""
smoke????order ????workflow/test data ????????????pytest ??????"""
import allure
import pytest

from workflows.order_workflow import OrderWorkflow
from data.order import BookRealAmountData
from utils import generate_bl_no


@pytest.mark.order1
def test_order_import_smoke():
    bl_no = generate_bl_no(999)
    assert bl_no
    assert BookRealAmountData.get_customer_standard_fees()
    assert BookRealAmountData.get_supplier_standard_fees()

