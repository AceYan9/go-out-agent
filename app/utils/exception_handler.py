# @Time: 2026/10/19 17:01
# @Author: yanggan

class BizException(Exception):
    def __init__(self, message: str):
        self.message = message
