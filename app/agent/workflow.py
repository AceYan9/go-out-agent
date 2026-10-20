# @Time: 2026/10/19 16:10
# @Author: yanggan

from typing import TypedDict, NotRequired, Any

from langgraph.graph import StateGraph, START, END

from app.agent.tools.location import get_location
from app.agent.tools.weather import get_weather
from app.llm import llm

from app.agent.workflows import weather_workflow


class WeatherState(TypedDict):
    user_input: str
    city: str
    latitude: NotRequired[float]
    longitude: NotRequired[float]
    temperature: NotRequired[float]
    humidity: NotRequired[float]
    error: NotRequired[str]
    result: NotRequired[dict[str, Any]]


def extract_city_node(state: WeatherState):
    response = llm.invoke(
        f"从以下文本中提取城市名称，只返回城市名：{state['user_input']}"
    )

    return {"city": response.content.strip()}


def coordinates_node(state: WeatherState) -> dict:
    try:
        longitude, latitude = get_location.invoke({"city": state["city"]})
        if not latitude or not longitude:
            return {"error": "未能获取有效的城市经纬度"}

        return {
            "latitude": latitude,
            "longitude": longitude,
        }
    except Exception as e:
        return {"error": f"获取经纬度失败：{str(e)}"}


def check_coordinates(state: WeatherState) -> str:
    if state.get("error"):
        return "end"

    return "weather"


def weather_node(state: WeatherState) -> dict:
    try:
        data = get_weather.invoke({
            "latitude": state["latitude"],
            "longitude": state["longitude"],
        })

        temperature = data.get("temperature")
        humidity = data.get("humidity")

        if temperature is None or humidity is None:
            return {"error": "天气接口未返回有效的温度或湿度"}

        return {
            "temperature": temperature,
            "humidity": humidity,
        }

    except Exception as exc:
        return {"error": f"获取天气失败：{exc}"}


def result_node(state: WeatherState) -> dict:
    return {
        "result": {
            "city": state["city"],
            "temperature": state["temperature"],
            "humidity": state["humidity"],
        }
    }


builder = StateGraph(WeatherState)

builder.add_node("weather", weather_workflow)

builder.add_edge(START, "weather")

builder.add_edge("weather", END)

# 编译
workflow = builder.compile()
