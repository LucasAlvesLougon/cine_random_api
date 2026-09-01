from fastapi import FastAPI
from database.connection import engine, Base
from routers import auth
import models.models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cine Random API",
    description="Backend para o Sorteador de Filmes",
    version="1.0.0"
)

app.include_router(auth.router)

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Pong! Servidor FastAPI rodando com sucesso."}
