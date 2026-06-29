from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.init_db import init_db
import logging
import threading

logger = logging.getLogger(__name__)


def _warmup_ollama() -> None:
    """Pre-load the Ollama model into memory on startup.
    
    Sending a tiny prompt with keep_alive forces the model to load so the first
    user request doesn't cold-start (which can OOM-kill on low-RAM machines).
    Runs in a background thread — does NOT block app startup.
    """
    import time
    import httpx
    time.sleep(5)  # Let Ollama finish initialising
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": "hi",
                    "stream": False,
                    "keep_alive": "10m",
                },
            )
            if resp.status_code == 200:
                logger.info("ollama_warmup_ok", extra={"model": settings.ollama_model})
            else:
                logger.warning("ollama_warmup_failed", extra={"status": resp.status_code})
    except Exception as exc:
        logger.warning("ollama_warmup_error", extra={"error": str(exc)})


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def initialize_database() -> None:
        if settings.auto_create_tables:
            init_db()

    @app.on_event("startup")
    def warmup_llm() -> None:
        """Start Ollama warmup in background so startup is non-blocking."""
        threading.Thread(target=_warmup_ollama, daemon=True).start()

    return app


app = create_app()
