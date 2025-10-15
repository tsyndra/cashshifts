#!/bin/bash
# Скрипт для настройки автоматического деплоя через Git hooks

PROJECT_DIR="/home/workdir/cash_shifts"
cd "$PROJECT_DIR"

echo "======================================================"
echo "⚙️  НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ"
echo "======================================================"
echo ""

# Создаем директорию для git hooks если ее нет
if [ ! -d ".git" ]; then
    echo "❌ Ошибка: Это не git репозиторий"
    echo "Сначала инициализируйте git: git init"
    exit 1
fi

mkdir -p .git/hooks

# Создаем post-commit hook
echo "📝 Создание post-commit hook..."

cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Git hook: автоматический деплой после коммита

echo ""
echo "🔄 Обнаружены новые изменения в коде"
echo "Запускаем автоматический деплой..."
echo ""

# Запускаем скрипт деплоя
./deploy_to_production.sh

EOF

# Делаем hook исполняемым
chmod +x .git/hooks/post-commit

echo "✅ post-commit hook создан"

# Создаем post-merge hook (срабатывает при git pull)
echo "📝 Создание post-merge hook..."

cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
# Git hook: автоматический деплой после git pull

echo ""
echo "🔄 Обнаружены изменения после git pull"
echo "Запускаем автоматический деплой..."
echo ""

# Запускаем скрипт деплоя
./deploy_to_production.sh

EOF

# Делаем hook исполняемым
chmod +x .git/hooks/post-merge

echo "✅ post-merge hook создан"

echo ""
echo "======================================================"
echo "✅ АВТОМАТИЧЕСКИЙ ДЕПЛОЙ НАСТРОЕН!"
echo "======================================================"
echo ""
echo "Теперь деплой будет запускаться автоматически:"
echo "  • После каждого git commit"
echo "  • После каждого git pull"
echo ""
echo "Для ручного деплоя используйте:"
echo "  ./deploy_to_production.sh"
echo ""
echo "Для отключения автодеплоя:"
echo "  rm .git/hooks/post-commit"
echo "  rm .git/hooks/post-merge"
echo ""

