from fastapi import FastAPI

app = FastAPI(title="출근도우미 API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
