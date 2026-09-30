"""Métricas leves e logs estruturados sem dependência externa obrigatória."""

from collections import defaultdict
from threading import Lock
from typing import DefaultDict


_lock = Lock()
_request_count: DefaultDict[tuple[str, str, int], int] = defaultdict(int)
_request_duration: DefaultDict[tuple[str, str], float] = defaultdict(float)


def record_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    key = (method, path, status_code)
    with _lock:
        _request_count[key] += 1
        _request_duration[(method, path)] += duration_seconds


def prometheus_text() -> str:
    lines = [
        "# HELP cine_random_http_requests_total Total de respostas HTTP.",
        "# TYPE cine_random_http_requests_total counter",
    ]
    with _lock:
        counts = sorted(_request_count.items())
        durations = sorted(_request_duration.items())

    for (method, path, status_code), count in counts:
        lines.append(
            f'cine_random_http_requests_total{{method="{_escape(method)}",path="{_escape(path)}",status="{status_code}"}} {count}'
        )
    lines.extend([
        "# HELP cine_random_http_request_duration_seconds_sum Total acumulado da duração das requisições.",
        "# TYPE cine_random_http_request_duration_seconds_sum counter",
    ])
    for (method, path), duration in durations:
        lines.append(
            f'cine_random_http_request_duration_seconds_sum{{method="{_escape(method)}",path="{_escape(path)}"}} {duration:.6f}'
        )
    return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
