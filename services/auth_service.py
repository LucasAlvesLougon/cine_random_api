import re
import secrets
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.exceptions import TransportError
from sqlalchemy.orm import Session

from config import settings
from repositories.user_repository import UserRepository
from schemas.schemas import UserCreate, GoogleAuthRequest, DemoAuthRequest
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

    def login_with_google(self, req: GoogleAuthRequest) -> dict:
        """Autentica usando apenas um ID token assinado e validado pelo Google."""
        try:
            claims = id_token.verify_oauth2_token(
                req.credential,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credencial do Google inválida ou expirada.",
            ) from exc
        except TransportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível validar a credencial do Google agora.",
            ) from exc

        email = claims.get("email")
        google_sub = claims.get("sub")
        if not google_sub or not email or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A credencial do Google não contém uma identidade válida.",
            )
        if claims.get("email_verified") is not True:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="O Google não confirmou este endereço de email.",
            )

        normalized_email = email.strip().lower()
        user = self.user_repo.get_by_google_sub(google_sub)
        if not user:
            existing_user = self.user_repo.get_by_email(normalized_email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Entre com sua senha para vincular esta conta ao Google.",
                )

            random_password = secrets.token_urlsafe(32)
            hashed_password = get_password_hash(random_password)
            user = self.user_repo.create(
                email=normalized_email,
                password_hash=hashed_password,
                google_sub=google_sub,
            )

        access_token = create_access_token(data={"sub": user.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user.email,
            "user_id": user.id
        }

    def login_demo(self, req: DemoAuthRequest) -> dict:
        """Cria uma sessão descartável somente em ambientes não produtivos."""
        normalized_email = req.email.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Informe um email válido para a demonstração.",
            )

        user = self.user_repo.get_by_email(normalized_email)
        if not user:
            user = self.user_repo.create(
                email=normalized_email,
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
            )

        return {
            "access_token": create_access_token(data={"sub": user.email}),
            "token_type": "bearer",
            "email": user.email,
            "user_id": user.id,
        }
