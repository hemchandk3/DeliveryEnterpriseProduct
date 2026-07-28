from fastapi import FastAPI

from app.api.ingest import router as ingest_router

app = FastAPI(title="Delivery Enterprise Platform")
app.include_router(ingest_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
