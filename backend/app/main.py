from fastapi import FastAPI

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.search import router as search_router

app = FastAPI(title="출근도우미 API")
app.include_router(profiles_router)
app.include_router(dashboard_router)
app.include_router(search_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
