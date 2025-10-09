#!/bin/bash
# Автоматический перезапуск приложения (без sudo)

cd /home/workdir/cash_shifts

# Убиваем только наши процессы (не root)
pkill -u tsyndra -f "python.*app.py" 2>/dev/null

# Ждем завершения
sleep 2

# Запускаем новую версию
nohup python3 app.py > /tmp/cashshifts.log 2>&1 &

echo "✅ Приложение перезапущено"
echo "📍 Порт: 5003"
echo "📝 Логи: /tmp/cashshifts.log"
echo "🔍 PID: $!"

# Проверяем, что запустилось
sleep 2
if ss -tln | grep -q ":5003"; then
    echo "✅ Приложение работает на порту 5003"
else
    echo "❌ Ошибка запуска, проверьте логи: tail -f /tmp/cashshifts.log"
fi

