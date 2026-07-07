import os
from loguru import logger
from config.settings import LOG_DIR
from datetime import datetime

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 加 PID 隔离，避免多进程同时启动时日志文件名冲突
log_file = os.path.join(
    LOG_DIR,
    f"auto_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}.log"
)

logger.add(
    log_file,
    rotation="500MB",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

log = logger