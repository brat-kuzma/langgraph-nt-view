"""FastAPI application: LangGraph NT View backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.db.database import init_db
from app.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    # shutdown if needed


app = FastAPI(
    title=settings.app_name,
    description="Backend: LangGraph agent for NT report generation, Grafana/K8s/artifacts",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Отдаём пустой ответ, чтобы браузер не слал 404 в лог."""
    return Response(status_code=204)
