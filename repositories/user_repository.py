from typing import Optional
from sqlalchemy.orm import Session
from models.models import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        """Busca um usuário pelo email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca um usuário pelo id."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, email: str, password_hash: str) -> User:
        """Cria e persiste um novo usuário."""
        new_user = User(email=email, password_hash=password_hash)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user
