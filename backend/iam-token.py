import json
import time
import jwt
import requests

def get_iam_token() -> str:
    with open("authorized_key.json", "r") as f:
        key_data = json.load(f)

    private_key = key_data["private_key"]
    key_id = key_data["id"]
    service_account_id = key_data["service_account_id"]

    now = int(time.time())
    payload = {
        "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        "iss": service_account_id,
        "iat": now,
        "exp": now + 3600
    }

    # Формируем JWT-токен, подписанный приватным ключом
    encoded_token = jwt.encode(
        payload,
        private_key,
        algorithm="PS256",
        headers={"kid": key_id}
    )

    # Обмениваем JWT на IAM-токен
    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        json={"jwt": encoded_token},
        timeout=5
    )
    response.raise_for_status()

    return response.json()["iamToken"]

if __name__ == "__main__":
    print(get_iam_token())