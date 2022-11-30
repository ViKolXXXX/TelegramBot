from flask import Flask, request
import requests
from dotenv import load_dotenv
import os
from os.path import join, dirname
from yookassa import Configuration, Payment
import json

app = Flask(__name__)


# Класс взаимодействия с платежной системой Юкасса
class PaymentYookassa:

    def __init__(self, chat_id):
        self.chat_id = chat_id

    # Создание счета на Юкассе
    def create_invoice(self):
        Configuration.account_id = get_from_env("SHOP_ID")
        Configuration.secret_key = get_from_env("PAYMENT_TOKEN")

        payment = Payment.create({
            "amount": {
                "value": "100.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://www.google.com"
            },
            "capture": True,
            "description": "Заказ №1",
            "metadata": {"chat_id": self.chat_id}
        })

        return payment.confirmation.confirmation_url

# получить секретные токены из .env файла
def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)  # возвращен секретный токен


def send_message(chat_id, text):
    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

def get_date_products(chat_id, table_name):
    app_id = get_from_env("APPSHEET_APP_ID")
    application_access_key = get_from_env("APPSHEET_APPLICATION_ACCESS_KEY")
    url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{table_name}/Action"
    data = {
            "Action": "Find",
            "Properties": {
               "Locale": "en-US",
               "Location": "47.623098, -122.330184",
               "Timezone": "Pacific Standard Time",
               "UserSettings": {
                  "Option 1": "value1",
                  "Option 2": "value2"
               }
            },
            "Rows": [
            ]
    }
    headers = {
        "Content-Type": "application/json",
        "ApplicationAccessKey": application_access_key
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.json())
    my_list = []
    for i in response.json():
        my_list.append(i.get('Наименование'))
    print(my_list)

    send_message(chat_id=chat_id, text=my_list)





def send_pay_button(chat_id, text):
    invoice_url = PaymentYookassa(chat_id).create_invoice()
    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"

    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": [[{
        "text": "Оплатить!",
        "url": f"{invoice_url}"
    }]]})}

    requests.post(url, data=data)

def send_get_table_button(chat_id, text):
    method = "sendMessage"
    token = get_from_env("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/{method}"

    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": [[{
        "text": "Получить список с AppSheet!"
    }]]})}
    requests.post(url, data=data)

def check_if_successful_payment(request):
    try:
        if request.json["event"] == "payment.succeeded":
            return True
    except KeyError:
        return False

    return False

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route('/', methods=["POST"])  # localhost:5000
def proces():
    # print(request.json)
    if check_if_successful_payment(request):
        # Обработка запроса Юкассы
        chat_id = request.json["object"]["metadata"]["chat_id"]
        send_message(chat_id, "Оплата прошла успешно")
    else:
        # Обработка запроса от Телеграм
        chat_id = request.json["message"]["chat"]["id"]
        send_pay_button(chat_id=chat_id, text="Тестовая оплата")
        get_date_products(chat_id=chat_id, table_name="Товар")

        # send_get_table_button(chat_id=chat_id, text="Получить таблицу из таблицы")

    return {"ok": True}
    # username = request.json["message"]["chat"]["username"]
    # text = request.json["message"]["text"]
    # send_message(chat_id=chat_id, text=f"Иди на хуй со своим {text}")


if __name__ == '__main__':
    app.run()
