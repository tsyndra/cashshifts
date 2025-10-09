#!/bin/bash
# Скрипт для запуска приложения без sudo

cd /home/workdir/cash_shifts

# Активируем виртуальное окружение, если есть
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запускаем приложение
nohup python3 app.py > /tmp/cashshifts.log 2>&1 &

echo "Приложение запущено на порту 5003"
echo "PID: $!"
echo "Логи: /tmp/cashshifts.log"

