# @Time: 2026/10/19 16:09
# @Author: yanggan

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

    async def validate(self):
        pass
