from fastapi import FastAPI
from src.routes import contacts, auth
from src.database.models import Base
from src.database.db import engine

app = FastAPI(title="Contacts REST API with JWT")

# Виправлений метод створення таблиць у базі даних
Base.metadata.create_all(bind=engine)

# Підключаємо роутери аутентифікації та контактів
app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Welcome to Contacts REST API. Operational with JWT Auth!"}
