import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from qr_api.resources.endpoints import router
from qr_api.resources.security import router as security_router
import uvicorn
import logging


#----------------------------------------------------------------
# configure logging to track requests and errors
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("qr_api").setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
#----------------------------------------------------------------


app = FastAPI(
    title="Query Recommender API",
    description="API for the Query Recommender",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/swagger",
    redoc_url="/api/v1/redoc",
    root_path=os.getenv("ROOT_PATH", ""),
)

app.include_router(router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")


# Root
@app.get("/", include_in_schema=False)
async def home():
    """Root endpoint to redirect to the API home"""
    return RedirectResponse(url="/api/v1")


# API
@app.get("/api/v1")
async def api_home():
    """API root endpoint showing available endpoints"""
    return {
        "message": "API V1 is running",
        "endpoints": {
            "recommend-next-queries": {
                "description": "Get the next queries given the previous one",
                "methods": ["POST"],
                "url": "/api/v1/recommend-next-queries",
                "example_url": "/api/v1/recommend-next-queries",
            },
            "authtest": {
                "description": "Test endpoint requiring a valid bearer token",
                "methods": ["POST"],
                "url": "/api/v1/authtest",
            },
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
