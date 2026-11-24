"""
VisionTutor AI backend entrypoint.

Wires together config, CORS, rate limiting, the RAG index (built once at
startup), the optional history store, and the API routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.db import HistoryStore
from app.routes import analyze, health, history
from app.services.rag_service import RAGService

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the RAG index once (not per-request) and open the (optional) DB.
    app.state.rag_service = RAGService(settings)
    app.state.history_store = HistoryStore(settings)
    yield


app = FastAPI(
    title="VisionTutor AI",
    description="Multimodal AI Image Explainer and ML Concept Tutor",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internals (stack traces, API keys, etc.) to the client.
    return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error."})


app.include_router(health.router, tags=["health"])
app.include_router(analyze.router, tags=["analyze"])
app.include_router(history.router, tags=["history"])
