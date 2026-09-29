from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.connection import get_db


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness():
    """Confirma que o processo HTTP está respondendo."""
    return {"status": "ok"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """Confirma que a API e sua dependência crítica estão prontas."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ready"}
