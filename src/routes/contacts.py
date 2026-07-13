from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, extract
from typing import List, Optional
from datetime import datetime, timedelta

from src.database.db import get_db
from src.database.models import Contact, User
from src.schemas import ContactResponse, ContactCreate, ContactUpdate
from src.services.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["contacts"])

# 1. Створити новий контакт
@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(body: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_contact = Contact(**body.model_dump(), user_id=current_user.id)
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

# 2. Отримати список контактів (з інтегрованим пошуком Query з ДЗ 11)
@router.get("/", response_model=List[ContactResponse])
def read_contacts(
    search: Optional[str] = Query(
        None,
        min_length=1,
        max_length=100,
        description="Пошук за іменем, прізвищем чи email",
    ),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Спочатку беремо контакти ТІЛЬКИ поточного користувача
    query = db.query(Contact).filter(Contact.user_id == current_user.id)
    
    # Якщо передано параметр пошуку — фільтруємо далі
    if search:
        query = query.filter(
            or_(
                Contact.first_name.ilike(f"%{search}%"),
                Contact.last_name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%")
            )
        )
    return query.all()

# 3. Список контактів, у яких день народження в найближчі 7 днів (З ДЗ 11)
@router.get("/birthdays", response_model=List[ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = datetime.now().date()
    upcoming_dates = [today + timedelta(days=i) for i in range(7)]
    
    # Масиви днів та місяців для порівняння без врахування року
    filter_conditions = []
    for d in upcoming_dates:
        filter_conditions.append((extract('month', Contact.birthday) == d.month) & (extract('day', Contact.birthday) == d.day))
        
    contacts = db.query(Contact).filter(
        Contact.user_id == current_user.id, # Тільки свої контакти
        or_(*filter_conditions)
    ).all()
    
    return contacts

# 4. Отримати один контакт за ID
@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено або доступ заборонено")
    return contact

# 5. Оновити існуючий контакт
@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено або доступ заборонено")
    
    for key, value in body.model_dump().items():
        setattr(contact, key, value)
        
    db.commit()
    db.refresh(contact)
    return contact

# 6. Видалити контакт
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не знайдено або доступ заборонено")
    
    db.delete(contact)
    db.commit()
    return None
