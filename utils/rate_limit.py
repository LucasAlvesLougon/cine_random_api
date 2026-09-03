import time
from threading import Lock
from typing import Dict, List, Tuple, Callable
from fastapi import Request, HTTPException, status

class InMemoryRateLimiter:
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._lock = Lock()

    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Verifica se a chave excedeu o limite de requisições na janela de tempo especificada.
        Retorna (is_limited, retry_after_seconds).
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            if key not in self._requests:
                self._requests[key] = []

            # Remove requisições fora da janela
            self._requests[key] = [t for t in self._requests[key] if t > cutoff]

            if len(self._requests[key]) >= limit:
                oldest_in_window = self._requests[key][0]
                retry_after = max(1, int(oldest_in_window + window_seconds - now))
                return True, retry_after

            # Registra a nova requisição
            self._requests[key].append(now)
            return False, 0

    def clear(self):
        """Limpa o registro de requisições (útil para testes)."""
        with self._lock:
            self._requests.clear()

limiter = InMemoryRateLimiter()

def check_upstash_rate_limit(key: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
    """Valida rate limit no Upstash Redis via REST API com fallback in-memory automático."""
    from config import settings
    if not settings.UPSTASH_REDIS_REST_URL or not settings.UPSTASH_REDIS_REST_TOKEN:
        return limiter.is_rate_limited(key, limit, window_seconds)

    try:
        import requests
        url = f"{settings.UPSTASH_REDIS_REST_URL}/pipeline"
        headers = {"Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"}
        redis_key = f"ratelimit:{key}"
        body = [
            ["INCR", redis_key],
            ["EXPIRE", redis_key, window_seconds, "NX"]
        ]
        res = requests.post(url, headers=headers, json=body, timeout=1.5)
        if res.status_code == 200:
            data = res.json()
            count = data[0].get("result", 1)
            if count > limit:
                return True, window_seconds
            return False, 0
    except Exception:
        # Fallback automático e silencioso para in-memory se houver timeout ou indisponibilidade
        pass

    return limiter.is_rate_limited(key, limit, window_seconds)

def get_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente considerando proxies reversos (Render / Vercel / Cloudflare)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def rate_limit(limit: int, window_seconds: int) -> Callable:
    """
    Dependency do FastAPI para limitar requisições por IP e endpoint.
    Exemplo: Depends(rate_limit(limit=5, window_seconds=60))
    """
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        endpoint = request.url.path
        key = f"{client_ip}:{endpoint}"

        is_limited, retry_after = check_upstash_rate_limit(key, limit, window_seconds)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Por favor, aguarde alguns instantes antes de tentar novamente.",
                headers={"Retry-After": str(retry_after)}
            )

    return dependency

