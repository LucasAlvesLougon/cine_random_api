import secrets
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from repositories.user_repository import UserRepository
from schemas.schemas import UserCreate
from utils.security import get_password_hash, verify_password, create_access_token

GOOGLE_CLIENT_ID = "844495701284-qvgpkr9446kr02dki8vs29191t1p33o7.apps.googleusercontent.com"

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def signup(self, user_in: UserCreate):
        """Regra de negócio para criação de conta."""
        existing_user = self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado."
            )

        hashed_password = get_password_hash(user_in.password)
        return self.user_repo.create(email=user_in.email, password_hash=hashed_password)

    def login(self, username: str, password: str) -> dict:
        """Regra de negócio para login com credenciais locais."""
        user = self.user_repo.get_by_email(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}

    def login_with_google(self, id_token_str: str) -> dict:
        """Regra de negócio para autenticação com Google Identity."""
        try:
            id_info = id_token.verify_oauth2_token(id_token_str, requests.Request(), GOOGLE_CLIENT_ID)
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

        user = self.user_repo.get_by_email(email)
        if not user:
            random_password = secrets.token_urlsafe(32)
            hashed_password = get_password_hash(random_password)
            user = self.user_repo.create(email=email, password_hash=hashed_password)

        access_token = create_access_token(data={"sub": user.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email
        }
