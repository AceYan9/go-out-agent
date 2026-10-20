# @Time: 2026/10/19 16:10
# @Author: yanggan

from typing import Literal

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

from app.llm import llm
from app.agent.workflows.common import AgentState
from app.agent.workflows import weather_workflow, requirement_workflow


class IntentResult(BaseModel):
    intent: Literal["requirement", "weather", "unknown"]


intent_llm = llm.with_structured_output(
    IntentResult,
    method="function_calling",
)


def classify_intent_node(state: AgentState):
    result = intent_llm.invoke(
        f"""
        判断用户输入属于哪种意图。

        requirement：用户希望分析、设计、拆解或规划一个软件需求。
        weather：用户表达了要查询天气或者去某个地方，并且提供了可识别的城市。
        unknown：不属于以上两种，或者无法明确判断。

        用户输入：{state["user_input"]}
        """
    )

    return {"intent": result.intent}


def route_by_intent(state: AgentState):
    return state["intent"]


def fallback_node(state: AgentState):
    return {"result": "暂时无法理解，请重新描述。"}


builder = StateGraph(AgentState)

builder.add_node("classify_intent", classify_intent_node)
builder.add_node("weather", weather_workflow)
builder.add_node("requirement", requirement_workflow)
builder.add_node("fallback", fallback_node)

builder.add_edge(START, "classify_intent")

builder.add_conditional_edges(
    "classify_intent",
    route_by_intent,
    {
        "requirement": "requirement",
        "weather": "weather",
        "unknown": "fallback",
    },
)

builder.add_edge("weather", END)
builder.add_edge("requirement", END)
builder.add_edge("fallback", END)

# 编译
workflow = builder.compile()
