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

        is_limited, retry_after = limiter.is_rate_limited(key, limit, window_seconds)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Por favor, aguarde alguns instantes antes de tentar novamente.",
                headers={"Retry-After": str(retry_after)}
            )

    return dependency
