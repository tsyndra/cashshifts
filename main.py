import requests
import json
from datetime import datetime, timedelta
import urllib3

# Отключаем предупреждения о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация филиалов
BRANCHES = [
    {
        "id": "novovatutinskaya",
        "name": "Нововатутинская",
        "base_url": "https://hatimaki-novovatutinskaya.iiko.it:443/resto/api"
    },
    # Добавьте другие филиалы здесь
]

def get_branches():
    """Возвращает список филиалов"""
    return BRANCHES

def get_branch_name(branch_id):
    """Возвращает название филиала по ID"""
    for branch in BRANCHES:
        if branch['id'] == branch_id:
            return branch['name']
    return "Неизвестный филиал"

def get_auth_token(login, password, branch_id=None):
    """Получение токена авторизации"""
    # Получаем base_url для филиала
    if branch_id:
        branch_data = next((b for b in BRANCHES if b['id'] == branch_id), None)
        if not branch_data:
            print(f"Филиал {branch_id} не найден")
            return None
        base_url = branch_data['base_url']
    else:
        # По умолчанию используем первый филиал
        base_url = BRANCHES[0]['base_url']
    
    auth_url = f"{base_url}/auth"
    params = {
        "login": login,
        "pass": password  # Ожидается SHA1 хеш
    }
    
    try:
        response = requests.get(auth_url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        token = response.text.strip()
        print(f"Successfully obtained token for {branch_id}: {token}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error getting authentication token: {e}")
        return None

def get_cash_shifts(token, branch_id=None):
    """Получение списка кассовых смен"""
    # Получаем base_url для филиала
    if branch_id:
        branch_data = next((b for b in BRANCHES if b['id'] == branch_id), None)
        if not branch_data:
            print(f"Филиал {branch_id} не найден")
            return None
        base_url = branch_data['base_url']
    else:
        base_url = BRANCHES[0]['base_url']
    
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
        url = f"{base_url}/v2/cashshifts/list?key={token}"
        response = requests.get(url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        cash_shifts = response.json()
        print(f"Successfully retrieved {len(cash_shifts)} cash shifts")
        return cash_shifts
    except requests.exceptions.RequestException as e:
        print(f"Error getting cash shifts: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
        return None

def get_cash_shift_payments(token, session_id, branch_id=None):
    """Получение платежей для конкретной смены"""
    # Получаем base_url для филиала
    if branch_id:
        branch_data = next((b for b in BRANCHES if b['id'] == branch_id), None)
        if not branch_data:
            print(f"Филиал {branch_id} не найден")
            return None
        base_url = branch_data['base_url']
    else:
        base_url = BRANCHES[0]['base_url']
    
    url = f"{base_url}/v2/cashshifts/payments/list/{session_id}?key={token}"
    params = {"hideAccepted": "false"}
    
    try:
        response = requests.get(url, params=params, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting payments for cash shift {session_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
        return None

def main():
    """Тестовая функция"""
    # Тестовые данные
    login = "tsyndra"
    password = "cb084e5e5f9bfc6cf6c705a382817739c8aebeac"  # SHA1 хеш
    branch_id = "novovatutinskaya"
    
    # Получаем токен
    token = get_auth_token(login, password, branch_id)
    if not token:
        print("Failed to get authentication token. Exiting...")
        return
    
    # Получаем смены
    cash_shifts = get_cash_shifts(token, branch_id)
    if cash_shifts:
        print(f"\nПолучено {len(cash_shifts)} смен")
        
        # Берем первую смену для теста
        if len(cash_shifts) > 0:
            test_shift = cash_shifts[0]
            session_id = test_shift.get("id")
            print(f"\nПолучаем платежи для смены: {session_id}")
            
            payments = get_cash_shift_payments(token, session_id, branch_id)
            if payments:
                print(f"Получено платежей:")
                print(f"- Безналичных: {len(payments.get('cashlessRecords', []))}")
                print(f"- Внесений: {len(payments.get('payInRecords', []))}")
                print(f"- Выдач: {len(payments.get('payOutsRecords', []))}")

if __name__ == "__main__":
    main()
