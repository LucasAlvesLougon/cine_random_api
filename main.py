from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from time import perf_counter
from uuid import uuid4
import json
import logging
from config import settings
from routers import auth, health, metrics, movies, tmdb
from utils.observability import record_request


logger = logging.getLogger("cine_random.access")

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
    expose_headers=["X-Request-ID"],
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
        "connect-src 'self' https://accounts.google.com "
        "https://oauth2.googleapis.com wss: ws:; frame-src https://accounts.google.com; "
        "manifest-src 'self'; worker-src 'self' blob:; form-action 'self'"
    )
    if settings.ENVIRONMENT.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started = perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration = perf_counter() - started
        status_code = response.status_code if response is not None else 500
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        record_request(request.method, path, status_code, duration)
        logger.info(json.dumps({
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": path,
            "status": status_code,
            "duration_ms": round(duration * 1000, 2),
        }, ensure_ascii=False))
        if response is not None:
            response.headers["X-Request-ID"] = request_id

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(movies.router)
app.include_router(tmdb.router)

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Pong! Servidor FastAPI rodando com sucesso."}
