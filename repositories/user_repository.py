from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from models.models import User, PasswordResetToken

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        """Busca um usuário pelo email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca um usuário pelo id."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_google_sub(self, google_sub: str) -> Optional[User]:
        """Busca um usuário pelo identificador estável fornecido pelo Google."""
        return self.db.query(User).filter(User.google_sub == google_sub).first()

    def create(self, email: str, password_hash: str, google_sub: str | None = None) -> User:
        """Cria e persiste um novo usuário."""
        new_user = User(
            email=email,
            password_hash=password_hash,
            google_sub=google_sub,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def link_google_sub(self, user: User, google_sub: str) -> User:
        """Vincula um identificador Google a um usuário já autenticado."""
        user.google_sub = google_sub
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_password_reset_token(self, user: User, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": datetime.now(timezone.utc)}, synchronize_session=False)
        token = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_valid_password_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        ).first()

    def consume_password_reset_token(self, token: PasswordResetToken, password_hash: str) -> None:
        token.user.password_hash = password_hash
        token.used_at = datetime.now(timezone.utc)
        self.db.commit()
