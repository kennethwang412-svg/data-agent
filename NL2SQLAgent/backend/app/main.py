from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.sessions import router as sessions_router
from app.api.database import router as database_router
from app.api.chat import router as chat_router

app.include_router(sessions_router)
app.include_router(database_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}
