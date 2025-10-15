# 🔐 Авторизация через iiko API

## Концепция

Cash Shifts теперь использует **прямую авторизацию через iiko API** вместо локальной базы данных пользователей.

## Как это работает

```
1. Пользователь вводит логин и пароль
   ↓
2. Система вычисляет SHA1(пароль)
   ↓
3. Запрос к iiko API: /auth?login=username&pass=sha1
   ↓
4. iiko API возвращает токен (если учетные данные верны)
   ↓
5. Пользователь авторизован ✅
   ↓
6. Логин и SHA1 сохраняются в сессии
   ↓
7. Для всех запросов используются эти же данные
```

## Преимущества

✅ **Нет дублирования** - один источник истины (iiko)  
✅ **Автосинхронизация** - изменения паролей сразу работают  
✅ **Простота** - не нужна локальная БД пользователей  
✅ **Безопасность** - пароли не хранятся, только SHA1  
✅ **Единая точка** - управление доступом в iiko  

## Вход в систему

Используйте свои учетные данные из **iiko**:

```
Логин: ваш_логин_из_iiko
Пароль: ваш_пароль_из_iiko
```

Например, если в iiko у вас:
- Логин: `tsyndra`
- Пароль: `We5fb2k93s71!`

То используйте их же для входа в Cash Shifts.

## Технические детали

### Файлы

- **`auth.py`** - модуль авторизации через iiko API
- **`app.py`** - основное приложение (обновлено)
- **`models.py`** - больше не используется ❌

### Процесс авторизации

1. **Login Route** (`/login`):
   ```python
   success, token, error = authenticate_with_iiko(username, password)
   ```

2. **Функция authenticate_with_iiko**:
   - Вычисляет SHA1 от пароля
   - Делает запрос к iiko API
   - Возвращает результат

3. **Сохранение в сессии**:
   ```python
   session['username'] = username
   session['password_sha1'] = password_sha1
   ```

4. **Получение токенов для запросов**:
   ```python
   token = get_token_for_user(username, password_sha1, branch_id)
   ```

### User Loader

```python
@login_manager.user_loader
def load_user(user_id):
    if 'username' in session and 'password_sha1' in session:
        if session['username'] == user_id:
            return User(username=session['username'], 
                       password_sha1=session['password_sha1'])
    return None
```

### User Model

Простой класс без БД:

```python
class User(UserMixin):
    def __init__(self, username, password_sha1):
        self.id = username
        self.username = username
        self.password_sha1 = password_sha1
```

## Управление доступом

**Вопрос:** Как добавить/удалить пользователя?  
**Ответ:** Через **iiko** - добавьте/удалите пользователя там

**Вопрос:** Как изменить пароль?  
**Ответ:** Через **iiko** - измените там, сразу заработает

**Вопрос:** Как ограничить доступ?  
**Ответ:** Через **iiko** - удалите/деактивируйте пользователя

## Безопасность

- ✅ Пароли передаются в открытом виде только при входе (HTTPS)
- ✅ В сессии хранится только SHA1
- ✅ Каждый запрос к API использует токен
- ✅ Токены временные (по политике iiko)
- ✅ Нет локального хранения паролей

## Что изменилось

### Удалено

- ❌ Локальная БД пользователей (`cash_shifts.db`)
- ❌ `models.py` (больше не используется)
- ❌ Админ-панель управления пользователями
- ❌ Функция `create_admin_user()`
- ❌ Routes: `/admin/users/*`

### Добавлено

- ✅ `auth.py` - модуль авторизации через iiko
- ✅ Функция `authenticate_with_iiko()`
- ✅ Функция `get_token_for_user()`
- ✅ Хранение учетных данных в сессии

### Изменено

- 🔄 `/login` - теперь проверяет через iiko API
- 🔄 `/logout` - очищает сессию
- 🔄 `get_user_auth_token()` - берет данные из сессии
- 🔄 `load_user()` - загружает из сессии

## Примеры

### Авторизация

```python
# Пользователь вводит:
username = "tsyndra"
password = "We5fb2k93s71!"

# Система делает:
success, token, error = authenticate_with_iiko(username, password)

# Если success = True:
session['username'] = 'tsyndra'
session['password_sha1'] = 'cb084e5e5f9bfc6cf6c705a382817739c8aebeac'
```

### Получение токена для запроса

```python
# При запросе к API:
branch_id = "novovatutinskaya"
token = get_token_for_user(
    username=session['username'],
    password_sha1=session['password_sha1'],
    branch_id=branch_id
)

# Используем токен:
response = requests.get(f"{base_url}/api/...", params={'key': token})
```

## Миграция

Если у вас были локальные пользователи - они больше не нужны.

Просто используйте учетные данные из iiko.

## Troubleshooting

**Не могу войти:**
- Проверьте логин и пароль в iiko
- Убедитесь что пользователь активен в iiko
- Проверьте доступность iiko API

**Ошибка "Нет данных пользователя в сессии":**
- Перезайдите в систему
- Очистите cookies браузера

**Токен не работает:**
- Возможно истек срок действия
- Перезайдите в систему

---

**Продакшн:** https://cashshifts.tsyndra.ru  
**Документация:** AUTH_README.md

