from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.connection import get_db
from config import settings
from schemas.schemas import (
    UserCreate,
    UserResponse,
    TokenResponse,
    GoogleAuthRequest,
    GoogleLinkConfirmationRequest,
    GoogleLinkResponse,
    DemoAuthRequest,
    PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse,
)
from services.auth_service import AuthService
from utils.rate_limit import rate_limit
from utils.security import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit(limit=5, window_seconds=60))])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Cria um novo usuário através da camada de serviço."""
    auth_service = AuthService(db)
    return auth_service.signup(user)

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit(limit=10, window_seconds=60))])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Autentica o usuário e retorna um token JWT."""
    auth_service = AuthService(db)
    return auth_service.login(username=form_data.username, password=form_data.password)

@router.post(
    "/password-reset/request",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
def request_password_reset(req: PasswordResetRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.request_password_reset(req.email)

@router.post(
    "/password-reset/confirm",
    response_model=PasswordResetResponse,
    dependencies=[Depends(rate_limit(limit=5, window_seconds=60))],
)
def confirm_password_reset(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.reset_password(req.token, req.new_password)

@router.post("/google", response_model=TokenResponse, dependencies=[Depends(rate_limit(limit=10, window_seconds=60))])
def login_with_google(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Processa autenticação com Google Identity através do AuthService."""
    auth_service = AuthService(db)
    return auth_service.login_with_google(req)

@router.post(
    "/google/confirm-link",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
)
def confirm_google_link(req: GoogleLinkConfirmationRequest, db: Session = Depends(get_db)):
    """Confirma a senha local, vincula o Google e cria a sessão."""
    auth_service = AuthService(db)
    return auth_service.confirm_google_link(req)

@router.post(
    "/google/link",
    response_model=GoogleLinkResponse,
    dependencies=[Depends(rate_limit(limit=10, window_seconds=60))],
)
def link_google_account(
    req: GoogleAuthRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Vincula uma conta Google à conta local autenticada."""
    auth_service = AuthService(db)
    return auth_service.link_google_account(req, current_user)

@router.post("/demo", response_model=TokenResponse, dependencies=[Depends(rate_limit(limit=10, window_seconds=60))])
def login_demo(req: DemoAuthRequest, db: Session = Depends(get_db)):
    """Disponibiliza login simulado apenas quando habilitado fora de produção."""
    if settings.ENVIRONMENT.lower() == "production" or not settings.ALLOW_DEMO_AUTH:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rota não encontrada.")

    auth_service = AuthService(db)
    return auth_service.login_demo(req)

