import os
import threading
import traceback

import uvicorn
from fastapi import FastAPI
import gradio as gr

from src.api.setup_api import logger
from src.utils.app_state import app_state
from src.interfaces.interface import build_interface
from src.api.endpoints import APIEndpoints  # assumes this defines your API routes

# -----------------------------
# Helpers
# -----------------------------

def background_initialize():
    """Initialize heavy stuff without blocking the web server port."""
    try:
        logger.info("Initializing app_state in background…")
        ok = app_state.initialize()
        if ok:
            logger.info("Initialization complete.")
        else:
            logger.error("Initialization failed (initialize() returned False).")
    except Exception:
        logger.error("Initialization crashed:\n%s", traceback.format_exc())

def create_fastapi_app() -> FastAPI:
    """
    Create a single FastAPI app, register the API endpoints on it,
    and mount the Gradio UI at '/'.
    """
    # Build API endpoints (expects APIEndpoints to expose either .app or .router)
    api = APIEndpoints(
        qa_chain=app_state.qa_chain,
        cache_manager=app_state.cache_manager,
        security_manager=app_state.security_manager,
    )

    # Prefer an internal FastAPI app if APIEndpoints defines one; otherwise make our own
    if hasattr(api, "app"):
        app = api.app
    else:
        app = FastAPI()
        # If APIEndpoints exposes a router, include it
        if hasattr(api, "router"):
            app.include_router(api.router, prefix="/api")
        # Or, if it exposes a register() method, let it attach routes
        elif hasattr(api, "register"):
            api.register(app, prefix="/api")
        else:
            # Fallback: nothing to register; your API will just be the Gradio UI
            logger.warning("APIEndpoints did not expose app/router/register; only UI will be served.")

    # Always include a health endpoint so Render can verify the port quickly
    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # Build and mount the Gradio UI at root
    iface = build_interface()
    gr.mount_gradio_app(app, iface, path="/")

    return app

# -----------------------------
# Entrypoint
# -----------------------------

if __name__ == "__main__":
    logger.info("Starting Document Q&A Assistant (Render)")

    # Start heavy init in the background so we bind to PORT immediately
    threading.Thread(target=background_initialize, daemon=True).start()

    # Single app, single port
    app = create_fastapi_app()
    port = int(os.environ.get("PORT", "7860"))  # Render injects PORT; don't override it in dashboard
    logger.info("Binding server on 0.0.0.0:%s", port)

    # Run uvicorn (this is the only server; no extra thread on :5000)
    uvicorn.run(app, host="0.0.0.0", port=port)
