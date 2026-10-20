# @Time: 2026/10/19 15:48
# @Author: yanggan

import os


class Settings:
    PROJECT_NAME = "GoOutAgent"

    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    OPENAI_KEY = os.getenv("OPENAI_KEY")

    CAIYUN_APP_KEY = os.getenv("CAIYUN_APP_KEY")
    CAIYUN_APP_SECRET = os.getenv("CAIYUN_APP_SECRET")
    CAIYUN_WEATHER_URL = f"https://api.caiyunapp.com"
    SIGNATURE_SECRET_KEY = os.getenv("SIGNATURE_SECRET_KEY")

    GAODE_GEO_URL = "https://restapi.amap.com/v3/geocode/geo"
    GAODE_KEY = os.getenv("GAODE_KEY")


settings = Settings()
