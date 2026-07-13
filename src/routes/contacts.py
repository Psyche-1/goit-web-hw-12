from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.db import get_db
from src.database.models import Contact, User
from src.schemas import ContactResponse, ContactCreate, ContactUpdate
from src.services.auth import get_current_user
from src.repository import contacts as repository_contacts

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_owned_contact_or_404(contact_id: int, db: Session, current_user: User) -> Contact:
    contact = repository_contacts.get_contact(db, contact_id, current_user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Контакт не знайдено або доступ заборонено",
        )
    return contact

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
    search: Optional[str] = Query(None, description="Пошук за іменем, прізвищем чи email"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return repository_contacts.search_contacts(db, current_user, search)

# 3. Список контактів, у яких день народження в найближчі 7 днів (З ДЗ 11)
@router.get("/birthdays", response_model=List[ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return repository_contacts.get_upcoming_birthdays(db, current_user)

# 4. Отримати один контакт за ID
@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_owned_contact_or_404(contact_id, db, current_user)

# 5. Оновити існуючий контакт
@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, body: ContactUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = get_owned_contact_or_404(contact_id, db, current_user)

    for key, value in body.model_dump().items():
        setattr(contact, key, value)
        
    db.commit()
    db.refresh(contact)
    return contact

# 6. Видалити контакт
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = get_owned_contact_or_404(contact_id, db, current_user)

    db.delete(contact)
    db.commit()
    return None
