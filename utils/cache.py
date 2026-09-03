import time
import threading
from typing import Any, Optional

class InMemoryTTLCache:
    """
    Cache em memória RAM Thread-Safe com suporte a Time-To-Live (TTL)
    e invalidação granular por chave ou prefixo.
    """
    def __init__(self, default_ttl: int = 180):
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Recupera um valor se ainda não tiver expirado."""
        with self._lock:
            if key not in self._cache:
                return None
            value, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Armazena um valor em memória com tempo de expiração."""
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> bool:
        """Remove uma chave específica do cache."""
        with self._lock:
            return self._cache.pop(key, None) is not None

    def delete_prefix(self, prefix: str) -> int:
        """Invalida todas as chaves que começam com um determinado prefixo."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)

    def clear(self) -> None:
        """Limpa completamente a memória do cache."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Retorna a quantidade de itens no cache (limpando expirados)."""
        with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self._cache.items() if now > exp]
            for k in expired:
                del self._cache[k]
            return len(self._cache)

# Instância global singleton de cache para a API
cache = InMemoryTTLCache(default_ttl=180)
