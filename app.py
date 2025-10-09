from flask import Flask, render_template, request, jsonify, send_file, make_response, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
from werkzeug.utils import secure_filename
import tempfile
from main import get_auth_token, get_cash_shifts, get_cash_shift_payments, get_branches, get_branch_name
import requests
import numpy as np
from models import db, User, UserBranch
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cash_shifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cash_shifts.log')
    ]
)
logger = logging.getLogger(__name__)

# Создаем папку для загрузок если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin_user():
    """Создание администратора по умолчанию"""
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('CashShifts2024!')
            db.session.add(admin)
            db.session.commit()
            logger.info("Создан администратор по умолчанию: admin/CashShifts2024!")
            logger.info(f"SHA1 хеш пароля: {admin.get_sha1_password()}")

def get_user_auth_token(branch_id, user_id=None):
    """Получение токена аутентификации с учетными данными пользователя"""
    try:
        if not current_user.is_authenticated:
            logger.error("Пользователь не аутентифицирован")
            return None
        
        # Получаем данные пользователя
        user = current_user
        if user_id:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"Пользователь с ID {user_id} не найден")
                return None
        
        # Получаем SHA1 хеш пароля
        password_sha1 = user.get_sha1_password()
        if not password_sha1:
            logger.error(f"SHA1 хеш пароля не найден для пользователя {user.username}")
            return None
        
        # Получаем base_url для филиала
        branches = get_branches()
        branch_data = next((b for b in branches if b['id'] == branch_id), None)
        if not branch_data:
            logger.error(f"Филиал {branch_id} не найден")
            return None
        
        base_url = branch_data['base_url']
        
        # Формируем URL для получения токена
        auth_url = f"{base_url}/auth"
        
        # Данные для аутентификации (используем формат из main.py)
        auth_params = {
            "login": user.username,
            "pass": password_sha1
        }
        
        logger.info(f"Запрос токена для пользователя {user.username} в филиале {branch_id}")
        
        # Отправляем запрос (используем GET с параметрами как в main.py)
        response = requests.get(auth_url, params=auth_params, verify=False, timeout=30)
        
        if response.status_code == 200:
            # Токен возвращается как текст (как в main.py)
            token = response.text.strip()
            if token:
                logger.info(f"Успешно получен токен для пользователя {user.username}: {token}")
                return token
            else:
                logger.error("Токен не найден в ответе")
                return None
        else:
            logger.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении токена пользователя: {str(e)}")
        return None

