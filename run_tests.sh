#!/bin/bash
# Скрипт для запуска автоматических тестов

cd /home/workdir/cash_shifts

echo "🧪 Запуск автоматических тестов с Playwright..."
echo ""

# Активируем виртуальное окружение и запускаем тесты
./venv/bin/python test_playwright.py

echo ""
echo "✅ Тестирование завершено!"

