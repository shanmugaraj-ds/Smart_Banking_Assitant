from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api.v1.routes import query, upload_routes

app = FastAPI()

# Create image directory if it doesn't exist
IMAGE_DIR = Path("data/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Serve extracted images
app.mount(
    "/images",
    StaticFiles(directory=str(IMAGE_DIR)),
    name="images",
)

app.include_router(query.router)
app.include_router(upload_routes.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
