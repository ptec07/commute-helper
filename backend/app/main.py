from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # noqa: F401
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.search import router as search_router
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


Base.metadata.create_all(bind=engine)
app = FastAPI(title="출근도우미 API", lifespan=lifespan)
app.include_router(profiles_router)
app.include_router(dashboard_router)
app.include_router(search_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
