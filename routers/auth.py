from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from database.connection import get_db
from models.models import User
from schemas.schemas import UserCreate, UserResponse
from utils.security import get_password_hash, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Cria um novo usuário no banco de dados."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado.")

    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Autentica o usuário e retorna um token JWT."""
    user = db.query(User).filter(User.email == form_data.username).first()

    # 2. Verifica se o usuário existe e se a senha bate com o Hash
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Gera a "chave eletrônica" JWT
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}

from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

class GoogleAuthRequest(BaseModel):
    idToken: str

# Estamos validando a assinatura diretamente com o Google Cloud Identity
@router.post("/google")
def login_with_google(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Rota para processar o login via Google Oficial."""
    try:
        # Valida o token com a chave pública do Google
        id_info = id_token.verify_oauth2_token(req.idToken, requests.Request())
        email = id_info.get("email")
    except ValueError:
        raise HTTPException(status_code=401, detail="Token do Google Inválido ou Expirado")
        
    if not email:
        raise HTTPException(status_code=400, detail="Conta do Google não tem email vinculado")

    # Verifica se esse email do Google já existe no nosso banco Postgres
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Se for o primeiro acesso, cria um usuário fantasma com senha hiper-segura aleatória
        import secrets
        hashed_password = get_password_hash(secrets.token_urlsafe(32))
        user = User(email=email, password_hash=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Devolve o nosso Token JWT (Para a nossa API)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "email": user.email}
