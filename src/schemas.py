from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

# --- СХЕМИ ДЛЯ КОРИСТУВАЧІВ ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Пароль має бути не менше 6 символів")

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# --- СХЕМИ ДЛЯ КОНТАКТІВ ---
class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: int
    user_id: int  # Вказуємо, кому належить контакт

    class Config:
        from_attributes = True
