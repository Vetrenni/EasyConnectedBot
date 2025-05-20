#!/usr/bin/env python
"""
Скрипт для автоматического перезапуска и проверки системы
Запускайте этот скрипт через cron каждые 5-10 минут
"""
import os
import sys
import time
import json
import logging
import subprocess
import signal
import psutil
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_restart.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auto_restart")

# Получаем абсолютный путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Файл PID для бота
BOT_PID_FILE = os.path.join(BASE_DIR, "bot.pid")

# Файл команд бота
BOT_COMMANDS_FILE = os.path.join(BASE_DIR, "bot_commands.json")


def is_bot_running():
    """
    Проверяет, запущен ли бот

    :return: True если бот запущен, иначе False
    """
    if not os.path.exists(BOT_PID_FILE):
        logger.warning(f"Файл PID бота не найден: {BOT_PID_FILE}")
        return False

    try:
        with open(BOT_PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Проверяем, существует ли процесс
        if psutil.pid_exists(pid):
            process = psutil.Process(pid)

            # Проверяем, что процесс - это Python и в его командной строке есть main.py
            if 'python' in process.name().lower() and 'main.py' in ' '.join(process.cmdline()):
                return True
            else:
                logger.warning(f"Процесс с PID {pid} не является ботом")
        else:
            logger.warning(f"Процесс с PID {pid} не существует")

        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса бота: {e}")
        return False


def start_bot():
    """
    Запускает бота

    :return: True если бот успешно запущен, иначе False
    """
    logger.info("Запуск бота...")

    try:
        # Запускаем бота с текущей директорией в качестве рабочей
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "main.py")],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Даем процессу время на инициализацию
        time.sleep(5)

        # Проверяем, запустился ли процесс
        if process.poll() is None:
            logger.info(f"Бот успешно запущен с PID {process.pid}")

            # Сохраняем PID в файл
            with open(BOT_PID_FILE, 'w') as f:
                f.write(str(process.pid))

            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Бот не запустился. Код выхода: {process.returncode}")
            logger.error(f"Стандартный вывод: {stdout.decode('utf-8', errors='ignore')}")
            logger.error(f"Ошибки: {stderr.decode('utf-8', errors='ignore')}")
            return False
            except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            return False

        def stop_bot():
            """
            Останавливает бота

            :return: True если бот успешно остановлен, иначе False
            """
            if not os.path.exists(BOT_PID_FILE):
                logger.warning(f"Файл PID бота не найден: {BOT_PID_FILE}")
                return True  # Считаем, что бот и так не запущен

            try:
                with open(BOT_PID_FILE, 'r') as f:
                    pid = int(f.read().strip())

                if psutil.pid_exists(pid):
                    # Отправляем сигнал SIGTERM для корректного завершения
                    os.kill(pid, signal.SIGTERM)

                    # Ждем завершения процесса
                    for i in range(10):  # Ждем до 10 секунд
                        if not psutil.pid_exists(pid):
                            break
                        time.sleep(1)

                    # Если процесс все еще существует, отправляем SIGKILL
                    if psutil.pid_exists(pid):
                        os.kill(pid, signal.SIGKILL)
                        time.sleep(1)

                    logger.info(f"Бот с PID {pid} остановлен")
                else:
                    logger.warning(f"Процесс с PID {pid} не существует")

                # Удаляем файл PID
                os.remove(BOT_PID_FILE)
                return True
            except Exception as e:
                logger.error(f"Ошибка при остановке бота: {e}")
                return False

        def check_bot_commands():
            """
            Проверяет файл команд бота

            :return: (all_ok, командное_сообщение)
            """
            if not os.path.exists(BOT_COMMANDS_FILE):
                return False, "Файл команд бота не существует"

            try:
                # Проверяем размер файла
                size = os.path.getsize(BOT_COMMANDS_FILE)
                if size == 0:
                    # Создаем пустой список команд
                    with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    return True, "Создан пустой список команд"

                # Проверяем содержимое файла
                with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        # Создаем пустой список команд
                        with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                            json.dump([], f)
                        return True, "Создан пустой список команд"

                    try:
                        commands = json.loads(content)

                        if not isinstance(commands, list):
                            # Исправляем структуру файла
                            with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                                json.dump([], f)
                            return False, "Структура файла команд исправлена (не список)"

                        # Проверяем зависшие команды
                        pending_count = 0
                        fixed_timestamp = 0
                        now = time.time()

                        for cmd in commands:
                            if cmd.get('status') == 'pending':
                                pending_count += 1

                                # Проверяем возраст команды
                                try:
                                    cmd_time = float(cmd.get('timestamp', '0'))
                                    if now - cmd_time > 300:  # 5 минут
                                        cmd['timestamp'] = '0'
                                        fixed_timestamp += 1
                                except:
                                    cmd['timestamp'] = '0'
                                    fixed_timestamp += 1

                        # Если есть исправленные метки времени, сохраняем файл
                        if fixed_timestamp > 0:
                            with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                                json.dump(commands, f, ensure_ascii=False, indent=4)
                            return True, f"Исправлено {fixed_timestamp} меток времени для зависших команд"

                        return True, f"Файл команд в порядке. Ожидающих команд: {pending_count}"
                    except json.JSONDecodeError:
                        # Создаем резервную копию поврежденного файла
                        backup_file = f"{BOT_COMMANDS_FILE}.bad.{int(time.time())}"
                        os.rename(BOT_COMMANDS_FILE, backup_file)

                        # Создаем новый пустой файл
                        with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                            json.dump([], f)

                        return False, f"Файл команд был поврежден и восстановлен. Резервная копия: {backup_file}"
            except Exception as e:
                logger.error(f"Ошибка при проверке файла команд: {e}")
                return False, f"Ошибка при проверке файла команд: {e}"

        def sync_files():
            """
            Синхронизирует файлы между ботом и админкой

            :return: (success, message)
            """
            try:
                # Импортируем функции из модуля синхронизации
                sys.path.append(os.path.join(BASE_DIR, 'admin'))
                from sync_bot import sync_all_from_bot_to_admin, sync_all_from_admin_to_bot

                # Синхронизируем файлы
                bot_to_admin = sync_all_from_bot_to_admin()
                admin_to_bot = sync_all_from_admin_to_bot()

                return True, f"Синхронизация завершена: {bot_to_admin} файлов из бота в админку, {admin_to_bot} файлов из админки в бота"
            except Exception as e:
                logger.error(f"Ошибка при синхронизации файлов: {e}")
                return False, f"Ошибка при синхронизации файлов: {e}"

        def perform_system_check():
            """
            Выполняет полную проверку системы

            :return: Список проблем
            """
            issues = []

            # Проверяем файлы синхронизации
            sync_files_to_check = [
                'admins.json',
                'global_admins.json',
                'allowed_users.json',
                'streamers.json',
                'user_stats.json',
                'user_settings.json',
                'chats.json',
                'bot_commands.json'
            ]

            for filename in sync_files_to_check:
                # Проверяем файл в корневой директории
                file_path = os.path.join(BASE_DIR, filename)
                if not os.path.exists(file_path):
                    issues.append(f"Файл {filename} отсутствует в директории бота")
                elif os.path.getsize(file_path) == 0:
                    issues.append(f"Файл {filename} в директории бота пуст")

                # Проверяем файл в директории админки
                admin_file_path = os.path.join(BASE_DIR, 'admin', filename)
                if not os.path.exists(admin_file_path):
                    issues.append(f"Файл {filename} отсутствует в директории админки")
                elif os.path.getsize(admin_file_path) == 0:
                    issues.append(f"Файл {filename} в директории админки пуст")

            # Проверяем работоспособность бота
            if not is_bot_running():
                issues.append("Бот не запущен")

            # Проверяем файл команд
            bot_commands_ok, message = check_bot_commands()
            if not bot_commands_ok:
                issues.append(f"Проблема с файлом команд бота: {message}")

            return issues

        def restart_if_needed():
            """
            Перезапускает бота, если он не запущен или если есть проблемы
            """
            logger.info("Проверка необходимости перезапуска...")

            # Проверяем, запущен ли бот
            bot_running = is_bot_running()

            if not bot_running:
                logger.warning("Бот не запущен. Выполняю запуск.")
                start_bot()
                return True

            # Проверяем файл команд
            bot_commands_ok, message = check_bot_commands()
            logger.info(f"Проверка файла команд: {message}")

            # Синхронизируем файлы
            sync_ok, sync_message = sync_files()
            logger.info(f"Синхронизация файлов: {sync_message}")

            # Выполняем дополнительные проверки
            issues = perform_system_check()

            if issues:
                logger.warning(f"Обнаружены проблемы: {', '.join(issues)}")

                # Останавливаем и перезапускаем бота
                logger.info("Перезапуск бота из-за проблем...")
                stop_bot()
                time.sleep(2)
                start_bot()
                return True

            logger.info("Система в порядке, перезапуск не требуется")
            return False

        def main():
            """Основная функция скрипта"""
            import argparse

            parser = argparse.ArgumentParser(description='Автоматический перезапуск и проверка системы')
            parser.add_argument('--force-restart', action='store_true', help='Принудительно перезапустить бота')
            parser.add_argument('--check-only', action='store_true', help='Только проверить систему без перезапуска')
            parser.add_argument('--sync', action='store_true', help='Синхронизировать файлы')

            args = parser.parse_args()

            if args.force_restart:
                logger.info("Принудительный перезапуск бота...")
                stop_bot()
                time.sleep(2)
                start_bot()
            elif args.check_only:
                logger.info("Только проверка системы...")
                issues = perform_system_check()

                if issues:
                    logger.warning(f"Обнаружены проблемы: {', '.join(issues)}")
                else:
                    logger.info("Система в порядке")
            elif args.sync:
                logger.info("Синхронизация файлов...")
                sync_ok, sync_message = sync_files()
                logger.info(f"Результат синхронизации: {sync_message}")
            else:
                # Обычный режим работы - перезапуск при необходимости
                restart_if_needed()

            return 0

        if __name__ == "__main__":
            sys.exit(main())