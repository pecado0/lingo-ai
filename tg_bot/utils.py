import backend.ai as ai
import backend.db as db

from aiogram.types import Message

import re

# Для проверки корректности формата сообщения
pattern = {
"email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
"password": r"^[A-Za-z\d@$!%*#?&_\-]{8,}$",
"clean_text": r"^[\w\s\.,!\?\-'\"—–\(\)]+$"
}

def get_item(message: Message, entity: str):
    if not message.text:
        return None
    
    item_to_pass = None
    entities = message.entities or []

    for item in entities:
        if item.type == entity:
            # Извлекаем нужный item
            item_to_pass = item.extract_from(message.text)
            break

    if not item_to_pass:
        item_to_pass = message.text

    if not re.match(pattern = pattern.get(entity), string = item_to_pass):
        return None

    return item_to_pass

def handle_translate(body: dict):
    
    # Получаем данные из запроса
    user_id = body.get('user_id')
    word = body.get('word')
    context = body.get('context')

    if not word:
        raise ValueError("Слово для перевода не найдено в данных.")

    if not context:
        # Ищем слово в кэше
        cached_word = db.get_cached_word(word = word)
        # Отработка, если слово найдено в кэше
        if cached_word:
            db.add_user_word(user_id = user_id, word = word)
            return cached_word        
        # Если слово не найдено в кэше, обращаемся к LLM
        if cached_word == None:
            llm_response = ai.get_llm_response(text = word, context = context)
            if not llm_response:
                raise Exception("Ошибка при обращении к LLM.")

            # Добавляем слово в кэш
            db.add_cached_word(
                    word = word,
                    translation = llm_response.get("translation", ""),
                    transcription = llm_response.get("transcription", ""),
                    explanation = llm_response.get("explanation", ""),
                    examples = llm_response.get("examples", [])
                    )

            # Добавляем слово в словарь пользователя
            db.add_user_word(user_id = user_id, word = word)

            return llm_response

    if context:
        if not llm_response:
            raise Exception("Ошибка при обращении к LLM.")

        db.add_user_word(user_id = user_id, word = word)
        
        return llm_response