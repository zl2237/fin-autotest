import os

bind = f"0.0.0.0:{os.getenv('PLATFORM_PORT', '3000')}"
workers = 1
worker_class = "sync"
timeout = 0
keepalive = 5

# 重要：gunicorn 启动目标为 server:app（不是 app.py）
accesslog = "-"
errorlog = "-"
loglevel = "info"

reload = False

# 自动读取 PLATFORM_PORT 环境变量覆盖上述绑定
_bind = os.getenv("PLATFORM_PORT")
if _bind:
    bind = f"0.0.0.0:{_bind}"
