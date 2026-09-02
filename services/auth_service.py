import secrets
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from config import settings
from repositories.user_repository import UserRepository
from schemas.schemas import UserCreate
from utils.security import get_password_hash, verify_password, create_access_token

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def signup(self, user_in: UserCreate):
        """Regra de negócio para criação de conta."""
        normalized_email = user_in.email.strip().lower()
        existing_user = self.user_repo.get_by_email(normalized_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado."
            )

        hashed_password = get_password_hash(user_in.password)
        return self.user_repo.create(email=normalized_email, password_hash=hashed_password)

    def login(self, username: str, password: str) -> dict:
        """Regra de negócio para login com credenciais locais."""
        normalized_username = username.strip().lower()
        user = self.user_repo.get_by_email(normalized_username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email,
            "user_id": user.id
        }

    def login_with_google(self, id_token_str: str) -> dict:
        """Regra de negócio para autenticação com Google Identity."""
        try:
            id_info = id_token.verify_oauth2_token(id_token_str, requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = id_info.get("email")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token do Google Inválido: {str(e)}"
            )

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conta do Google não tem email vinculado"
            )

        normalized_email = email.strip().lower()
        user = self.user_repo.get_by_email(normalized_email)
        if not user:
            random_password = secrets.token_urlsafe(32)
            hashed_password = get_password_hash(random_password)
            user = self.user_repo.create(email=normalized_email, password_hash=hashed_password)

        access_token = create_access_token(data={"sub": user.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email,
            "user_id": user.id
        }
