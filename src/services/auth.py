from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
# Імпортуємо налаштування з нового конфігу
from src.conf.config import settings
import bcrypt

# Використовуємо змінні з .env файлу
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class HashService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # Перетворюємо рядки в байти, оскільки bcrypt працює з байтами
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except ValueError:
            # Некоректний/пошкоджений хеш у БД — вважаємо пароль невірним,
            # а не піднімаємо 500 через внутрішню помилку bcrypt
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        # Хешуємо пароль за допомогою чистого bcrypt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

class TokenService:
    @staticmethod
    def create_token(data: dict, expires_delta: Optional[timedelta] = None, is_refresh: bool = False) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + (timedelta(days=7) if is_refresh else timedelta(minutes=15))
        
        to_encode.update({"exp": expire, "scope": "refresh_token" if is_refresh else "access_token"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося валідувати токен доступу",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        scope: str = payload.get("scope")
        if email is None or scope != "access_token":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
