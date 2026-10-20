# @Time: 2026/10/20 09:32
# @Author: yanggan

import operator
from typing import TypedDict, NotRequired, Any, Annotated


class AgentState(TypedDict):
    user_input: str
    intent: str
    process_data: Annotated[
        NotRequired[dict[str, Any]],
        operator.or_,
    ]
    error: NotRequired[str]
    result: NotRequired[dict[str, Any]]
