from fastapi import FastAPI, Request, Depends, HTTPException
from src.app.ingest.script import Ingest, api_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ingest_service = Ingest()
    yield
    app.state.ingest_service.terminate()

app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/ingest")

@app.get("/health")
def health_check():
    return {"status": "healthy"}