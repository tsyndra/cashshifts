#!/bin/bash

echo "🚀 Обновление продакшн Cash Shifts..."

# Копируем файлы
cp app.py models.py main.py requirements.txt /var/www/cash-shifts/
cp -r templates/ static/ /var/www/cash-shifts/

# Устанавливаем зависимости
python3 -m pip install -r requirements.txt --user

# Останавливаем старые процессы (если можем)
pkill -f "python.*app.py" 2>/dev/null || echo "Не удалось остановить процессы"

# Запускаем новую версию
cd /var/www/cash-shifts
nohup python3 app.py > app.log 2>&1 &

echo "✅ Обновление завершено"
echo "🌐 Проверяйте: https://cashshifts.tsyndra.ru"
