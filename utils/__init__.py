"""
工具层公共模块

统一测试数据生成器：
  generate_bl_no(link, prefix)  : 提单号，格式 {prefix}-LK{link:02d}{datetime}{ms}{rnd}，
                                  如 MYCO-LK01-260702153045123A1B2C3
  generate_invoice_no(type)     : 发票号，格式 {AR|AP}-{yymmddHHMMSS}{rnd}，
                                  如 AR-260702163045A3F2D1
"""
from utils.generate import generate_bl_no, generate_invoice_no

__all__ = ["generate_bl_no", "generate_invoice_no"]