# Загружаем типы платежей
def load_payment_types():
    try:
        with open("payment_types.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return {pt["id"]: pt["name"] for pt in data["paymentTypes"]}
    except FileNotFoundError:
        return {}

@app.route('/')
@login_required
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Перенаправляем на запрошенную страницу или на главную
            next_page = request.args.get('next')
            if next_page and url_is_safe(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

def url_is_safe(url):
    """Проверка безопасности URL для перенаправления"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, url))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()
    branches = get_branches()
    return render_template('admin.html', users=users, branches=branches)

@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return jsonify({"error": "Доступ запрещен"}), 403
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    is_admin = data.get('is_admin', False)
    branches = data.get('branches', [])
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Пользователь с таким именем уже существует"}), 400
    
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Добавляем связи с филиалами
    for branch in branches:
        user_branch = UserBranch(
            user_id=user.id,
            branch_id=branch['id'],
            branch_name=branch['name']
        )
        db.session.add(user_branch)
    
    db.session.commit()
    return jsonify({"success": True, "message": "Пользователь добавлен"})

@app.route('/admin/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Доступ запрещен"}), 403
    
    if user_id == current_user.id:
        return jsonify({"error": "Нельзя удалить самого себя"}), 400
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True, "message": "Пользователь удален"})

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Доступ запрещен"}), 403
    
    if user_id == current_user.id:
        return jsonify({"error": "Нельзя изменить статус самого себя"}), 400
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"success": True, "is_active": user.is_active})

@app.route('/admin/users/<int:user_id>/change-password', methods=['POST'])
@login_required
def change_user_password(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Доступ запрещен"}), 403
    
    data = request.json
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({"error": "Пароль не может быть пустым"}), 400
    
    user = User.query.get_or_404(user_id)
    user.set_password(new_password)
    db.session.commit()
    
    logger.info(f"Пароль изменен для пользователя {user.username}")
    return jsonify({"success": True, "message": "Пароль изменен"})

@app.route('/api/branches')
@login_required
def api_branches():
    """Получение списка филиалов"""
    try:
        logger.info("Запрос списка филиалов")
        branches = get_branches()
        logger.info(f"Получено {len(branches)} филиалов")
        return jsonify(branches)
    except Exception as e:
        logger.error(f"Ошибка в api_branches: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cash-shifts')
@login_required
def api_cash_shifts():
    """Получение списка кассовых смен"""
    try:
        branch_id = request.args.get('branch_id')
        logger.info(f"Запрос списка кассовых смен для филиала: {branch_id}")
        
        # Используем учетные данные пользователя для получения токена
        token = get_user_auth_token(branch_id)
        if not token:
            logger.error("Ошибка аутентификации пользователя")
            return jsonify({"error": "Ошибка аутентификации"}), 401
        
        cash_shifts = get_cash_shifts(token, branch_id)
        if not cash_shifts:
            logger.error("Ошибка получения кассовых смен")
            return jsonify({"error": "Ошибка получения кассовых смен"}), 500
        
        # Добавляем информацию о филиале к каждой смене
        branch_name = get_branch_name(branch_id) if branch_id else "Ватутинки"
        for shift in cash_shifts:
            shift['branch_name'] = branch_name
            shift['branch_id'] = branch_id
        
        logger.info(f"Получено {len(cash_shifts)} кассовых смен")
        return jsonify(cash_shifts)
    except Exception as e:
        logger.error(f"Ошибка в api_cash_shifts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cash-shift/<session_id>/payments')
@login_required
def api_cash_shift_payments(session_id):
    """Получение платежей для конкретной смены"""
    try:
        branch_id = request.args.get('branch_id')
        logger.info(f"Запрос платежей для смены {session_id} филиала: {branch_id}")
        
        # Используем учетные данные пользователя для получения токена
        token = get_user_auth_token(branch_id)
        if not token:
            return jsonify({"error": "Ошибка аутентификации"}), 401
        
        payments = get_cash_shift_payments(token, session_id, branch_id)
        if not payments:
            return jsonify({"error": "Ошибка получения платежей"}), 500
        
        # Обрабатываем платежи для удобного отображения
        payment_types = load_payment_types()
        processed_payments = []
        
        # Обрабатываем только безналичные операции (внесения и выдачи исключены)
        cashless_records = payments.get("cashlessRecords", [])
        payin_records = payments.get("payInRecords", [])
        payout_records = payments.get("payOutsRecords", [])
        
        cashless_count = len(cashless_records)
        payin_count = len(payin_records)
        payout_count = len(payout_records)
        
        logger.info(f"Найдено операций: cashless={cashless_count}, payin={payin_count}, payout={payout_count}")
        logger.info(f"Обрабатываем только безналичные операции: {cashless_count} (внесения и выдачи исключены)")
        
        # Обрабатываем только безналичные операции
        for record in cashless_records:
            payment_type_id = record.get("paymentTypeId")
            if payment_type_id:
                # Пробуем найти название типа платежа в справочнике
                payment_type_name = payment_types.get(payment_type_id)
                if not payment_type_name:
                    # Если не нашли в справочнике, показываем ID с предупреждением
                    payment_type_name = f"Неизвестный тип ({payment_type_id[:8]}...)"
                    logger.warning(f"Неизвестный тип платежа: {payment_type_id}")
            else:
                payment_type_name = "Безналичный платеж (без типа)"
            record['_operation_type'] = 'cashless'
            record['_payment_type_name'] = payment_type_name
        
        # Внесения и выдачи наличных исключены из отображения
        all_records = cashless_records  # Только безналичные операции
        
        for record in all_records:
            payment_type_name = record.get('_payment_type_name', 'Неизвестный тип')
            operation_type = record.get('_operation_type', 'unknown')
            
            # actualSum приходит в рублях (float)
            actual_sum = record.get("actualSum", 0)
            
            # Обрабатываем дату
            raw_date = record.get("info", {}).get("creationDate")  # creationDate находится внутри info
            logger.info(f"Сырая дата из API: {raw_date} (тип: {type(raw_date)})")
            
            # Отладочная информация - покажем все поля записи
            logger.info(f"Все поля записи: {list(record.keys())}")
            if 'info' in record:
                logger.info(f"Поля info: {list(record['info'].keys())}")
                logger.info(f"info.date: {record['info'].get('date')}")
                logger.info(f"info.creationDate: {record['info'].get('creationDate')}")
            
            # Преобразуем дату в правильный формат
            try:
                if isinstance(raw_date, str):
                    # Если дата приходит как строка, пробуем разные форматы
                    if raw_date.isdigit():
                        # Если это timestamp в миллисекундах
                        date_obj = datetime.fromtimestamp(int(raw_date) / 1000)
                        logger.info(f"Обработали как timestamp: {date_obj}")
                    else:
                        # Пробуем парсить как ISO формат
                        date_obj = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                        logger.info(f"Обработали как ISO: {date_obj}")
                elif isinstance(raw_date, (int, float)):
                    # Если это timestamp
                    date_obj = datetime.fromtimestamp(raw_date / 1000)
                    logger.info(f"Обработали как timestamp (число): {date_obj}")
                else:
                    # Если это уже datetime объект
                    date_obj = raw_date
                    logger.info(f"Уже datetime объект: {date_obj}")
                
                formatted_date = date_obj.isoformat()
                logger.info(f"Финальная дата: {formatted_date}")
            except Exception as e:
                logger.error(f"Ошибка обработки даты {raw_date}: {e}")
                formatted_date = raw_date  # Оставляем как есть
            
            processed_payment = {
                "id": record["info"]["id"],
                "date": formatted_date,
                "creationDate": record["info"]["creationDate"],
                "paymentTypeId": record.get("paymentTypeId"),
                "paymentTypeName": payment_type_name,
                "operationType": operation_type,  # Добавляем тип операции (cashless/payin/payout)
                "actualSum": actual_sum,  # В рублях
                "originalSum": record["originalSum"],
                "status": record["status"],
                "type": record["info"]["type"],
                "cashierId": record["info"]["cashierId"],
                "comment": record["info"].get("comment", "")  # Добавляем комментарий для внесений/выдач
            }
            processed_payments.append(processed_payment)
        
        # Логируем информацию о платежах
        total_sum = sum(p.get("actualSum", 0) for p in processed_payments)
        logger.info(f"Отправляем {len(processed_payments)} платежей, общая сумма: {total_sum}")
        
        return jsonify({
            "sessionId": payments.get("sessionId"),
            "operationDay": payments.get("operationDay"),
            "payments": processed_payments
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-bank-report', methods=['POST'])
@login_required
def upload_bank_report():
    """Загрузка банковского отчета"""
    if 'file' not in request.files:
        return jsonify({"error": "Файл не найден"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Пытаемся прочитать файл как Excel или CSV
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                try:
                    # Читаем Excel с правильными параметрами
                    df = pd.read_excel(
                        filepath, 
                        engine='openpyxl',
                        sheet_name=0,  # Первый лист
                        header=0,      # Первая строка как заголовок
                        na_values=['', 'nan', 'NaN', 'NULL'],  # Значения для NaN
                        keep_default_na=True,
                        decimal=','     # Запятая как десятичный разделитель для копеек
                    )
                except Exception as excel_error:
                    try:
                        # Пробуем с другим движком
                        df = pd.read_excel(
                            filepath, 
                            engine='xlrd',
                            sheet_name=0,
                            header=0,
                            na_values=['', 'nan', 'NaN', 'NULL'],
                            keep_default_na=True
                        )
                    except Exception as xlrd_error:
                        return jsonify({"error": f"Не удается прочитать Excel файл. Ошибка openpyxl: {str(excel_error)}, Ошибка xlrd: {str(xlrd_error)}"}), 500
            elif filename.endswith('.csv'):
                try:
                    # Пробуем разные кодировки для CSV
                    df = pd.read_csv(
                        filepath, 
                        encoding='utf-8',
                        decimal=','     # Запятая как десятичный разделитель для копеек
                    )
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(
                            filepath, 
                            encoding='cp1251',
                            decimal=','
                        )
                    except UnicodeDecodeError:
                        df = pd.read_csv(
                            filepath, 
                            encoding='latin-1',
                            decimal=','
                        ) 
            else:
                return jsonify({"error": "Неподдерживаемый формат файла. Поддерживаются только .xlsx, .xls и .csv"}), 400
            
            # Проверяем, что DataFrame не пустой
            if df.empty:
                return jsonify({"error": "Файл не содержит данных"}), 400
            
            # Очищаем данные от NaN значений
            df = df.fillna('')
            
            # Обрабатываем числовые колонки - правильно обрабатываем запятые как десятичные разделители
            for column in df.columns:
                if df[column].dtype == 'object':  # Если колонка содержит строки
                    # Пробуем конвертировать строки с запятыми в числа
                    try:
                        # Обрабатываем запятые как десятичные разделители (например: "1234,56" -> 1234.56)
                        df[column] = df[column].astype(str).str.replace(' ', '')
                        # Заменяем запятую на точку для корректной конвертации
                        df[column] = df[column].str.replace(',', '.')
                        # Пробуем конвертировать в числовой тип
                        numeric_values = pd.to_numeric(df[column], errors='coerce')
                        # Если большинство значений успешно конвертировались, заменяем колонку
                        if not numeric_values.isna().all():
                            df[column] = numeric_values
                    except:
                        pass  # Если не удалось конвертировать, оставляем как есть
            
            # Очищаем все NaN значения перед конвертацией в JSON
            df = df.replace([np.inf, -np.inf], '')  # Заменяем бесконечности
            df = df.fillna('')  # Заменяем NaN на пустые строки
            
            # Конвертируем в JSON для отправки на фронтенд
            data = df.to_dict('records')
            
            # Дополнительная очистка данных от NaN значений
            for row in data:
                for key, value in row.items():
                    if pd.isna(value) or value == 'nan' or value == 'NaN':
                        row[key] = ''
                    elif isinstance(value, (int, float)) and (np.isnan(value) or np.isinf(value)):
                        row[key] = ''
            
            return jsonify({
                "success": True,
                "filename": filename,
                "data": data,
                "columns": df.columns.tolist(),
                "rows_count": len(data)
            })
            
        except Exception as e:
            # Удаляем файл в случае ошибки
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"error": f"Ошибка обработки файла: {str(e)}"}), 500

@app.route('/api/compare-data', methods=['POST'])
@login_required
def compare_data():
    """Сравнение данных кассовой смены с банковским отчетом"""
    try:
        data = request.json
        cash_shift_data = data.get('cashShiftData', [])
        bank_data = data.get('bankData', [])
        mapping = data.get('mapping', {})  # Маппинг колонок
        
        # Получаем колонки для сравнения
        amount_column = mapping.get('amount', 'Сумма')
        type_column = mapping.get('type', 'Тип')
        date_column = mapping.get('date', 'Дата')  # Добавляем колонку даты если есть
        
        # Подготавливаем данные кассовой смены для сравнения
        cash_operations = []
        for payment in cash_shift_data:
            cash_operations.append({
                'paymentTypeName': payment.get('paymentTypeName', 'Неизвестно'),
                'actualSum': payment.get('actualSum', 0),
                'date': payment.get('date', ''),
                'id': payment.get('id', ''),
                'matched': False  # Флаг для отслеживания совпадений
            })
        
        # Подготавливаем данные банковского отчета для сравнения
        bank_operations = []
        for row in bank_data:
            payment_type = str(row.get(type_column, 'Неизвестно')).strip()
            
            # Правильная обработка суммы из банковского отчета
            amount_raw = row.get(amount_column, 0)
            if isinstance(amount_raw, str):
                # Обрабатываем запятые как десятичные разделители (например: "1234,56" -> 1234.56)
                amount_str = str(amount_raw).replace(' ', '')
                # Заменяем запятую на точку для корректной конвертации
                amount_str = amount_str.replace(',', '.')
                try:
                    amount = float(amount_str)
                except ValueError:
                    amount = 0
            else:
                amount = float(amount_raw) if amount_raw else 0
            
            bank_operations.append({
                'paymentTypeName': payment_type,
                'amount': amount,
                'date': row.get(date_column, ''),
                'row_data': row,  # Сохраняем исходные данные строки
                'matched': False  # Флаг для отслеживания совпадений
            })
        
        # Сравниваем каждую операцию
        matched_operations = []
        unmatched_cash = []
        unmatched_bank = []
        
        # Проходим по каждой операции из банковского отчета
        for bank_op in bank_operations:
            found_match = False
            
            # Ищем совпадение в кассовых операциях
            for cash_op in cash_operations:
                if not cash_op['matched']:  # Проверяем только несовпавшие операции
                    # Сравниваем тип платежа и сумму
                    if (bank_op['paymentTypeName'] == cash_op['paymentTypeName'] and 
                        abs(bank_op['amount'] - cash_op['actualSum']) < 0.01):
                        
                        # Если есть колонка даты, сравниваем и её
                        if date_column and bank_op['date'] and cash_op['date']:
                            # Простое сравнение дат (можно улучшить)
                            bank_date = str(bank_op['date']).split('T')[0] if 'T' in str(bank_op['date']) else str(bank_op['date'])
                            cash_date = str(cash_op['date']).split('T')[0] if 'T' in str(cash_op['date']) else str(cash_op['date'])
                            if bank_date != cash_date:
                                continue
                        
                        # Нашли совпадение
                        matched_operations.append({
                            'cash_operation': cash_op,
                            'bank_operation': bank_op,
                            'cashAmount': cash_op['actualSum'],
                            'bankAmount': bank_op['amount'],
                            'difference': cash_op['actualSum'] - bank_op['amount'],
                            'status': 'match'
                        })
                        
                        # Помечаем операции как совпавшие
                        cash_op['matched'] = True
                        bank_op['matched'] = True
                        found_match = True
                        break
            
            # Если не нашли совпадение для банковской операции
            if not found_match:
                unmatched_bank.append(bank_op)
        
        # Собираем несовпавшие кассовые операции
        for cash_op in cash_operations:
            if not cash_op['matched']:
                unmatched_cash.append(cash_op)
        
        # Формируем итоговый результат
        comparison = []
        
        # Добавляем совпавшие операции
        for match in matched_operations:
            comparison.append({
                "paymentType": match['cash_operation']['paymentTypeName'],
                "cashAmount": match['cashAmount'],
                "bankAmount": match['bankAmount'],  # Уже в рублях
                "difference": match['difference'],
                "status": "match",
                "type": "matched"
            })
        
        # Добавляем несовпавшие кассовые операции
        for cash_op in unmatched_cash:
            comparison.append({
                "paymentType": cash_op['paymentTypeName'],
                "cashAmount": cash_op['actualSum'],
                "bankAmount": 0,
                "difference": cash_op['actualSum'],
                "status": "mismatch",
                "type": "cash_only"
            })
        
        # Добавляем несовпавшие банковские операции
        for bank_op in unmatched_bank:
            comparison.append({
                "paymentType": bank_op['paymentTypeName'],
                "cashAmount": 0,
                "bankAmount": bank_op['amount'],  # Уже в рублях
                "difference": -bank_op['amount'],
                "status": "mismatch",
                "type": "bank_only"
            })
        
        # Подсчитываем итоговые суммы
        total_cash_amount = sum(match['cashAmount'] for match in matched_operations)
        total_bank_amount = sum(match['bankAmount'] for match in matched_operations)
        total_difference = total_cash_amount - total_bank_amount
        
        return jsonify({
            "comparison": comparison,
            "summary": {
                "totalCashAmount": total_cash_amount,
                "totalBankAmount": total_bank_amount,
                "totalDifference": total_difference,
                "matchedCount": len(matched_operations),
                "unmatchedCashCount": len(unmatched_cash),
                "unmatchedBankCount": len(unmatched_bank)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Запуск приложения Cash Shifts")
    create_admin_user()  # Создаем администратора по умолчанию
    app.run(debug=False, host='0.0.0.0', port=5000)

