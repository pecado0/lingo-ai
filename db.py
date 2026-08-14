import os
import json
import uuid
import ydb
import ydb.iam
from dotenv import load_dotenv
import datetime

load_dotenv()

def decode_val(val: bytes | str):
    return val.decode('utf-8') if isinstance(val, bytes) else val

def get_ydb_driver():
    """Создаем и возвращаем подключение к YDB"""

    endpoint = os.getenv("YDB_ENDPOINT")
    database = os.getenv("YDB_DATABASE")
    path_to_key = os.getenv("YDB_CERTS_PATH")

    if path_to_key:
        # Локальная разработка
        credentials = ydb.iam.ServiceAccountCredentials.from_file(path_to_key)
    else:
        # Облачная функция
        credentials = ydb.iam.MetadataUrlCredentials()

    driver_config = ydb.DriverConfig(endpoint, database, credentials = credentials)
    
    driver = ydb.Driver(driver_config)
    driver.wait(timeout = 15)
    return driver

# Глобальная инициализация (выполнится один раз при старте контейнера)
DRIVER = get_ydb_driver()
POOL = ydb.SessionPool(DRIVER)

def _execute_query(session, query: str, parameters: dict):
    """Универсальная функция для выполнения запроса в рамках сессии."""

    prepared_query = session.prepare(query)
    return session.transaction(ydb.SerializableReadWrite()).execute(
        prepared_query, 
        parameters, 
        commit_tx = True
    )

def create_user(email: str, password_hash: str, name: str = ""):
    """Создаем нового пользователя в таблице Users"""

    user_id = str(uuid.uuid4())
    
    query = """
    DECLARE $id AS Utf8;
    DECLARE $email AS Utf8;
    DECLARE $password_hash AS Utf8;
    DECLARE $name AS Utf8;
    
    INSERT INTO Users (id, email, pw_hash, name, created_at)
    VALUES ($id, $email, $password_hash, $name, CurrentUtcTimestamp());
    """
    
    parameters = {
        "$id": user_id,
        "$email": email,
        "$password_hash": password_hash,
        "$name": name or ""
    }

    try:
        # Передаем функцию через lambda, чтобы пул мог подставлять туда session
        POOL.retry_operation_sync(
            lambda session: _execute_query(session, query, parameters)
        )
        return user_id
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return None

def check_user(email: str):
    """Ищем пользователя в таблице Users по email"""

    query = """
    DECLARE $email AS Utf8;

    SELECT id, pw_hash FROM `Users` WHERE email = $email;
    """

    parameters = {
        "$email": email
    }

    try: 
        # Используем тот же метод, что и при создании пользователя, для поиска пользователя по email
        result_sets = POOL.retry_operation_sync(
            lambda session: _execute_query(session, query, parameters)
        )

        if not result_sets[0].rows: 
            return None
        
        output = result_sets[0].rows[0]
        
        return {
            "id": decode_val(output['id']),
            "hash_password": decode_val(output['pw_hash'])
        }
    except Exception as e:
        print(f"Ошибка при авторизации: {e}")
        return None


def get_cached_word(word: str):
    """Ищем слово в таблице Words_cache"""

    query = """
    DECLARE $word AS Utf8;

    SELECT
        translation,
        transcription,
        explanation,
        examples

    FROM `Words_cache`
    WHERE word = $word
    """

    parameters = {
        "$word": word
    }

    try:
        result_sets = POOL.retry_operation_sync(
            lambda session: _execute_query(session, query, parameters)
        )

        # Если слово не найдено в словаре
        if not result_sets[0].rows:
            return None

        else:
            output = result_sets[0].rows[0]

            # Переводим examples из str в list, если требуется
            examples = decode_val(output['examples'])
            if isinstance(examples, str):
                try:
                    examples = json.loads(examples)
                except json.JSONDecodeError:
                    examples = []

            elif not isinstance(examples, list):
                examples = []

            return {
                "translation": decode_val(output['translation']),
                "transcription": decode_val(output['transcription']),
                "explanation": decode_val(output['explanation']),
                "examples": examples
            }

    except Exception as e:
        print(f"Ошибка при получении данных о слове: {e}")
        return None

def add_cached_word(word: str, translation: str, transcription: str, explanation: str, examples: list):
    """Добавляем слово в таблицу Words_cache"""

    query = """
    DECLARE $word AS Utf8;
    DECLARE $translation AS Utf8;
    DECLARE $transcription AS Utf8;
    DECLARE $explanation AS Utf8;
    DECLARE $examples AS Json;
    DECLARE $created_at AS Timestamp;

    UPSERT INTO `Words_cache` (word, translation, transcription, explanation, examples, created_at)
    VALUES ($word, $translation, $transcription, $explanation, $examples, CurrentUtcTimestamp());
    """

    parameters = {
        "$word": word,
        "$translation": translation,
        "$transcription": transcription,
        "$explanation": explanation,
        "$examples": json.dumps(examples, ensure_ascii = False),
        "$created_at": datetime.datetime.utcnow()
    }

    try:
        POOL.retry_operation_sync(
            lambda session: _execute_query(session, query, parameters)
        )
        return True
    
    except Exception as e:
        print(f"Ошибка при добавлении слова в кэш: {e}")
        return False


def add_user_word(user_id: str, word: str):
    """Добавляем слово в таблицу User_words"""

    query = """
    DECLARE $user_id AS Utf8;
    DECLARE $word AS Utf8;

    UPSERT INTO `User_words` (user_id, word, last_reviewed, mastery_level)
    VALUES ($user_id, $word, CurrentUtcTimestamp(), 0);
    """

    parameters = {
        "$user_id": user_id,
        "$word": word
    }

    try:
        POOL.retry_operation_sync(
            lambda session: _execute_query(session, query, parameters)
        )
        return True
    
    except Exception as e:
        print(f"Ошибка при добавлении слова пользователю: {e}")
        return False