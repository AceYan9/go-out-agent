# @Time: 2026/10/19 15:53
# @Author: yanggan

from fastapi import APIRouter

from app.api.routes import agent_routes

version1_prefix = "/v1"


api_router = APIRouter(prefix=version1_prefix)
api_router.include_router(agent_routes.router, prefix="/agent", tags=["agent"])
