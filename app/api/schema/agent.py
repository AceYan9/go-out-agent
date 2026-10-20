# @Time: 2026/10/19 20:49
# @Author: yanggan

from pydantic import BaseModel


class UserInputSchema(BaseModel):
    user_input: str
