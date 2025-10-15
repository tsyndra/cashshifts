#!/bin/bash

echo "🚀 Деплой Cash Shifts на продакшн..."

# Останавливаем старый процесс
echo "🛑 Останавливаем старый процесс..."
pkill -f "python.*app.py" || true
sleep 2

# Копируем файлы на продакшн (если нужно)
echo "📁 Копируем файлы..."
# cp -r /home/workdir/cash_shifts/* /path/to/production/ || true

# Запускаем новый процесс в фоне
echo "▶️ Запускаем новый процесс..."
cd /home/workdir/cash_shifts
nohup python3 app.py > app.log 2>&1 &
sleep 3

# Проверяем, что процесс запустился
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ Процесс запущен успешно!"
    echo "📊 PID: $(pgrep -f 'python.*app.py')"
    echo "📝 Логи: /home/workdir/cash_shifts/app.log"
else
    echo "❌ Процесс не запустился!"
    echo "📝 Проверь логи: /home/workdir/cash_shifts/app.log"
fi

echo "🌐 Приложение доступно по адресу: https://cashshifts.tsyndra.ru"
echo "🔧 Для остановки: pkill -f 'python.*app.py'"