import os
import requests
from flask import Flask, request

app = Flask(__name__)

print("APP.PY LOADED", flush=True)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

print("TELEGRAM TOKEN EXISTS:", bool(TELEGRAM_BOT_TOKEN), flush=True)
print("GEMINI KEY EXISTS:", bool(GEMINI_API_KEY), flush=True)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_message(chat_id, text):
    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )

    print("TELEGRAM STATUS:", response.status_code, flush=True)
    print("TELEGRAM RESPONSE:", response.text, flush=True)

    return response


def ask_gemini(text):
    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    response = requests.post(
        url,
        json={
            "contents": [
                {
                    "parts": [
                        {"text": text}
                    ]
                }
            ]
        },
        timeout=60
    )

    print("GEMINI STATUS:", response.status_code, flush=True)
    print("GEMINI RESPONSE:", response.text, flush=True)

    response.raise_for_status()
    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]


@app.get("/")
def home():
    return "Ellie is running!"


@app.post("/telegram")
def telegram_webhook():
    update = request.get_json(silent=True) or {}

    print("TELEGRAM UPDATE:", update, flush=True)

    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")

    if not chat_id:
        return "OK", 200

    if text == "/start":
        send_telegram_message(
            chat_id,
            "Привет! Я Элли 👋 Напиши мне что-нибудь."
        )
        return "OK", 200

    if text:
        try:
            answer = ask_gemini(text)
            send_telegram_message(chat_id, answer)

        except Exception as error:
            print("ERROR:", repr(error), flush=True)

            send_telegram_message(
                chat_id,
                "Не получилось получить ответ. Попробуй ещё раз."
            )

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
