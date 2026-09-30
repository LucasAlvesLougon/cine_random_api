from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from utils.observability import prometheus_text


router = APIRouter(tags=["observability"])


@router.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
def metrics():
    """Expõe métricas Prometheus básicas para monitoramento externo."""
    return PlainTextResponse(prometheus_text(), media_type="text/plain; version=0.0.4")
