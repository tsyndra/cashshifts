#!/bin/bash
# Быстрый деплой БЕЗ тестов (используйте только если уверены)

PROJECT_DIR="/home/workdir/cash_shifts"
cd "$PROJECT_DIR"

echo "⚡ БЫСТРЫЙ ДЕПЛОЙ (БЕЗ ТЕСТОВ)"
echo "======================================================"
echo ""

./venv/bin/python auto_deploy.py

echo ""
echo "✅ Готово!"

