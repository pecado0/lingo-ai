import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

# Секретный ключ для подписи токенов. 
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-local-key-for-lingo-app")
JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Превращает обычный пароль в хэш для БД"""
    # bcrypt работает только с байтами, кодируем строку
    password_bytes = password.encode('utf-8')
    
    # gensalt() добавляет случайные символы к паролю перед хэшированием.
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # Возвращаем строку для записи в YDB
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли введенный пароль хэшу из базы"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # checkpw достает соль из хэша и проверяет совпадение
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def generate_token(user_id: str) -> str:
    """Создает JWT-токен, действующий 7 дней"""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7), # Годен до
        "iat": datetime.now(timezone.utc)                      # Выдан в
    }
    
    # Генерируем строку токена на основе наших данных и секретного ключа
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token
