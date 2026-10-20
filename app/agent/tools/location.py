# @Time: 2026/10/19 17:21
# @Author: yanggan

import requests

from langchain_core.tools import tool

from app.config import settings
from app.utils.exception_handler import BizException


@tool
def get_location(city: str) -> (str, str):
    """查询指定地址的经纬度信息"""
    try:
        response = requests.get(f"{settings.GAODE_GEO_URL}?address={city}&key={settings.GAODE_KEY}")
        data = response.json()
    except Exception as e:
        raise BizException(str(e))
    else:
        return data["geocodes"][0]["location"].split(",")
