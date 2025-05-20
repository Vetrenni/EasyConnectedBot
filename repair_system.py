#!/usr/bin/env python
"""
Скрипт для диагностики и восстановления проблем синхронизации между ботом и админ-панелью
"""
import os
import sys
import json
import shutil
import logging
import time
import traceback
from datetime import datetime
import argparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("repair.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("repair_system")

# Определяем пути к директориям
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_DIR = os.path.join(BASE_DIR, 'admin')

# Файлы для синхронизации
SYNC_FILES = [
    'admins.json',
    'global_admins.json',
    'allowed_users.json',
    'streamers.json',
    'user_stats.json',
    'user_settings.json',
    'chats.json',
    'bot_commands.json'
]


def check_file_exists(file_path):
    """Проверяет существование файла и создает пустой, если он не существует"""
    if not os.path.exists(file_path):
        logger.warning(f"Файл {file_path} не найден. Создаю пустой файл.")
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Создаем пустой файл с соответствующей структурой
        if file_path.endswith(('admins.json', 'global_admins.json', 'allowed_users.json', 'streamers.json')):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        elif file_path.endswith(('user_stats.json', 'user_settings.json')):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        elif file_path.endswith('chats.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        elif file_path.endswith('bot_commands.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")

        return False
    return True


def verify_json_file(file_path):
    """Проверяет целостность JSON-файла и восстанавливает его при необходимости"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Файл {file_path} пуст. Инициализирую со значениями по умолчанию.")
                reset_json_file(file_path)
                return False

            # Пробуем разобрать JSON
            json.loads(content)
            return True
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка в JSON-файле {file_path}: {e}")
        # Создаем резервную копию поврежденного файла
        backup_file = f"{file_path}.bad.{int(time.time())}"
        shutil.copy2(file_path, backup_file)
        logger.info(f"Создана резервная копия поврежденного файла: {backup_file}")

        # Восстанавливаем файл
        reset_json_file(file_path)
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке файла {file_path}: {e}")
        traceback.print_exc()
        return False


def reset_json_file(file_path):
    """Сбрасывает JSON-файл к значениям по умолчанию"""
    try:
        if file_path.endswith(('admins.json', 'global_admins.json', 'allowed_users.json', 'streamers.json')):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        elif file_path.endswith(('user_stats.json', 'user_settings.json')):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        elif file_path.endswith('chats.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        elif file_path.endswith('bot_commands.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

        logger.info(f"Файл {file_path} сброшен к значениям по умолчанию")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сбросе файла {file_path}: {e}")
        traceback.print_exc()
        return False


def check_and_repair_all_files():
    """Проверяет и восстанавливает все файлы синхронизации"""
    logger.info("Начинаю проверку и восстановление файлов...")

    repaired_files = 0

    # Проверяем файлы в корневой директории
    for filename in SYNC_FILES:
        file_path = os.path.join(BASE_DIR, filename)
        exists = check_file_exists(file_path)

        if exists:
            # Проверяем JSON-файл
            if verify_json_file(file_path):
                logger.info(f"Файл {filename} в порядке")
            else:
                logger.info(f"Файл {filename} восстановлен")
                repaired_files += 1
        else:
            logger.info(f"Файл {filename} создан")
            repaired_files += 1

    # Проверяем файлы в директории админки
    for filename in SYNC_FILES:
        file_path = os.path.join(ADMIN_DIR, filename)
        exists = check_file_exists(file_path)

        if exists:
            # Проверяем JSON-файл
            if verify_json_file(file_path):
                logger.info(f"Файл admin/{filename} в порядке")
            else:
                logger.info(f"Файл admin/{filename} восстановлен")
                repaired_files += 1
        else:
            logger.info(f"Файл admin/{filename} создан")
            repaired_files += 1

    logger.info(f"Проверка и восстановление файлов завершены. Обработано файлов: {repaired_files}")
    return repaired_files


def synchronize_files():
    """Синхронизирует все файлы между директориями"""
    from admin.sync_bot import sync_all_from_bot_to_admin, sync_all_from_admin_to_bot

    logger.info("Запуск полной синхронизации файлов...")

    # Синхронизация из бота в админку
    bot_to_admin = sync_all_from_bot_to_admin()
    logger.info(f"Синхронизация из бота в админку: {bot_to_admin} файлов")

    # Синхронизация из админки в бота
    admin_to_bot = sync_all_from_admin_to_bot()
    logger.info(f"Синхронизация из админки в бота: {admin_to_bot} файлов")

    return bot_to_admin + admin_to_bot


def restart_bot():
    """Перезапускает бота (если это возможно)"""
    logger.info("Попытка перезапуска бота...")

    bot_pid_file = os.path.join(BASE_DIR, 'bot.pid')

    if os.path.exists(bot_pid_file):
        try:
            with open(bot_pid_file, 'r') as f:
                bot_pid = int(f.read().strip())

            # Проверяем, существует ли процесс
            import psutil
            if psutil.pid_exists(bot_pid):
                logger.info(f"Найден процесс бота с PID {bot_pid}. Отправляю сигнал остановки.")
                os.kill(bot_pid, 15)  # Отправляем сигнал SIGTERM
                time.sleep(5)  # Ждем завершения процесса

            # Запускаем бота заново
            import subprocess
            subprocess.Popen([sys.executable, os.path.join(BASE_DIR, 'main.py')])
            logger.info("Бот успешно перезапущен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при перезапуске бота: {e}")
            traceback.print_exc()
    else:
        logger.warning("Не найден файл PID бота. Перезапуск невозможен.")

    return False


def repair_system(restart=False):
    """Выполняет полное восстановление системы"""
    logger.info("=" * 50)
    logger.info("Запуск полного восстановления системы")
    logger.info("=" * 50)

    # Проверяем и восстанавливаем файлы
    check_and_repair_all_files()

    # Синхронизируем файлы
    synchronize_files()

    # Перезапускаем бота при необходимости
    if restart:
        restart_bot()

    logger.info("Восстановление системы завершено")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Восстановление системы бота и админ-панели')
    parser.add_argument('--restart', action='store_true', help='Перезапустить бота после восстановления')
    parser.add_argument('--check-only', action='store_true', help='Только проверить файлы без исправления')

    args = parser.parse_args()

    if args.check_only:
        logger.info("Выполняется только проверка файлов...")
        check_and_repair_all_files()
    else:
        repair_system(restart=args.restart)