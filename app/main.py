from fastapi import FastAPI
from app.salas import router

app = FastAPI(title="API de Salas de Cine", version="1.0.0")
app.include_router(router)


@app.get("/")
def raiz() -> dict:
    return {"api": "salas-cine", "docs": "/docs"}