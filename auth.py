"""
Модуль аутентификации через iiko API
Без локальной БД пользователей - все через iiko
"""
import hashlib
import requests
import logging
from flask_login import UserMixin

logger = logging.getLogger(__name__)

# Отключаем предупреждения SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class User(UserMixin):
    """Минимальная модель пользователя для flask-login"""
    
    def __init__(self, username, password_sha1):
        self.id = username  # ID = username
        self.username = username
        self.password_sha1 = password_sha1
        # UserMixin автоматически предоставляет is_authenticated, is_active, is_anonymous
        # Не устанавливаем их напрямую
    
    def get_id(self):
        return self.username


def authenticate_with_iiko(username, password, branch_id=None):
    """
    Аутентификация через iiko API
    
    Args:
        username: логин пользователя
        password: пароль пользователя (в открытом виде)
        branch_id: ID филиала для проверки (опционально)
    
    Returns:
        tuple: (success: bool, token: str или None, error: str или None)
    """
    try:
        # Вычисляем SHA1 от пароля
        password_sha1 = hashlib.sha1(password.encode()).hexdigest()
        
        logger.info(f"Попытка авторизации пользователя: {username}")
        
        # Получаем список филиалов для определения base_url
        from main import get_branches
        branches = get_branches()
        
        if not branches:
            logger.error("Не удалось получить список филиалов")
            return False, None, "Не удалось получить список филиалов"
        
        # Если branch_id не указан, берем первый ДОСТУПНЫЙ филиал
        if not branch_id:
            # Ищем доступный филиал (не Бутово, который недоступен)
            available_branches = [b for b in branches if b['id'] not in ['butovo', 'yasenevo', 'kommunarka']]
            if available_branches:
                branch_id = available_branches[0]['id']
                logger.info(f"Branch ID не указан, используем первый доступный: {branch_id}")
            else:
                branch_id = branches[0]['id']
                logger.info(f"Branch ID не указан, используем первый: {branch_id}")
        
        # Находим данные филиала
        branch_data = next((b for b in branches if b['id'] == branch_id), None)
        if not branch_data:
            # Пробуем первый филиал
            branch_data = branches[0]
            logger.info(f"Филиал {branch_id} не найден, используем первый: {branch_data['id']}")
        
        base_url = branch_data['base_url']
        
        # Формируем URL для авторизации
        auth_url = f"{base_url}/auth"
        
        # Параметры авторизации
        auth_params = {
            "login": username,
            "pass": password_sha1
        }
        
        logger.info(f"Отправляем запрос авторизации к: {auth_url}")
        logger.info(f"Логин: {username}, SHA1: {password_sha1[:10]}...")
        
        # Делаем запрос к iiko API
        response = requests.get(auth_url, params=auth_params, verify=False, timeout=30)
        
        if response.status_code == 200:
            token = response.text.strip()
            
            if token and len(token) > 0:
                logger.info(f"✅ Авторизация успешна! Токен: {token[:20]}...")
                return True, token, None
            else:
                logger.error("Токен пустой в ответе API")
                return False, None, "Пустой ответ от API"
        else:
            logger.error(f"Ошибка авторизации: {response.status_code} - {response.text}")
            return False, None, f"Неверный логин или пароль (код {response.status_code})"
    
    except Exception as e:
        logger.error(f"Исключение при авторизации: {str(e)}")
        return False, None, f"Ошибка подключения к серверу: {str(e)}"


def get_token_for_user(username, password_sha1, branch_id):
    """
    Получает токен для пользователя для конкретного филиала
    
    Args:
        username: логин пользователя
        password_sha1: SHA1 хеш пароля
        branch_id: ID филиала
    
    Returns:
        str или None: токен или None при ошибке
    """
    try:
        from main import get_branches
        branches = get_branches()
        
        branch_data = next((b for b in branches if b['id'] == branch_id), None)
        if not branch_data:
            logger.error(f"Филиал {branch_id} не найден")
            return None
        
        base_url = branch_data['base_url']
        auth_url = f"{base_url}/auth"
        
        auth_params = {
            "login": username,
            "pass": password_sha1
        }
        
        response = requests.get(auth_url, params=auth_params, verify=False, timeout=30)
        
        if response.status_code == 200:
            token = response.text.strip()
            if token:
                logger.info(f"Токен получен для {username} в филиале {branch_id}")
                return token
        
        logger.error(f"Не удалось получить токен: {response.status_code}")
        return None
    
    except Exception as e:
        logger.error(f"Ошибка получения токена: {str(e)}")
        return None

