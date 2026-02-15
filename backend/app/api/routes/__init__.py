from fastapi import APIRouter

from app.api.routes import projects, tests, artifacts, reports, collect

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tests.router, prefix="/tests", tags=["tests"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(collect.router, prefix="/collect", tags=["collect"])
