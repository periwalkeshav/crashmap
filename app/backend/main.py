from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from routers.analytics import router as analytics_router
from services.data_loader import initialize_all_data, is_data_loaded, get_loading_error


def create_app() -> FastAPI:
    """
    Application factory so we can import `app` in tests without side effects.
    """
    app = FastAPI(title="US Accident Analytics API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analytics_router)

    @app.on_event("startup")
    async def load_data_on_startup():
        """
        Load all datasets when the server starts.
        This ensures all data is ready before accepting requests.
        """
        try:
            initialize_all_data()
        except Exception as e:
            print(f"CRITICAL: Failed to load datasets: {e}")
            print("Server will start but endpoints may fail until data is loaded.")

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        """Basic health check endpoint."""
        return {"status": "ok"}

    @app.get("/status", tags=["system"])
    async def get_status() -> dict[str, str | bool]:
        """
        Check if all datasets are loaded and ready.
        
        Returns:
            dict with 'ready' (bool) and optional 'error' (str) fields
        """
        if is_data_loaded():
            return {"ready": True}
        else:
            error = get_loading_error()
            return {
                "ready": False,
                "error": error if error else "Data is still loading..."
            }

    return app


app = create_app()