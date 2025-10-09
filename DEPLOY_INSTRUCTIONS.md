# Инструкции по деплою изменений в продакшн

## Текущая ситуация

- ✅ **Новая версия** приложения запущена на порту **5003**
- ❌ **Старая версия** все еще работает на порту **5000** (под root)
- ❌ **Nginx** проксирует запросы на старую версию (порт 5000)

## Что нужно сделать для деплоя

### 1. Остановить старые процессы (требует sudo)

```bash
# Найти и остановить старые процессы
sudo pkill -f "python3 app.py"
sudo pkill -f "python.*cash"

# Проверить, что процессы остановлены
ps aux | grep "python.*app.py" | grep -v grep
```

### 2. Обновить конфигурацию Nginx (требует sudo)

```bash
# Создать новую конфигурацию
sudo tee /etc/nginx/sites-available/cashshifts-updated << 'EOF'
server {
    listen 80;
    server_name cashshifts.tsyndra.ru;

    location / {
        proxy_pass http://127.0.0.1:5003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/cash-shifts/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Активировать новую конфигурацию
sudo ln -sf /etc/nginx/sites-available/cashshifts-updated /etc/nginx/sites-enabled/

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl reload nginx
```

### 3. Запустить новую версию как сервис (требует sudo)

```bash
# Создать systemd сервис для новой версии
sudo tee /etc/systemd/system/cashshifts-new.service << 'EOF'
[Unit]
Description=Cash Shifts Application (New Version)
After=network.target

[Service]
Type=simple
User=tsyndra
Group=tsyndra
WorkingDirectory=/home/workdir/cash_shifts
Environment=PATH=/home/workdir/cash_shifts/venv/bin
ExecStart=/home/workdir/cashshifts/venv/bin/python3 app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузить systemd и запустить сервис
sudo systemctl daemon-reload
sudo systemctl enable cashshifts-new
sudo systemctl start cashshifts-new

# Проверить статус
sudo systemctl status cashshifts-new
```

## Альтернативный способ (если нет sudo)

Если нет доступа к sudo, можно:

1. **Оставить приложение на порту 5003** как есть
2. **Попросить администратора** обновить Nginx конфигурацию
3. **Или использовать другой порт** (например, 8080) и настроить проксирование

## Проверка результата

После выполнения команд:

1. **Проверить сайт**: https://cashshifts.tsyndra.ru
2. **Убедиться, что**:
   - ❌ Нет операций "Внесение" и "Выдача"
   - ✅ Статус "Принят" вместо "Ошибка"
   - ✅ Показывается информация о количестве загруженных операций

## Текущие исправления

- ✅ **Исключены операции внесения и выдачи** из отчетов
- ✅ **Статус "ACCEPTED" переводится как "Принят"**
- ✅ **Добавлена информация** о количестве загруженных операций
- ✅ **Приложение работает на порту 5003**

## Команды для проверки

```bash
# Проверить, что новая версия работает
curl -s http://localhost:5003 | head -5

# Проверить процессы
ps aux | grep "python.*app.py" | grep -v grep

# Проверить порты
ss -tlnp | grep :5003
```
