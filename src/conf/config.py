from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str

    # Вказуємо Pydantic шукати файл .env в корені проєкту
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

try:
    settings = Settings()
except ValidationError as e:
    # Робимо помилку конфігурації явною замість сирого трейсбеку Pydantic
    missing = ", ".join(str(err["loc"][0]) for err in e.errors())
    raise RuntimeError(
        f"Некоректна конфігурація застосунку: відсутні або невалідні змінні ({missing}). "
        "Переконайтеся, що файл .env існує та містить DATABASE_URL, SECRET_KEY і ALGORITHM."
    ) from e
