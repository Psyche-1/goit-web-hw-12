from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import extract, or_
from sqlalchemy.orm import Query, Session

from src.database.models import Contact, User


def owned_contacts_query(db: Session, user: User) -> Query:
    """Базовий запит, що обмежує вибірку контактами конкретного користувача."""
    return db.query(Contact).filter(Contact.user_id == user.id)


def get_contact(db: Session, contact_id: int, user: User) -> Optional[Contact]:
    """Повертає контакт користувача за ID або None, якщо його не знайдено."""
    return owned_contacts_query(db, user).filter(Contact.id == contact_id).first()


def search_contacts(db: Session, user: User, search: Optional[str]) -> List[Contact]:
    """Повертає контакти користувача з опціональним пошуком за ім'ям/прізвищем/email."""
    query = owned_contacts_query(db, user)
    if search:
        query = query.filter(
            or_(
                Contact.first_name.ilike(f"%{search}%"),
                Contact.last_name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%"),
            )
        )
    return query.all()


def get_upcoming_birthdays(db: Session, user: User, days: int = 7) -> List[Contact]:
    """Повертає контакти користувача з днями народження у найближчі `days` днів."""
    today = datetime.now().date()
    upcoming_dates = [today + timedelta(days=i) for i in range(days)]
    filter_conditions = [
        (extract("month", Contact.birthday) == d.month)
        & (extract("day", Contact.birthday) == d.day)
        for d in upcoming_dates
    ]
    return owned_contacts_query(db, user).filter(or_(*filter_conditions)).all()
