# Changelog - История изменений Cash Shifts

## [Текущая версия] - 2025-10-15

### ✨ Добавлено
- **Автоматическое тестирование Playwright**
  - E2E тесты для всех основных функций
  - Автоматические скриншоты при ошибках
  - Скрипт `run_tests.sh` для быстрого запуска

- **Автоматический деплой**
  - Полный деплой с тестированием: `deploy_to_production.sh`
  - Быстрый деплой без тестов: `quick_deploy.sh`
  - Git hooks для автодеплоя после commit/pull
  - Скрипт настройки: `setup_auto_deploy.sh`

- **Документация**
  - `README_TESTING.md` - руководство по тестированию
  - `DEPLOY.md` - подробная инструкция по деплою
  - `CHANGELOG.md` - история изменений

### 🔧 Исправлено
- Исправлен порт в auto_deploy.py (5000 → 5003)
- Обновлен README.md с актуальным портом
- Удалены устаревшие шаблоны (index.html, index_new.html)

### 🗑️ Удалено
- Старые тестовые файлы (test_*.py - 11 штук)
- Устаревшие deployment скрипты
- Временные файлы (логи, скриншоты, JSON)
- __pycache__ директории
- Лишние deployment инструкции

### 📦 Зависимости
- Добавлен Playwright 1.55.0
- Добавлен pytest-playwright 0.7.1

### 🏗️ Структура проекта
```
cash_shifts/
├── app.py                      # Основное приложение
├── models.py                   # Модели БД
├── main.py                     # iiko API
├── auto_deploy.py             # Скрипт деплоя
├── requirements.txt           # Зависимости
│
├── test_playwright.py         # Автотесты
├── run_tests.sh              # Запуск тестов
│
├── deploy_to_production.sh   # Полный деплой
├── quick_deploy.sh           # Быстрый деплой
├── setup_auto_deploy.sh      # Настройка автодеплоя
│
├── README.md                 # Основная документация
├── README_TESTING.md         # Документация тестов
├── DEPLOY.md                 # Инструкция по деплою
├── CHANGELOG.md              # История изменений
│
├── templates/                # HTML шаблоны
│   ├── base.html
│   ├── login.html
│   ├── index_final.html
│   └── admin.html
│
├── static/                   # Статические файлы
├── venv/                     # Виртуальное окружение
└── screenshots/              # Скриншоты тестов
```

---

## Workflow разработки

### Разработка с автодеплоем:
```bash
# 1. Вносим изменения
nano app.py

# 2. Коммитим - деплой происходит автоматически!
git add .
git commit -m "Описание изменений"
```

### Разработка с ручным деплоем:
```bash
# 1. Вносим изменения
nano app.py

# 2. Деплоим вручную
./deploy_to_production.sh
```

---

## Контакты

- **Продакшн:** https://cashshifts.tsyndra.ru
- **Автор:** tsyndra

