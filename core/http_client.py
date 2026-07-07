import os
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from utils.logger import log
from config.settings import BASE_URL

# 关闭 SSL 证书验证（部分内网环境需要）
SSL_VERIFY = os.getenv("SSL_VERIFY", "false").lower() not in ("false", "0", "no", "")

# SSL_VERIFY=False 时抑制不安全请求警告
if not SSL_VERIFY:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class HttpClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        if not SSL_VERIFY:
            self.session.verify = False

    def _make_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return self.base_url + url

    def request(self, method, url, **kwargs):
        full_url = self._make_url(url)
        log.info(f"请求地址: {full_url}")
        log.info(f"请求方式: {method}")
        log.info(f"请求头: {dict(self.session.headers)}")
        log.info(f"请求参数: {kwargs}")

        try:
            resp = self.session.request(method, full_url, **kwargs)
            log.info(f"响应状态码: {resp.status_code}")
            log.info(f"响应内容: {resp.text}")
            return resp
        except Exception as e:
            log.error(f"请求异常: {str(e)}")
            raise

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def request_full_url(self, method, full_url: str, **kwargs):
        """直接使用完整 URL（用于跨 base_url 的接口调用，如财务系统）"""
        log.info(f"请求地址: {full_url}")
        log.info(f"请求方式: {method}")
        log.info(f"请求头: {dict(self.session.headers)}")
        log.info(f"请求参数: {kwargs}")

        try:
            resp = self.session.request(method, full_url, **kwargs)
            log.info(f"响应状态码: {resp.status_code}")
            log.info(f"响应内容: {resp.text}")
            return resp
        except Exception as e:
            log.error(f"请求异常: {str(e)}")
            raise

    def post_full_url(self, full_url: str, **kwargs):
        return self.request_full_url("POST", full_url, **kwargs)

http = HttpClient()