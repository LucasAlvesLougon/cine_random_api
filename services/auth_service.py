import base64
import json
import re
import secrets
from typing import Union
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from config import settings
from repositories.user_repository import UserRepository
from schemas.schemas import UserCreate, GoogleAuthRequest
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

    def login_with_google(self, req: Union[GoogleAuthRequest, str]) -> dict:
        """Regra de negócio para autenticação com Google Identity (suporta idToken, credential ou dados de perfil)."""
        if isinstance(req, str):
            token_str = req
            email = None
            name = None
            google_id = None
        else:
            token_str = req.idToken or req.credential or req.token
            email = req.email
            name = req.name
            google_id = req.google_id

        if token_str:
            parts = token_str.split(".")
            if len(parts) >= 2:
                try:
                    padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                    payload_json = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
                    payload = json.loads(payload_json)
                    if isinstance(payload, dict):
                        email = payload.get("email") or email
                        name = payload.get("name") or payload.get("given_name") or name
                        google_id = payload.get("sub") or google_id
                except Exception:
                    pass

        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise HTTPException(
                status_code=422,
                detail="O token do Google não contém um e-mail válido ou não foi fornecido."
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
