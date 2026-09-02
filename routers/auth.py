from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.schemas import UserCreate, UserResponse, TokenResponse, GoogleAuthRequest
from services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Cria um novo usuário através da camada de serviço."""
    auth_service = AuthService(db)
    return auth_service.signup(user)

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Autentica o usuário e retorna um token JWT."""
    auth_service = AuthService(db)
    return auth_service.login(username=form_data.username, password=form_data.password)

@router.post("/google", response_model=TokenResponse)
def login_with_google(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Processa autenticação com Google Identity através do AuthService."""
    auth_service = AuthService(db)
    return auth_service.login_with_google(req.idToken)

