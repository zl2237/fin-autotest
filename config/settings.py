import os
from pathlib import Path
from dotenv import load_dotenv

# 项目路径
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# 环境变量加载（从 .env 文件）
# ============================================================
# 尝试加载 .env 文件
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)
    print(f"[INFO] 已加载环境变量文件: {_env_file}")
else:
    print(f"[WARN] 未找到环境变量文件: {_env_file}，将使用默认值")


# ============================================================
# 路径配置（非敏感）
# ============================================================
PATH_CONFIG = {
    "log_dir": BASE_DIR / "report" / "logs",
    "allure_result_dir": BASE_DIR / "report" / "allure-results",
    "attachment_dir": BASE_DIR / "data" / "attachment",
}

LOG_DIR = str(PATH_CONFIG["log_dir"])
ALLURE_RESULT_DIR = str(PATH_CONFIG["allure_result_dir"])
TEST_DATA_DIR = str(PATH_CONFIG["attachment_dir"])
LOG_RETENTION = 7


# ============================================================
# 敏感配置（从环境变量读取，优先使用 .env 中的值）
# ============================================================

# API 基础地址
BASE_URL = os.getenv("BASE_URL", "https://your-api-domain.com")

# 登录配置
LOGIN_URL = os.getenv("LOGIN_URL", "/api/home/login/userLogin")
USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")
TOKEN_FIELD = os.getenv("TOKEN_FIELD", "data.token")
TOKEN_TYPE = os.getenv("TOKEN_TYPE", "")
AUTH_HEADER = os.getenv("AUTH_HEADER", "Authorization")

LOGIN_CONFIG = {
    "url": LOGIN_URL,
    "username": USERNAME,
    "password": PASSWORD,
    "token_field": TOKEN_FIELD,
    "token_type": TOKEN_TYPE,
    "auth_header": AUTH_HEADER,
}

# 订单操作员配置
ORDER_OPERATOR_CONFIG = {
    "create_id": os.getenv("ORDER_CREATE_ID", ""),
    "username": os.getenv("USERNAME", ""),
}
