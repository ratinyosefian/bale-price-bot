import requests
from config import BOT_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


def get_updates(offset=None):

    url = f"{BASE_URL}/getUpdates"

    params = {}

    if offset is not None:
        params["offset"] = offset

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def send_message(chat_id, text, reply_markup=None):

    url = f"{BASE_URL}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup is not None:
        data["reply_markup"] = reply_markup

    response = requests.post(
        url,
        json=data,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


def answer_callback_query(callback_query_id):

    url = f"{BASE_URL}/answerCallbackQuery"

    response = requests.post(
        url,
        json={"callback_query_id": callback_query_id},
        timeout=15
    )

    response.raise_for_status()

    return response.json()
