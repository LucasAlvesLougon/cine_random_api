"""Tickets curtos e opacos para autenticar conexões WebSocket."""

from dataclasses import dataclass
from threading import Lock
from time import monotonic
import secrets


@dataclass(frozen=True)
class WebSocketTicket:
    user_id: int
    list_code: str
    expires_at: float


class WebSocketTicketStore:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._tickets: dict[str, WebSocketTicket] = {}
        self._lock = Lock()

    def issue(self, user_id: int, list_code: str) -> tuple[str, int]:
        ticket = secrets.token_urlsafe(32)
        with self._lock:
            self._purge_expired()
            self._tickets[ticket] = WebSocketTicket(
                user_id=user_id,
                list_code=list_code,
                expires_at=monotonic() + self.ttl_seconds,
            )
        return ticket, self.ttl_seconds

    def consume(self, ticket: str, list_code: str) -> int | None:
        with self._lock:
            self._purge_expired()
            entry = self._tickets.pop(ticket, None)
            if entry is None or entry.list_code != list_code:
                return None
            return entry.user_id

    def _purge_expired(self) -> None:
        now = monotonic()
        expired = [key for key, value in self._tickets.items() if value.expires_at <= now]
        for key in expired:
            self._tickets.pop(key, None)


websocket_tickets = WebSocketTicketStore()
