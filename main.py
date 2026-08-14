import auth
import db
import ai

import os
import json
from dotenv import load_dotenv

# Загружаем переменные из .env файла (только для локальной работы)
load_dotenv()

# Читаем доступы к БД
YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")
YDB_CERTS_PATH = os.getenv("YDB_CERTS_PATH")

def handle_translate(body: dict):
    # Получаем данные из запроса
    user_id = body.get('user_id')
    text = body.get('text')
    context = body.get('context')

    if not context:
        # Ищем слово в кэше
        cached_word = db.get_cached_word(word = text)

        # Отработка, если слово найдено в кэше
        if cached_word:

            db.add_user_word(user_id = user_id, word = text)

            return cached_word        
        # Если слово не найдено в кэше, обращаемся к LLM
        if cached_word == None:

            llm_response = ai.get_llm_response(text = text, context = context)
            if not llm_response:
                raise Exception("Ошибка при обращении к LLM.")

            # Добавляем слово в кэш
            db.add_cached_word(
                    word = text,
                    translation = llm_response.get("translation", ""),
                    transcription = llm_response.get("transcription", ""),
                    explanation = llm_response.get("explanation", ""),
                    examples = llm_response.get("examples", [])
                    )

            # Добавляем слово в словарь пользователя
            db.add_user_word(user_id = user_id, word = text) 

            return llm_response

    if context:

        llm_response = ai.get_llm_response(text = text, context = context)
        if not llm_response:
            raise Exception("Ошибка при обращении к LLM.")
        
        db.add_user_word(user_id = user_id, word = text)
        
        return llm_response

def handler(event, context):
    """
    Главная точка входа для Yandex Cloud Function.
    Сюда будут приходить запросы от фронтенда.
    """
    
    # Получаем HTTP-метод и тело запроса
    http_method = event.get('httpMethod', 'GET')
    body = event.get('body', '{}')
    
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON'})
        }

    # Регистрация пользователя
    if http_method == 'POST' and event.get('path') == '/register':

        # Получение логина и пароля пользователя
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        # Проверка корректности ввода
        if not email or not password: 
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Некорректный логин или пароль!'})
            }
        
        # Хеширование пароля
        hash_password = auth.hash_password(password = password)

        # Создание id пользователя
        user_id = db.create_user(email = email, password_hash = hash_password, name = name)
        if not user_id: 
            return {
                'statusCode': 501,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Ошибка при создании пользователя.'})
            }

        # Создание токена для доступа в течение 7 дней
        token = auth.generate_token(user_id = user_id)

        #Завершение регистрации
        return {
            'statusCode': 201,  # 201 Created (Успешно создано)
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Регистрация прошла успешно',
                'token': token,
                'user_id': user_id
            })
        }

    # Авторизация пользователя
    if http_method == 'POST' and event.get('path') == '/login':

        # Получение логина и пароля пользователя и проверка их корректности
        email = data.get('email')
        password = data.get('password')

        if not email or not password: 
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Неверный логин или пароль!'})
            }

        # Поиск аккаунта пользователя с введенным email
        user_data = db.check_user(email = email)

        # Отработка в случае, если пользователь с таким email не найден
        if user_data is None:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Incorrect!'})
            }
        
        # Отработка, если найден такой email
        else:
            # Проверка совпадения введенного пароля при авторизации с введенным при регистрации
            user_password_hash = user_data['hash_password']
            user_id = user_data['id']

            # Успешная авторизация, если пароли совпадают
            if auth.verify_password(plain_password = password, hashed_password = user_password_hash):
                token = auth.generate_token(user_id = user_id)
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'message': 'Successful login!',
                        'token': token,
                        'id': user_id
                    })
                }
            
            # Ошибка авторизации, если пароли не совпадают
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'message': 'Неверный логин или пароль!'})
                }

    # Перевод слова
    if http_method == 'POST' and event.get('path') == '/translate':
        # Получаем id и  текст для перевода из запроса
        text = data.get('text')
        user_id = data.get('user_id')
        translation_context = data.get('context')

        if not user_id or not isinstance(user_id, str):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Некорректный user_id!'})
            }
        
        if not text:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Текст для перевода не предоставлен!'})
            }

        if not isinstance(text, str):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Текст для перевода должен быть строкой!'})
            }
        
        if translation_context and not isinstance(translation_context, (str, dict)):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Контекст перевода должен быть строкой или словарем!'})
            }
        try:
            # Получаем результат перевода
            translation_result = handle_translate(body = data)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(translation_result, ensure_ascii = False)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Ошибка сервера при формировании перевода'})
            }   

          
    # Если маршрут не найден
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Not found'})
    }