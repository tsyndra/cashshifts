import requests
import json
from datetime import datetime, timedelta

# Base URL for the API
BASE_URL = "https://hatimaki-novovatutinskaya.iiko.it:443/resto/api"

# Authentication credentials
login = "tsyndra"
password = "cb084e5e5f9bfc6cf6c705a382817739c8aebeac"

def get_auth_token():
    # Make authentication request
    auth_url = f"{BASE_URL}/auth"
    params = {
        "login": login,
        "pass": password
    }
    
    try:
        response = requests.get(auth_url, params=params, verify=False)  # verify=False for self-signed certificates
        response.raise_for_status()  # Raise an exception for bad status codes
        print(response.text)
        # The token is in the response text
        token = response.text.strip()
        print(f"Successfully obtained token: {token}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error getting authentication token: {e}")
        return None

def get_cash_shifts(token):
    # Параметры запроса
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    yesterday = today - timedelta(days=1)
    params = {
        "status": "ANY",
        "revisionFrom": -1,
        "openDateFrom": week_ago.strftime("%Y-%m-%d"),
        "openDateTo": yesterday.strftime("%Y-%m-%d")
    }
    try:
        response = requests.get(f"{BASE_URL}/v2/cashshifts/list?key={token}", params=params, verify=False)
        response.raise_for_status()
        cash_shifts = response.json()
        print("Successfully retrieved cash shifts")
        return cash_shifts
    except requests.exceptions.RequestException as e:
        print(f"Error getting cash shifts: {e}")
        if e.response is not None:
            print(e.response.text)
        return None

def get_cash_shift_payments(token, session_id):
    url = f"{BASE_URL}/v2/cashshifts/payments/list/{session_id}?key={token}"
    params = {"hideAccepted": "false"}
    try:
        response = requests.get(url, params=params, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting payments for cash shift {session_id}: {e}")
        if e.response is not None:
            print(e.response.text)
        return None

def main():
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token. Exiting...")
        return
    
    # Get cash shifts using the token
    cash_shifts = get_cash_shifts(token)
    if cash_shifts:
        print("\nCash Shifts Data:")
        print(json.dumps(cash_shifts, indent=2, ensure_ascii=False))
        # Получаем id всех смен
        ids = [shift["id"] for shift in cash_shifts if "id" in shift]
        print(f"\nПолучено {len(ids)} id смен. Загружаю подробности по каждой...")
        # Получаем payments для указанного id
        test_id = "cb21fce6-af50-4756-82cc-378e7c3a0cd9"
        payments = get_cash_shift_payments(token, test_id)
        print(f"\nPayments для смены {test_id}:")
        print(json.dumps(payments, indent=2, ensure_ascii=False))
        # Сохраняем ответ в файл
        with open("payments_response.json", "w", encoding="utf-8") as f:
            json.dump(payments, f, ensure_ascii=False, indent=2)
        print("\nОтвет сохранён в payments_response.json")

        # Обработка для нового файла: actualSum + name типа оплаты
        with open("payment_types.json", "r", encoding="utf-8") as f:
            payment_types_data = json.load(f)
        payment_types_dict = {pt["id"]: pt["name"] for pt in payment_types_data["paymentTypes"]}

        with open("payments_response.json", "r", encoding="utf-8") as f:
            payments_data = json.load(f)
        result = []
        for rec in payments_data.get("cashlessRecords", []):
            payment_type_id = rec.get("paymentTypeId")
            actual_sum = rec.get("actualSum")
            name = payment_types_dict.get(payment_type_id, payment_type_id)
            result.append({"actualSum": actual_sum, "paymentTypeName": name})
        with open("payments_actuals.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("Результат сохранён в payments_actuals.json")

if __name__ == "__main__":
    main()
