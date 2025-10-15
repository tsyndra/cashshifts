#!/usr/bin/env python3
"""
Автоматический деплой Cash Shifts на продакшн
Вызывается после каждого git commit для обновления продакшн версии
"""

import subprocess
import sys
import time
import requests
import os
from pathlib import Path

def run_command(command, cwd=None, capture_output=True):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=capture_output, 
            text=True, 
            check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {command}")
        print(f"Код ошибки: {e.returncode}")
        if capture_output:
            print(f"Вывод: {e.stdout}")
            print(f"Ошибка: {e.stderr}")
        return None

def check_app_health():
    """Проверяет доступность приложения"""
    try:
        response = requests.get('http://localhost:5004/login', timeout=10)
        return response.status_code == 200
    except:
        return False

def deploy_to_production():
    """Основная функция деплоя"""
    print("🚀 Начинаем автоматический деплой Cash Shifts на продакшн...")
    
    # Переходим в директорию проекта
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print(f"📂 Рабочая директория: {project_dir}")
    
    # Останавливаем старые процессы
    print("🛑 Останавливаем старые процессы...")
    run_command("pkill -f 'python.*app.py'", capture_output=False)
    time.sleep(2)
    
    # Активируем виртуальное окружение и запускаем
    print("🐍 Активируем виртуальное окружение и запускаем приложение...")
    
    # Запускаем приложение в фоне
    venv_python = project_dir / "venv" / "bin" / "python"
    if not venv_python.exists():
        print("❌ Виртуальное окружение не найдено!")
        return False
    
    # Запускаем приложение
    cmd = f"nohup {venv_python} app.py > app.log 2>&1 &"
    run_command(cmd, capture_output=False)
    
    # Ждем запуска
    print("⏳ Ждем запуска приложения...")
    time.sleep(5)
    
    # Проверяем здоровье приложения
    print("🔍 Проверяем доступность приложения...")
    max_retries = 10
    for i in range(max_retries):
        if check_app_health():
            print("✅ Приложение успешно запущено и отвечает на запросы")
            print("🌐 Доступно по адресу: https://cashshifts.tsyndra.ru")
            return True
        else:
            print(f"⏳ Попытка {i+1}/{max_retries}: ждем запуска...")
            time.sleep(3)
    
    print("❌ Приложение не отвечает после запуска")
    print("📋 Последние строки логов:")
    try:
        with open('app.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.strip()}")
    except:
        print("  Логи недоступны")
    
    return False

if __name__ == "__main__":
    success = deploy_to_production()
    sys.exit(0 if success else 1)
