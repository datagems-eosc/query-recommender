import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, APIRouter
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

dataset_router = APIRouter()
app.include_router(dataset_router, prefix="/api/v1")


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
            "next_query": {
                "description": "Get the next query given the previous one",
                "methods": ["GET"],
                "url": "/api/v1/next_query",
                "example_url": "/api/v1/next_query/previous_query",
            },
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
