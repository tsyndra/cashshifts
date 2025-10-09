#!/bin/bash

# Простой ручной деплой для Cash Shifts
# Использование: ./manual_deploy.sh

echo "🚀 Ручной деплой Cash Shifts на продакшн..."

# Переходим в директорию проекта
cd /home/workdir/cash_shifts

# Копируем обновленные файлы в продакшн
echo "📁 Копируем файлы в продакшн..."
cp app.py models.py main.py requirements.txt /var/www/cash-shifts/
cp -r templates/ static/ /var/www/cash-shifts/

# Проверяем, что файлы скопировались
echo "✅ Файлы скопированы:"
ls -la /var/www/cash-shifts/app.py

# Перезапускаем сервис (если есть права)
echo "🔄 Перезапускаем сервис..."
systemctl restart cash-shifts 2>/dev/null || echo "⚠️  Нет прав для перезапуска сервиса"

# Ждем запуска
sleep 3

# Проверяем статус
echo "🔍 Проверяем статус..."
systemctl status cash-shifts --no-pager | head -5

# Проверяем доступность сайта
echo "🌐 Проверяем продакшн сайт..."
curl -s https://cashshifts.tsyndra.ru | head -5

echo "🎉 Ручной деплой завершен!"
echo "🌐 Сайт: https://cashshifts.tsyndra.ru"
