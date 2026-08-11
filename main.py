from fastapi import FastAPI
from src.api.v1.routes import query
from src.api.v1.routes import upload_routes

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Smart Banking Assistant"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(query.router)
app.include_router(upload_routes.router)
