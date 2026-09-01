import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from config import settings

def get_password_hash(password: str) -> str:
    """Criptografa a senha gerando um Salt aleatório."""
    # O bcrypt exige que a senha seja convertida para bytes
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Retornamos como string normal para salvar no banco
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano bate com o hash salvo."""
    # Ambos precisam estar em bytes para a comparação
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict):
    """Gera o Token JWT para o usuário navegar logado."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt