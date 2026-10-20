# @Time: 2026/10/19 15:54
# @Author: yanggan

import logging
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.schema.agent import UserInputSchema
from app.commands.agent import SearchCommand

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", summary="Main (SSE stream)")
async def search_stream(body_data: UserInputSchema):
    """Stream node progress and the final result using Server-Sent Events.

    This is a POST endpoint, so browser clients should consume it with
    ``fetch``/``ReadableStream`` rather than ``EventSource`` (which only
    supports GET requests).
    """
    command = SearchCommand(body_data.user_input)

    async def event_source() -> AsyncIterator[str]:
        async for item in command.stream():
            event = item["event"]
            data = json.dumps(item["data"], ensure_ascii=False, default=str)
            yield f"event: {event}\ndata: {data}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
