# @Time: 2026/10/19 16:21
# @Author: yanggan

import hmac
import hashlib
import base64
import uuid
import requests
from datetime import datetime

from langchain_core.tools import tool

from app.config import settings
from app.utils.exception_handler import BizException


@tool
def get_weather(longitude: str, latitude: str) -> dict:
    """查询指定经纬度的天气信息，返回天气状况、温度等数据。"""

    def get_signature():
        h = hmac.new(
            settings.CAIYUN_APP_SECRET.encode("utf-8"),
            f"{method}:{path}::{settings.CAIYUN_APP_KEY}:{nonce}:{ts}".encode("utf-8"),
            hashlib.sha256,
        )
        return base64.urlsafe_b64encode(h.digest()).decode("utf-8")

    nonce = str(uuid.uuid4())
    ts = int(datetime.now().timestamp())
    path = f"/v2.6/{settings.CAIYUN_APP_KEY}/{longitude},{latitude}/realtime"
    method = "GET"
    headers = {
        "x-cy-nonce": nonce,
        "x-cy-timestamp": str(ts),
        "x-cy-signature": get_signature()
    }

    try:
        response = requests.get(
            f"{settings.CAIYUN_WEATHER_URL}/{path}",
            headers=headers
        )
        data = response.json()
    except Exception as e:
        raise BizException(str(e))
    else:
        return data["result"]["realtime"]
