import os
from dotenv import load_dotenv
import json
import requests
from litellm import completion

import litellm
litellm.set_verbose = True  # Включаем подробные логи LiteLLM

load_dotenv()

def get_iam_token() -> str:
    # Для локальной разработки используем токен из переменной окружения
    local_token = os.getenv("YANDEX_IAM_TOKEN")
    
    if local_token:
        return local_token

    # Для облачной функции получаем токен из метаданных
    try:
        url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
        response = requests.get(url, headers={"Metadata-Flavor": "Google"}, timeout=2)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"!!! ОШИБКА LITELLM: {repr(e)}")
        raise RuntimeError(f"Error occurred while fetching IAM token: {e}")

def get_llm_response(text: str, context: str | dict |None = None) -> dict:
    # Формирование запроса к LLM: инстуркции по выводу ответа и запрос пользователя

    # Инструкции для генерации ответа LLM
    ResponseInsructions = """
    "Ты — профессиональный англо-русский словарь. "
        "Твоя задача — перевести слово или фразу на русский язык и вернуть результат СТРОГО в формате JSON. "
        "ОЧЕНЬ ВАЖНО: Если слово многозначное (имеет несколько разных смыслов), "
        "обязательно перечисли все основные переводы через запятую в поле 'translation'. "
        "В поле 'examples' приведи примеры предложений, раскрывающие эти разные значения.\n"
        "Формат ответа:\n"
        "{\n"
        '  "translation": "перевод1, перевод2",\n'
        '  "transcription": "[транскрипция]",\n'
        '  "explanation": "краткое объяснение значений на русском",\n'
        '  "examples": [\n'
        '    {"original": "фраза 1", "translation": "перевод 1"},\n'
        '    {"original": "фраза 2", "translation": "перевод 2"}\n'
        "  ]\n"
        "}"
    """

    # Формирование запроса пользователя
    if isinstance(context, dict):
        context_fmt = json.dumps(context, ensure_ascii=False, indent=2)
    else:
        context_fmt = context if isinstance(context, str) else ""

    prompt = f"Текст: {text}\nКонтекст: {context_fmt}" if context_fmt else f"Текст: {text}"

    messages = [{"role": "system", "content": ResponseInsructions},
                {"role": "user", "content": prompt}
                ]


    # Отправка запроса к LLM
    
    token = get_iam_token()
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    if not folder_id:
        raise ValueError("YANDEX_FOLDER_ID не найден в окружении!")

    response = completion(
        model = f"openai/gpt://{folder_id}/yandexgpt-lite/latest",
        messages = messages,
        api_key = token,
        api_base = "https://ai.api.cloud.yandex.net/v1",
        response_format = {"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)