from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import auth, health, movies

app = FastAPI(
    title="Cine Random API",
    description="Backend para o Sorteador de Filmes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        "img-src 'self' data: blob: https://image.tmdb.org https://*.tmdb.org; "
        "font-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/client; "
        "connect-src 'self' https://api.themoviedb.org https://accounts.google.com "
        "https://oauth2.googleapis.com wss: ws:; frame-src https://accounts.google.com; "
        "manifest-src 'self'; worker-src 'self' blob:; form-action 'self'"
    )
    if settings.ENVIRONMENT.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(movies.router)

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Pong! Servidor FastAPI rodando com sucesso."}
