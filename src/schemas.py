from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import date
from typing import Optional

# --- СХЕМИ ДЛЯ КОРИСТУВАЧІВ ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Пароль має бути не менше 8 символів")

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Пароль не може перевищувати 72 байти")
        return password

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# --- СХЕМИ ДЛЯ КОНТАКТІВ ---
class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone_number: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[0-9+() .-]+$",
    )
    birthday: date
    additional_data: Optional[str] = Field(default=None, max_length=1000)

    model_config = ConfigDict(str_strip_whitespace=True)

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: int
    user_id: int  # Вказуємо, кому належить контакт

    model_config = ConfigDict(from_attributes=True)
