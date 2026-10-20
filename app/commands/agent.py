# @Time: 2026/10/19 16:09
# @Author: yanggan

from collections.abc import AsyncIterator

from app.agent.workflow import workflow


class SearchCommand:
    def __init__(self, user_input: str):
        self._user_input = user_input

    async def run(self):
        await self.validate()
        state = workflow.invoke({
            "user_input": self._user_input,
        })

        if state.get("error"):
            return {
                "success": False,
                "error": state["error"],
            }

        return {
            "success": True,
            "data": state["result"],
        }

    async def stream(self) -> AsyncIterator[dict]:
        """Yield workflow task lifecycle events and the final workflow result.

        ``tasks`` emits an event as soon as a LangGraph node is scheduled, which
        is the earliest point at which the client can be told that a node is
        running. The root ``values`` event contains the complete final state,
        so the final result does not depend on how a nested subgraph formats its
        individual ``updates`` event.
        """
        final_state = None

        try:
            async for chunk in workflow.astream(
                {"user_input": self._user_input},
                stream_mode=["tasks", "updates", "values"],
                subgraphs=True,
            ):
                namespace, mode, payload = self._unpack_stream_chunk(chunk)

                if mode == "tasks":
                    event_name = (
                        "node_completed"
                        if self._is_task_finished(payload)
                        else "node_started"
                    )
                    yield {
                        "event": event_name,
                        "data": {
                            "node": payload.get("name"),
                            "path": list(namespace),
                            "error": payload.get("error"),
                        },
                    }
                elif mode == "updates":
                    for node, update in payload.items():
                        if update.get("error"):
                            yield {
                                "event": "error",
                                "data": {
                                    "node": node,
                                    "path": list(namespace),
                                    "message": update["error"],
                                },
                            }

                elif mode == "values" and not namespace:
                    # ``values`` is emitted once at the beginning and after
                    # every completed root-graph step. Keep the last one.
                    final_state = payload

            if final_state and final_state.get("result") is not None:
                yield {
                    "event": "result",
                    "data": {"result": final_state["result"]},
                }
            elif final_state and final_state.get("error"):
                yield {
                    "event": "error",
                    "data": {"message": final_state["error"]},
                }
            else:
                yield {
                    "event": "error",
                    "data": {"message": "工作流未返回结果"},
                }
            yield {
                "event": "done",
                "data": {"success": bool(final_state and final_state.get("result") is not None)},
            }
        except Exception as exc:
            yield {"event": "error", "data": {"message": str(exc)}}
            yield {"event": "done", "data": {"success": False}}

    @staticmethod
    def _unpack_stream_chunk(chunk):
        """Normalize LangGraph chunks with and without subgraph namespaces."""
        if len(chunk) == 3:
            namespace, mode, payload = chunk
        else:
            mode, payload = chunk
            namespace = ()
        return namespace, mode, payload

    @staticmethod
    def _is_task_finished(payload: dict) -> bool:
        # Task-start events contain input/triggers; task-finish events contain
        # result, error, or interrupts (including a successful None result).
        return any(key in payload for key in ("result", "error", "interrupts"))

    async def validate(self):
        pass
