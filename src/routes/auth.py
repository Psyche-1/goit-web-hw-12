from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from src.database.db import get_db
from src.database.models import User
from src.schemas import UserCreate, UserResponse, Token
from src.services.auth import HashService, TokenService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db: Session = Depends(get_db)):
    # Перевірка чи пошта вже зайнята
    exist_user = db.query(User).filter(User.email == body.email).first()
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Користувач з таким Email вже існує")
    
    # Хешуємо пароль та зберігаємо користувача
    hashed_password = HashService.get_password_hash(body.password)
    new_user = User(email=body.email, password=hashed_password)
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        # Захист від гонки: пошту могли зайняти між перевіркою та commit
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Користувач з таким Email вже існує")
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.username).first()
    if user is None or not HashService.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невірна пошта або пароль")
    
    # Створення пари токенів
    access_token = TokenService.create_token(data={"sub": user.email}, expires_delta=timedelta(minutes=30))
    refresh_token = TokenService.create_token(data={"sub": user.email}, expires_delta=timedelta(days=7), is_refresh=True)
    
    # Записуємо refresh_token користувачу в базу
    user.refresh_token = refresh_token
    db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
