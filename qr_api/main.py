import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from qr_api.resources.endpoints import router
import uvicorn

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
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
