# 🚀 Quick Start - Быстрый старт Cash Shifts

## 1️⃣ Первый запуск

```bash
# Переходим в директорию проекта
cd /home/workdir/cash_shifts

# Активируем виртуальное окружение (если нужно)
source venv/bin/activate

# Запускаем приложение
python app.py
```

Откройте в браузере: **http://localhost:5003**

**Логин:** admin  
**Пароль:** CashShifts2024!

---

## 2️⃣ Запуск тестов

```bash
./run_tests.sh
```

Скриншоты сохраняются в `screenshots/`

---

## 3️⃣ Деплой на продакшн

### С тестами (рекомендуется):
```bash
./deploy_to_production.sh
```

### Без тестов (быстро):
```bash
./quick_deploy.sh
```

---

## 4️⃣ Автоматический деплой

```bash
# Настроить один раз
./setup_auto_deploy.sh

# Теперь деплой происходит автоматически после:
git commit
git pull
```

---

## 5️⃣ Основные команды

| Команда | Описание |
|---------|----------|
| `python app.py` | Запуск приложения |
| `./run_tests.sh` | Запуск тестов |
| `./deploy_to_production.sh` | Полный деплой с тестами |
| `./quick_deploy.sh` | Быстрый деплой без тестов |
| `./setup_auto_deploy.sh` | Настройка автодеплоя |

---

## 6️⃣ Файлы документации

- **README.md** - Полная документация проекта
- **README_TESTING.md** - Руководство по тестированию
- **DEPLOY.md** - Инструкция по деплою
- **CHANGELOG.md** - История изменений
- **QUICKSTART.md** - Этот файл

---

## 🆘 Помощь

### Не запускается приложение?
```bash
# Проверьте логи
tail -f cash_shifts.log

# Проверьте процессы
ps aux | grep app.py

# Убейте старые процессы
pkill -f "python.*app.py"
```

### Тесты не работают?
```bash
# Проверьте Playwright
./venv/bin/playwright --version

# Переустановите браузеры
./venv/bin/playwright install chromium
```

### Деплой не работает?
```bash
# Посмотрите логи деплоя
cat app.log

# Проверьте скрипты
ls -la *.sh

# Дайте права на выполнение
chmod +x *.sh
```

---

**Продакшн:** https://cashshifts.tsyndra.ru

