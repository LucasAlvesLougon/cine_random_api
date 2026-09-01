from fastapi import FastAPI

app = FastAPI(
    title="Cine Random API",
    description="Backend para o Sorteador de Filmes",
    version="1.0.0"
)

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Pong! Servidor FastAPI rodando com sucesso."}