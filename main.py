import requests
import json
from datetime import datetime, timedelta
import urllib3

# Отключаем предупреждения о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Конфигурация API
IIKO_API_KEY = "your-api-key-here"  # Замените на ваш API ключ
IIKO_API_URL = "https://api-ru.iiko.services/api/1"

def get_iiko_bearer_token():
    """Получает bearer token для нового API iiko"""
    try:
        auth_url = "https://api-ru.iiko.services/api/1/access_token"
        
        # Данные для получения токена согласно документации
        auth_data = {
            "apiLogin": IIKO_API_KEY
        }
        
        response = requests.post(auth_url, json=auth_data, verify=False, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            if token:
                print(f"✅ Bearer token получен: {token[:20]}...")
                return token
            else:
                print("❌ Токен не найден в ответе")
                return None
        else:
            print(f"❌ Ошибка получения токена: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при получении токена: {e}")
        return None

def get_branches():
    """Возвращает статический список всех филиалов"""
    # Статический список всех филиалов с их адресами
    branches = [
        {
            "id": "butovo",
            "name": "Бутово", 
            "base_url": "https://dostavka-hatimaki-butovo.iiko.it:443/resto/api"
        },
        {
            "id": "yasenevo",
            "name": "Ясенево",
            "base_url": "https://hatimakiyasenevo.iiko.it:443/resto/api"
        },
        {
            "id": "kommunarka", 
            "name": "Коммунарка",
            "base_url": "https://dostavka-hatimaki-kommunarka.iiko.it:443/resto/api"
        },
        {
            "id": "podolsk",
            "name": "Подольск", 
            "base_url": "https://dostavka-hatimaki-podolsk.iiko.it:443/resto/api"
        },
        {
            "id": "moskovskii",
            "name": "Московский",
            "base_url": "https://dostavka-hatimaki-moskovskii.iiko.it:443/resto/api"
        },
        {
            "id": "etalon",
            "name": "Эталон",
            "base_url": "https://dostavka-hatimaki-etalon.iiko.it:443/resto/api"
        },
        {
            "id": "bobrovo",
            "name": "Боброво",
            "base_url": "https://dostavka-hatimaki-bobrovo.iiko.it:443/resto/api"
        },
        {
            "id": "scherbinka",
            "name": "Щербинка (Степано)",
            "base_url": "https://hatimaki-scherbinka-ip-stepano.iiko.it:443/resto/api"
        },
        {
            "id": "monahovo",
            "name": "Монахово (Тащили)",
            "base_url": "https://hatimaki-monahovoi-ip-taschili.iiko.it:443/resto/api"
        },
        {
            "id": "40let",
            "name": "40 лет",
            "base_url": "https://hatimaki-40-let.iiko.it:443/resto/api"
        },
        {
            "id": "skandinaviya",
            "name": "Скандинавия",
            "base_url": "https://hatimaki-skandinaviya.iiko.it:443/resto/api"
        },
        {
            "id": "ispaniya",
            "name": "Испания", 
            "base_url": "https://hatimaki-ispaniya.iiko.it:443/resto/api"
        },
        {
            "id": "novovatutinskaya",
            "name": "Нововатутинская",
            "base_url": "https://hatimaki-novovatutinskaya.iiko.it:443/resto/api"
        },
        {
            "id": "luchi",
            "name": "Лучи",
            "base_url": "https://hatimaki-luchi.iiko.it:443/resto/api"
        }
    ]
    
    print(f"✅ Возвращаем статический список из {len(branches)} филиалов")
    return branches

def get_branches_old():
    """Старая функция получения филиалов через API (не используется)"""
    try:
        # Получаем bearer token
        token = get_iiko_bearer_token()
        if not token:
            print("❌ Не удалось получить bearer token, используем fallback")
            return get_fallback_branches()
        
        # Получаем список организаций согласно документации API v1
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Используем правильный endpoint согласно документации
        response = requests.get(f"{IIKO_API_URL}/organizations", headers=headers, verify=False, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            organizations = data.get('organizations', [])
            
            print(f"✅ Получено организаций из API: {len(organizations)}")
            
            branches = []
            for org in organizations:
                # Согласно документации, организация содержит id, name и другие поля
                branches.append({
                    "id": org.get('id'),
                    "name": org.get('name'),
                    "base_url": f"https://{org.get('domain')}/resto/api" if org.get('domain') else None
                })
                print(f"  🏢 {org.get('name')} (ID: {org.get('id')})")
            
            return branches
        else:
            print(f"❌ Ошибка получения организаций: {response.status_code} - {response.text}")
            return get_fallback_branches()
            
    except Exception as e:
        print(f"❌ Ошибка при получении организаций: {e}")
        return get_fallback_branches()

def get_fallback_branches():
    """Возвращает список филиалов, полученных через старый API"""
    print("🔄 Получаем организации через старый API...")
    
    # Полный список всех доменов Hatimaki
    known_domains = [
        {"domain": "dostavka-hatimaki-butovo.iiko.it:443", "name": "Бутово", "id": "butovo"},
        {"domain": "hatimakiyasenevo.iiko.it:443", "name": "Ясенево", "id": "yasenevo"},
        {"domain": "dostavka-hatimaki-kommunarka.iiko.it:443", "name": "Коммунарка", "id": "kommunarka"},
        {"domain": "dostavka-hatimaki-podolsk.iiko.it:443", "name": "Подольск", "id": "podolsk"},
        {"domain": "dostavka-hatimaki-moskovskii.iiko.it:443", "name": "Московский", "id": "moskovskii"},
        {"domain": "dostavka-hatimaki-etalon.iiko.it:443", "name": "Эталон", "id": "etalon"},
        {"domain": "dostavka-hatimaki-bobrovo.iiko.it:443", "name": "Боброво", "id": "bobrovo"},
        {"domain": "hatimaki-scherbinka-ip-stepano.iiko.it:443", "name": "Щербинка (Степано)", "id": "scherbinka-stepano"},
        {"domain": "hatimaki-monahovoi-ip-taschili.iiko.it:443", "name": "Монахово (Тащили)", "id": "monahovoi-taschili"},
        {"domain": "hatimaki-40-let.iiko.it:443", "name": "40 лет", "id": "40-let"},
        {"domain": "hatimaki-skandinaviya.iiko.it:443", "name": "Скандинавия", "id": "skandinaviya"},
        {"domain": "hatimaki-ispaniya.iiko.it:443", "name": "Испания", "id": "ispaniya"},
        {"domain": "hatimaki-novovatutinskaya.iiko.it:443", "name": "Нововатутинская", "id": "novovatutinskaya"},
        {"domain": "hatimaki-luchi.iiko.it:443", "name": "Лучи", "id": "luchi"}
    ]
    
    branches = []
    
    for domain_info in known_domains:
        try:
            domain = domain_info["domain"]
            print(f"🌐 Проверяем домен: {domain}")
            
            # Получаем токен для проверки доступности
            old_api_url = f"https://{domain}/resto/api"
            auth_url = f"{old_api_url}/auth"
            auth_params = {
                "login": "tsyndra",
                "pass": "cb084e5e5f9bfc6cf6c705a382817739c8aebeac"  # SHA1 хеш
            }
            
            auth_response = requests.get(auth_url, params=auth_params, verify=False, timeout=10)
            
            if auth_response.status_code == 200:
                token = auth_response.text.strip()
                print(f"✅ Домен {domain} доступен, токен: {token[:20]}...")
                
                branches.append({
                    "id": domain_info["id"],
                    "name": domain_info["name"],
                    "base_url": old_api_url
                })
            else:
                print(f"❌ Домен {domain} недоступен: {auth_response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка для домена {domain_info['domain']}: {e}")
    
    if not branches:
        print("🔄 Ни один домен не доступен, используем захардкоженный список")
        branches = [
            {
                "id": "novovatutinskaya",
                "name": "Нововатутинская",
                "base_url": "https://hatimaki-novovatutinskaya.iiko.it:443/resto/api"
            }
        ]
    
    print(f"✅ Найдено доступных организаций: {len(branches)}")
    return branches

def get_branch_name(branch_id):
    """Возвращает название филиала по ID"""
    branches = get_branches()
    for branch in branches:
        if branch['id'] == branch_id:
            return branch['name']
    return "Неизвестный филиал"

def get_cash_shifts_v2(organization_id, token, from_date=None, to_date=None):
    """Получает кассовые смены через новый API v2 согласно документации"""
    try:
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Данные запроса согласно документации кассовых смен v2
        request_data = {
            "organizationIds": [organization_id],
            "from": from_date,
            "to": to_date
        }
        
        response = requests.post(
            f"{IIKO_API_URL}/cash_shifts", 
            json=request_data, 
            headers=headers, 
            verify=False, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            cash_shifts = data.get('cashShifts', [])
            
            print(f"✅ Получено кассовых смен через API v2: {len(cash_shifts)}")
            
            # Преобразуем в формат, совместимый со старым API
            shifts = []
            for shift in cash_shifts:
                shifts.append({
                    "id": shift.get('id'),
                    "openDate": shift.get('openDate'),
                    "closeDate": shift.get('closeDate'),
                    "cashierName": shift.get('cashierName', 'Неизвестный кассир'),
                    "cashierId": shift.get('cashierId')
                })
            
            return shifts
        else:
            print(f"❌ Ошибка получения кассовых смен v2: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Исключение при получении кассовых смен v2: {e}")
        return []

def get_auth_token(login, password, branch_id=None):
    """Получение токена авторизации"""
    # Получаем base_url для филиала
    branches = get_branches()
    if branch_id:
        branch_data = next((b for b in branches if b['id'] == branch_id), None)
        if not branch_data:
            print(f"Филиал {branch_id} не найден")
            return None
        base_url = branch_data['base_url']
    else:
        # По умолчанию используем первый филиал
        if branches:
            base_url = branches[0]['base_url']
        else:
            print("Нет доступных филиалов")
            return None
    
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
    branches = get_branches()
    if branch_id:
        branch_data = next((b for b in branches if b['id'] == branch_id), None)
        if not branch_data:
            print(f"Филиал {branch_id} не найден")
            return None
        base_url = branch_data['base_url']
    else:
        if branches:
            base_url = branches[0]['base_url']
        else:
            print("Нет доступных филиалов")
            return None
    
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
    branches = get_branches()
    if branch_id:
        branch_data = next((b for b in branches if b['id'] == branch_id), None)
        if not branch_data:
            print(f"Филиал {branch_id} не найден")
            return None
        base_url = branch_data['base_url']
    else:
        if branches:
            base_url = branches[0]['base_url']
        else:
            print("Нет доступных филиалов")
            return None
    
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
