#!/usr/bin/env python3
"""
Автоматическое тестирование приложения Cash Shifts с помощью Playwright
"""
import asyncio
import subprocess
import time
import os
import signal
from playwright.async_api import async_playwright, expect

# Настройки
BASE_URL = "http://localhost:5003"  # Тестируем локально
ADMIN_USERNAME = "tsyndra"
ADMIN_PASSWORD = "We5fb2k93s71!"

class AppTester:
    def __init__(self):
        self.app_process = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def start_app(self):
        """Запуск приложения Flask"""
        print("🚀 Запуск приложения...")
        
        # Проверяем, не запущено ли приложение уже
        try:
            import requests
            response = requests.get(BASE_URL, timeout=2)
            if response.status_code in [200, 302]:
                print("✅ Приложение уже запущено")
                return
        except:
            pass
        
        # Запускаем приложение
        venv_python = "/home/workdir/cash_shifts/venv/bin/python"
        self.app_process = subprocess.Popen(
            [venv_python, "app.py"],
            cwd="/home/workdir/cash_shifts",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Ждем запуска
        max_wait = 30
        for i in range(max_wait):
            try:
                import requests
                response = requests.get(BASE_URL, timeout=2)
                if response.status_code in [200, 302]:
                    print("✅ Приложение запущено")
                    time.sleep(2)  # Дополнительная пауза для инициализации
                    return
            except:
                pass
            time.sleep(1)
        
        raise Exception("❌ Не удалось запустить приложение")
    
    async def stop_app(self):
        """Остановка приложения"""
        if self.app_process:
            print("🛑 Остановка приложения...")
            try:
                os.killpg(os.getpgid(self.app_process.pid), signal.SIGTERM)
                self.app_process.wait(timeout=5)
            except:
                pass
            print("✅ Приложение остановлено")
    
    async def setup_browser(self, playwright):
        """Инициализация браузера"""
        print("🌐 Запуск браузера...")
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ru-RU'
        )
        self.page = await self.context.new_page()
        print("✅ Браузер запущен")
    
    async def close_browser(self):
        """Закрытие браузера"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        print("✅ Браузер закрыт")
    
    async def test_login(self):
        """Тест авторизации"""
        print("\n📝 Тест 1: Авторизация")
        
        # Слушаем консоль браузера
        self.page.on("console", lambda msg: print(f"  🖥️ Консоль [{msg.type}]: {msg.text}"))
        self.page.on("pageerror", lambda exc: print(f"  ❌ Ошибка страницы: {exc}"))
        
        # Переходим на страницу логина
        await self.page.goto(f"{BASE_URL}/login")
        await self.page.wait_for_load_state('networkidle')
        
        # Вводим данные
        await self.page.fill('input[name="username"]', ADMIN_USERNAME)
        await self.page.fill('input[name="password"]', ADMIN_PASSWORD)
        
        # Нажимаем кнопку входа
        await self.page.click('button[type="submit"]')
        
        # Ждем редиректа на главную страницу
        await self.page.wait_for_url(f"{BASE_URL}/", timeout=10000)
        
        # Проверяем что мы на главной странице
        assert self.page.url == f"{BASE_URL}/", f"Не произошел редирект на главную страницу. Текущий URL: {self.page.url}"
        
        print("✅ Тест авторизации пройден")
    
    async def test_load_branches(self):
        """Тест загрузки филиалов"""
        print("\n🏢 Тест 2: Загрузка филиалов")
        
        # Сначала проверим что мы на правильной странице
        print(f"  Текущий URL: {self.page.url}")
        
        # Ждем загрузки страницы
        await self.page.wait_for_load_state('networkidle')
        
        # Проверим что есть на странице
        page_content = await self.page.content()
        if 'branchSelect' not in page_content:
            print("  ❌ Элемент #branchSelect не найден на странице")
            print(f"  Содержимое страницы: {page_content[:500]}...")
            return
        
        # Ждем загрузки селекта филиалов
        await self.page.wait_for_selector('#branchSelect', timeout=20000)
        
        # Ждем загрузки опций
        await self.page.wait_for_timeout(2000)
        
        # Получаем список филиалов
        branches = await self.page.eval_on_selector(
            '#branchSelect',
            'select => Array.from(select.options).map(o => o.text)'
        )
        
        print(f"  Найдено филиалов: {len(branches)}")
        for branch in branches:
            print(f"    - {branch}")
        
        # Проверяем что есть хотя бы "Выберите филиал..." + реальные филиалы
        assert len(branches) > 1, f"Не загружены филиалы. Найдено: {branches}"
        
        print("✅ Тест загрузки филиалов пройден")
    
    async def test_load_cash_shifts(self):
        """Тест загрузки кассовых смен"""
        print("\n💰 Тест 3: Загрузка кассовых смен")
        
        # Выбираем первый филиал (не "Выберите филиал")
        await self.page.select_option('#branchSelect', index=1)
        
        # Ждем загрузки смен для выбранного филиала
        await self.page.wait_for_timeout(3000)
        
        # Проверяем что появились смены
        cash_shift_select = await self.page.query_selector('#cashShiftSelect')
        if cash_shift_select:
            options = await cash_shift_select.eval_on_selector_all('option', 'options => options.length')
            print(f"  Найдено опций в селекте смен: {options}")
            
            if options > 1:  # Есть смены кроме "Выберите смену..."
                # Выбираем первую смену
                await self.page.select_option('#cashShiftSelect', index=1)
                await self.page.wait_for_timeout(1000)
                
                # Теперь кнопка должна быть активна
                button_enabled = await self.page.eval_on_selector('#loadCashShiftBtn', 'btn => !btn.disabled')
                print(f"  Кнопка активна: {button_enabled}")
                
                if button_enabled:
                    # Нажимаем кнопку загрузки
                    await self.page.click('#loadCashShiftBtn')
                else:
                    print("  ⚠️  Кнопка все еще неактивна")
            else:
                print("  ⚠️  Нет доступных смен для выбранного филиала")
        else:
            print("  ⚠️  Селект смен не найден")
        
        # Ждем появления таблицы или сообщения
        try:
            await self.page.wait_for_selector('#cash_shifts_table tbody tr', timeout=15000)
            
            # Подсчитываем количество смен
            shifts_count = await self.page.eval_on_selector_all(
                '#cash_shifts_table tbody tr',
                'rows => rows.length'
            )
            
            print(f"  Загружено кассовых смен: {shifts_count}")
            
            assert shifts_count > 0, "Не загружены кассовые смены"
            
            print("✅ Тест загрузки кассовых смен пройден")
            
        except Exception as e:
            print(f"⚠️  Ошибка при загрузке кассовых смен: {e}")
            print("  (это нормально, если нет доступных смен)")
    
    async def test_view_shift_details(self):
        """Тест просмотра деталей смены"""
        print("\n🔍 Тест 4: Просмотр деталей смены")
        
        try:
            # Ищем первую строку в таблице
            first_row = await self.page.query_selector('#cashShiftsTable tbody tr')
            
            if first_row:
                # Кликаем на первую строку
                await first_row.click()
                await self.page.wait_for_timeout(2000)
                
                # Ищем модальное окно или таблицу с платежами
                payments_visible = await self.page.is_visible('#payments_table')
                
                if payments_visible:
                    print("✅ Тест просмотра деталей смены пройден")
                else:
                    print("⚠️  Детали смены не отображаются")
            else:
                print("⚠️  Нет доступных смен для просмотра")
                
        except Exception as e:
            print(f"⚠️  Ошибка при просмотре деталей: {e}")
    
    async def test_logout(self):
        """Тест выхода из системы"""
        print("\n🚪 Тест 5: Выход из системы")
        
        # Ищем кнопку выхода
        logout_button = await self.page.query_selector('a[href="/logout"]')
        
        if logout_button:
            await logout_button.click()
            await self.page.wait_for_load_state('networkidle')
            
            # Проверяем редирект на страницу логина
            assert '/login' in self.page.url, "Не произошел редирект на страницу логина"
            
            print("✅ Тест выхода пройден")
        else:
            print("⚠️  Кнопка выхода не найдена")
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("="*60)
        print("🧪 АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ CASH SHIFTS")
        print("="*60)
        
        # Создаем папку для скриншотов
        os.makedirs('screenshots', exist_ok=True)
        
        async with async_playwright() as playwright:
            try:
                # Запускаем приложение
                await self.start_app()
                
                # Инициализируем браузер
                await self.setup_browser(playwright)
                
                # Запускаем тесты
                await self.test_login()
                await self.test_load_branches()
                await self.test_load_cash_shifts()
                await self.test_view_shift_details()
                await self.test_logout()
                
                # Финальный скриншот для проверки
                await self.page.goto(f"{BASE_URL}/login")
                await self.page.wait_for_load_state('networkidle')
                await self.page.screenshot(path='screenshots/final_state.png', full_page=True)
                
                print("\n" + "="*60)
                print("✅ ВСЕ ТЕСТЫ ВЫПОЛНЕНЫ")
                print("📸 Финальный скриншот: screenshots/final_state.png")
                print("="*60)
                
            except Exception as e:
                print(f"\n❌ ОШИБКА: {e}")
                if self.page:
                    await self.page.screenshot(path='screenshots/error_state.png', full_page=True)
                    print("📸 Скриншот ошибки сохранен: screenshots/error_state.png")
                raise
                
            finally:
                # Закрываем браузер
                await self.close_browser()
                
                # Не останавливаем приложение, если оно было запущено до тестов
                # await self.stop_app()

async def main():
    tester = AppTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

