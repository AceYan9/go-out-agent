# @Time: 2026/10/19 20:29
# @Author: yanggan

from langchain.chat_models import init_chat_model

from app.config import settings

llm = init_chat_model(
    model=settings.OPENAI_MODEL,
    model_provider="openai",
    api_key=settings.OPENAI_KEY,
)
