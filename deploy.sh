#!/bin/bash

# Скрипт автоматического деплоя Cash Shifts на продакшн
# Использование: ./deploy.sh

set -e  # Остановить при ошибке

echo "🚀 Начинаем деплой Cash Shifts на продакшн..."

# Переходим в директорию проекта
cd /home/workdir/cash_shifts

# Проверяем, что мы в правильной директории
if [ ! -f "app.py" ]; then
    echo "❌ Ошибка: app.py не найден. Убедитесь, что вы в правильной директории."
    exit 1
fi

echo "📂 Текущая директория: $(pwd)"

# Останавливаем старые процессы app.py
echo "🛑 Останавливаем старые процессы..."
pkill -f "python.*app.py" || true
sleep 2

# Активируем виртуальное окружение
echo "🐍 Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем зависимости (если изменились)
echo "📦 Проверяем зависимости..."
pip install -r requirements.txt --quiet

# Проверяем синтаксис Python
echo "🔍 Проверяем синтаксис приложения..."
python -m py_compile app.py
python -m py_compile models.py
python -m py_compile main.py
echo "✅ Синтаксис корректен"

# Создаем папки если не существуют
mkdir -p uploads
mkdir -p instance

# Запускаем приложение в фоне
echo "🚀 Запускаем приложение..."
nohup python app.py > app.log 2>&1 &
APP_PID=$!

# Ждем запуска
echo "⏳ Ждем запуска приложения..."
sleep 5

# Проверяем, что приложение запустилось
if ps -p $APP_PID > /dev/null; then
    echo "✅ Приложение успешно запущено (PID: $APP_PID)"
    
    # Проверяем доступность
    if curl -s http://localhost:5000/login > /dev/null; then
        echo "✅ Приложение отвечает на запросы"
    else
        echo "⚠️  Приложение запущено, но не отвечает на запросы"
    fi
else
    echo "❌ Ошибка запуска приложения"
    echo "📋 Логи:"
    tail -20 app.log
    exit 1
fi

echo "🎉 Деплой завершен успешно!"
echo "🌐 Приложение доступно по адресу: https://cashshifts.tsyndra.ru"
echo "📊 PID процесса: $APP_PID"
echo "📝 Логи: tail -f /home/workdir/cash_shifts/app.log"
