from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.conf.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

# Додаємо аргументи підключення спеціально для SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

# Створюємо рушій
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# Створюємо фабрику сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Залежність для отримання сесії БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
