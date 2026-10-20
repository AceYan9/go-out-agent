# @Time: 2026/10/19 16:26
# @Author: yanggan

import secrets
import string


def get_random_string(length: int = 16):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))
