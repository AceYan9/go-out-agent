# @Time: 2026/10/20 09:22
# @Author: yanggan

import json
from typing import Dict

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

from app.llm import llm
from app.agent.workflows.common import AgentState


# 判断需求是否完整且闭环
def judge_requirement_complete_node(state: AgentState):
    judge_time = state.get("process_data", {}).get("judge_time") or 0
    requirement = state.get("process_data", {}).get("current_requirement") or state["user_input"]
    response = llm.invoke(
        f"""
        用户提了一个需求说明，帮我判断需求是否完整且闭环
        判断标准：
        - true：需求足够明确，可以进入开发任务拆解。
        - false：存在影响核心功能、实现方案或工期的关键信息缺失。
        只允许返回 true 或 false，不要输出其他内容。
        用户输入：{requirement}
        """
    )
    print(f"======> {judge_time} {response.content}")
    judge_time += 1

    return {
        "process_data": {
            "judge_time": judge_time,
            "is_complete": response.content.strip().lower() == "true"
        }
    }


def route_requirement_node(state: AgentState):
    if state.get("process_data", {}).get("is_complete"):
        return "complete"
    if state.get("process_data", {}).get("judge_time") > 2:
        return "complete"
    return "incomplete"


# 补充需求
def fill_requirement_node(state: AgentState):
    if not (current_requirement := state.get("process_data", {}).get("current_requirement")):
        current_requirement = state.get("user_input")

    response = llm.invoke(
        f"""
        按照当前需求说明，填充未明确的定义以及未闭环的逻辑，需求需要明确完整且闭环
        当前需求：{current_requirement}
        """
    )
    return {
        "process_data": {
            "current_requirement": response.content,
        }
    }


# todo 拆分任务
def split_task_node(state: AgentState):
    current_requirement = state.get("process_data", {}).get("current_requirement")
    response = llm.invoke(
        f"""
        按照需求说明，帮我做任务拆分，按照开发模块来拆，拆分成大模块嵌套小模块的形式
        当前需求：{current_requirement}
        """
    )
    return {
        "process_data": {
            "task": response.content
        }
    }


# 估算工时
def calc_working_hours(state: AgentState):
    current_task = state["process_data"].get("task")
    response = llm.invoke(
        f"""
        帮我把任务判断一下实现难易程度，分三个等级，easy、medium、difficult
        判断完成后帮我计算总工时，按照下面的计算方式：
        easy      -  2小时
        medium    -  4小时
        difficult -  8小时
        最后给我加总的小时数即可，结果只要返回一个数字
        当前任务拆分：{current_task}
        """
    )
    return {
        "process_data": {
            "working_hours": response.content
        }
    }


# 整理结果
def result_node(state: AgentState):
    requirement = state["process_data"]["current_requirement"]
    task = state["process_data"]["task"]
    working_hours = state["process_data"]["working_hours"]
    return {
        "result": f"{requirement}\n\n{task}\n\n预估总工时：{working_hours}小时"
    }


builder = StateGraph(AgentState)

builder.add_node("judge", judge_requirement_complete_node)
builder.add_node("fill", fill_requirement_node)
builder.add_node("split", split_task_node)
builder.add_node("calc", calc_working_hours)
builder.add_node("result", result_node)

builder.add_edge(START, "judge")
builder.add_conditional_edges(
    "judge",
    route_requirement_node,
    {
        "complete": "split",
        "incomplete": "fill",
    }
)
builder.add_edge("fill", "judge")
builder.add_edge("split", "calc")
builder.add_edge("calc", "result")
builder.add_edge("result", END)

requirement_workflow = builder.compile()
