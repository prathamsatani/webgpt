from fastapi import FastAPI, Request, Depends, HTTPException
from src.app.ingest import Ingest, api_router as ingest_api_router
from src.app.retrieve import Retrieve, api_router as retrieve_api_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ingest_service = Ingest()
    app.state.retrieve_service = Retrieve()
    yield
    await app.state.ingest_service.terminate()
    await app.state.retrieve_service.terminate()
    
app = FastAPI(lifespan=lifespan)
app.include_router(ingest_api_router, prefix="/ingest")
app.include_router(retrieve_api_router, prefix="/retrieve")

@app.get("/health")
def health_check():
    return {"status": "healthy"}