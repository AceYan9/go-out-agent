# @Time: 2026/10/19 15:54
# @Author: yanggan

import logging

from fastapi import APIRouter

from app.api.schema.agent import UserInputSchema
from app.api.schema.common import ApiResponse
from app.commands.agent import SearchCommand

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=ApiResponse, summary="Main")
async def search(body_data: UserInputSchema):
    command = SearchCommand(body_data.user_input)
    data = await command.run()
    if not data["success"]:
        return {"code": 1, "message": data["error"]}
    return {"data": data["data"]}
