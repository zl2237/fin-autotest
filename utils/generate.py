"""
工具层 - 测试数据生成器

统一管理所有需要全局唯一的测试数据生成函数：

  generate_bl_no(link, prefix) : 提单号，格式 {prefix}-LK{link:02d}{datetime}{ms}{rnd}，
                                 如 MYCO-LK01-260702153045123A1B2C3（用户前缀来自界面或环境变量）
  generate_invoice_no(type)   : 发票号，格式 {AR|AP}-{yymmddHHMMSS}{rnd}，
                                 如 AR-260702163045A3F2D1

设计原则：
  1. 尽可能短
  2. 每次唯一（毫秒时间戳 + 长随机 hex）
  3. 体现所选链路 / 业务类型
  4. 提单号由用户自定义前缀 + 系统生成后缀两部分构成
"""
import os
import random
import time
import uuid


# ------------------------------------------------------------------
# 提单号
# ------------------------------------------------------------------

def generate_bl_no(link: int = 1, prefix: str = None) -> str:
    """
    生成唯一提单号。

    格式：{prefix}-LK{link:02d}{datetime}{ms}{rnd}
    示例：
      MYCO-LK01-260702153045123A1B2C3   (prefix="MYCO", link=1)
      TEST-LK12-2607021530454563B8C9D0   (prefix="TEST", link=12)
      AUTO-LK101-260702153045789C4D7E1F2  (prefix=默认环境变量 ORDER_PREFIX 或 "AUTO", link=101)

    Args:
        link   : 链路编号，直接拼入编号位
                 1-9   → LK01 ~ LK09
                 10-99 → LK10 ~ LK99
                 100+  → LK100 ~ LK999
        prefix : 用户自定义前缀（来自界面输入或环境变量 ORDER_PREFIX），
                 默认读取 ORDER_PREFIX，不存在则使用 "AUTO"

    Returns:
        约 24~32 字符的唯一提单号
    """
    if prefix is None:
        prefix = os.getenv("ORDER_PREFIX", "AUTO")
    now = time.time()
    datetime_part = time.strftime("%y%m%d%H%M%S", time.localtime(now))  # 12 位：260702153045
    ms_part = f"{int((now - int(now)) * 1000):03d}"  # 3 位毫秒：123
    rnd_part = uuid.uuid4().hex[:6].upper()  # 6 位随机 hex
    return f"{prefix}_LK{link:02d}{datetime_part}{ms_part}{rnd_part}"


# ------------------------------------------------------------------
# 发票号（应收 AR / 应付 AP）
# ------------------------------------------------------------------

def generate_invoice_no(invoice_type: str = "AR") -> str:
    """
    生成唯一发票号码。

    格式：{AR|AP}-{yymmddHHMMSS}{rnd}
    示例：AR-260702163045A3F2D1  (应收),  AP-260702163045B7C9E0  (应付)

    Args:
        invoice_type: AR = 应收发票，AP = 应付发票

    Returns:
        18 字符的唯一发票号
    """
    prefix    = "AR" if invoice_type == "AR" else "AP"
    ts        = time.strftime("%y%m%d%H%M%S")          # 12 位
    rnd_front = uuid.uuid4().hex[:2].upper()           # 2 位
    rnd_back  = random.choice("0123456789ABCDEF") + random.choice("0123456789ABCDEF")
    return f"{prefix}-{ts}{rnd_front}{rnd_back}"
