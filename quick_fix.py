#!/usr/bin/env python
"""
Скрипт быстрой диагностики и исправления проблем синхронизации
"""
import os
import sys
import json
import shutil
import logging
import time
import traceback
import argparse
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("quick_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("quick_fix")

# Получаем абсолютный путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_DIR = os.path.join(BASE_DIR, 'admin')

# Список файлов для синхронизации
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

# Базовые структуры для файлов
DEFAULT_STRUCTURES = {
    'admins.json': [],
    'global_admins.json': [],
    'allowed_users.json': [],
    'streamers.json': [],
    'user_stats.json': {},
    'user_settings.json': {},
    'chats.json': {},
    'bot_commands.json': []
}


def fix_file(file_path, default_structure):
    """
    Исправляет файл, если он поврежден

    :param file_path: Путь к файлу
    :param default_structure: Структура по умолчанию
    :return: True если файл был исправлен, False если ошибок не было
    """
    if not os.path.exists(file_path):
        # Создаем директорию для файла, если её нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Создаем файл с дефолтной структурой
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_structure, f, ensure_ascii=False, indent=4)

        logger.info(f"Создан новый файл: {file_path}")
        return True

    try:
        # Проверяем размер файла
        if os.path.getsize(file_path) == 0:
            # Файл пуст, записываем дефолтную структуру
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_structure, f, ensure_ascii=False, indent=4)

            logger.info(f"Исправлен пустой файл: {file_path}")
            return True

        # Проверяем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

            if not content:
                # Файл пуст, записываем дефолтную структуру
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_structure, f, ensure_ascii=False, indent=4)

                logger.info(f"Исправлен пустой файл: {file_path}")
                return True

            try:
                # Пробуем разобрать JSON
                data = json.loads(content)

                # Проверяем тип данных
                if isinstance(default_structure, list) and not isinstance(data, list):
                    # Неверный тип данных, записываем дефолтную структуру
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_structure, f, ensure_ascii=False, indent=4)

                    logger.info(f"Исправлен файл с неверным типом данных: {file_path}")
                    return True

                if isinstance(default_structure, dict) and not isinstance(data, dict):
                    # Неверный тип данных, записываем дефолтную структуру
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_structure, f, ensure_ascii=False, indent=4)

                    logger.info(f"Исправлен файл с неверным типом данных: {file_path}")
                    return True

                # Все в порядке
                return False
            except json.JSONDecodeError:
                # Создаем резервную копию поврежденного файла
                backup_file = f"{file_path}.bad.{int(time.time())}"
                shutil.copy2(file_path, backup_file)

                # Записываем дефолтную структуру
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_structure, f, ensure_ascii=False, indent=4)

                logger.info(f"Исправлен поврежденный файл: {file_path} (резервная копия: {backup_file})")
                return True
    except Exception as e:
        logger.error(f"Ошибка при исправлении файла {file_path}: {e}")
        traceback.print_exc()
        return False


def fix_all_files():
    """
    Исправляет все файлы синхронизации

    :return: Количество исправленных файлов
    """
    fixed_count = 0

    for filename in SYNC_FILES:
        # Исправляем файл в директории бота
        bot_file = os.path.join(BASE_DIR, filename)
        if fix_file(bot_file, DEFAULT_STRUCTURES[filename]):
            fixed_count += 1

        # Исправляем файл в директории админки
        admin_file = os.path.join(ADMIN_DIR, filename)
        if fix_file(admin_file, DEFAULT_STRUCTURES[filename]):
            fixed_count += 1

    return fixed_count


def copy_files_from_bot_to_admin():
    """
    Копирует все файлы из директории бота в директорию админки

    :return: Количество скопированных файлов
    """
    copied_count = 0

    for filename in SYNC_FILES:
        bot_file = os.path.join(BASE_DIR, filename)
        admin_file = os.path.join(ADMIN_DIR, filename)

        # Проверяем существование исходного файла
        if not os.path.exists(bot_file):
            logger.warning(f"Файл {bot_file} не существует")
            continue

        try:
            # Создаем резервную копию файла админки, если он существует
            if os.path.exists(admin_file):
                backup_file = f"{admin_file}.bak.{int(time.time())}"
                shutil.copy2(admin_file, backup_file)
                logger.info(f"Создана резервная копия файла админки: {backup_file}")

            # Копируем файл из бота в админку
            shutil.copy2(bot_file, admin_file)
            logger.info(f"Файл {filename} скопирован из бота в админку")
            copied_count += 1
        except Exception as e:
            logger.error(f"Ошибка при копировании файла {filename}: {e}")
            traceback.print_exc()

    return copied_count


def copy_files_from_admin_to_bot():
    """
    Копирует все файлы из директории админки в директорию бота

    :return: Количество скопированных файлов
    """
    copied_count = 0

    for filename in SYNC_FILES:
        bot_file = os.path.join(BASE_DIR, filename)
        admin_file = os.path.join(ADMIN_DIR, filename)

        # Проверяем существование исходного файла
        if not os.path.exists(admin_file):
            logger.warning(f"Файл {admin_file} не существует")
            continue

        try:
            # Создаем резервную копию файла бота, если он существует
            if os.path.exists(bot_file):
                backup_file = f"{bot_file}.bak.{int(time.time())}"
                shutil.copy2(bot_file, backup_file)
                logger.info(f"Создана резервная копия файла бота: {backup_file}")

            # Копируем файл из админки в бота
            shutil.copy2(admin_file, bot_file)
            logger.info(f"Файл {filename} скопирован из админки в бота")
            copied_count += 1
        except Exception as e:
            logger.error(f"Ошибка при копировании файла {filename}: {e}")
            traceback.print_exc()

    return copied_count


def check_file_permissions():
    """
    Проверяет и исправляет права доступа к файлам

    :return: Количество файлов с исправленными правами
    """
    fixed_count = 0

    for filename in SYNC_FILES:
        # Проверяем файл в директории бота
        bot_file = os.path.join(BASE_DIR, filename)
        if os.path.exists(bot_file):
            try:
                # Устанавливаем права на чтение и запись для всех
                os.chmod(bot_file, 0o666)
                logger.info(f"Установлены права 666 для файла {bot_file}")
                fixed_count += 1
            except Exception as e:
                logger.error(f"Ошибка при изменении прав для файла {bot_file}: {e}")

        # Проверяем файл в директории админки
        admin_file = os.path.join(ADMIN_DIR, filename)
        if os.path.exists(admin_file):
            try:
                # Устанавливаем права на чтение и запись для всех
                os.chmod(admin_file, 0o666)
                logger.info(f"Установлены права 666 для файла {admin_file}")
                fixed_count += 1
            except Exception as e:
                logger.error(f"Ошибка при изменении прав для файла {admin_file}: {e}")

    return fixed_count


def extract_user_data(force=False):
    """
    Извлекает и проверяет данные пользователей из файлов

    :param force: Вывести данные даже если все в порядке
    :return: True если есть проблемы, False если все в порядке
    """
    has_issues = False

    # Загружаем файлы
    admin_files = {}
    bot_files = {}

    for filename in ['admins.json', 'global_admins.json', 'allowed_users.json', 'streamers.json']:
        admin_path = os.path.join(ADMIN_DIR, filename)
        bot_path = os.path.join(BASE_DIR, filename)

        try:
            if os.path.exists(admin_path):
                with open(admin_path, 'r', encoding='utf-8') as f:
                    admin_files[filename] = json.load(f)
            else:
                admin_files[filename] = []
                has_issues = True
                logger.warning(f"Файл {admin_path} не существует")

            if os.path.exists(bot_path):
                with open(bot_path, 'r', encoding='utf-8') as f:
                    bot_files[filename] = json.load(f)
            else:
                bot_files[filename] = []
                has_issues = True
                logger.warning(f"Файл {bot_path} не существует")

            # Проверяем соответствие файлов
            if set(admin_files[filename]) != set(bot_files[filename]):
                has_issues = True
                logger.warning(f"Файлы {filename} в боте и админке отличаются")
        except Exception as e:
            has_issues = True
            logger.error(f"Ошибка при загрузке файла {filename}: {e}")

    if has_issues or force:
        # Выводим информацию о пользователях
        print("\nДанные пользователей:")
        print("=================")

        print(f"\nАдминистраторы (админка): {len(admin_files.get('admins.json', []))}")
        print(admin_files.get('admins.json', []))

        print(f"\nАдминистраторы (бот): {len(bot_files.get('admins.json', []))}")
        print(bot_files.get('admins.json', []))

        print(f"\nГлобальные администраторы (админка): {len(admin_files.get('global_admins.json', []))}")
        print(admin_files.get('global_admins.json', []))

        print(f"\nГлобальные администраторы (бот): {len(bot_files.get('global_admins.json', []))}")
        print(bot_files.get('global_admins.json', []))

        print(f"\nРазрешенные пользователи (админка): {len(admin_files.get('allowed_users.json', []))}")
        print(admin_files.get('allowed_users.json', []))

        print(f"\nРазрешенные пользователи (бот): {len(bot_files.get('allowed_users.json', []))}")
        print(bot_files.get('allowed_users.json', []))

        print(f"\nСтриммеры (админка): {len(admin_files.get('streamers.json', []))}")
        print(admin_files.get('streamers.json', []))

        print(f"\nСтриммеры (бот): {len(bot_files.get('streamers.json', []))}")
        print(bot_files.get('streamers.json', []))

    return has_issues


def add_user_manually(user_id, user_type):
    """
    Добавляет пользователя вручную в соответствующие файлы

    :param user_id: ID пользователя
    :param user_type: Тип пользователя (user, admin, global_admin, streamer)
    :return: True если успешно, False если произошла ошибка
    """
    user_id = str(user_id)  # Преобразуем ID в строку

    try:
        # Всегда добавляем в список разрешенных пользователей
        allowed_users_bot = os.path.join(BASE_DIR, 'allowed_users.json')
        allowed_users_admin = os.path.join(ADMIN_DIR, 'allowed_users.json')

        # Загружаем и обновляем файл бота
        if os.path.exists(allowed_users_bot):
            with open(allowed_users_bot, 'r', encoding='utf-8') as f:
                users = json.load(f)

            if user_id not in users:
                users.append(user_id)

                with open(allowed_users_bot, 'w', encoding='utf-8') as f:
                    json.dump(users, f, ensure_ascii=False, indent=4)

                logger.info(f"Пользователь {user_id} добавлен в файл разрешенных пользователей бота")

        # Загружаем и обновляем файл админки
        if os.path.exists(allowed_users_admin):
            with open(allowed_users_admin, 'r', encoding='utf-8') as f:
                users = json.load(f)

            if user_id not in users:
                users.append(user_id)

                with open(allowed_users_admin, 'w', encoding='utf-8') as f:
                    json.dump(users, f, ensure_ascii=False, indent=4)

                logger.info(f"Пользователь {user_id} добавлен в файл разрешенных пользователей админки")

        # Добавляем пользователя в соответствующие файлы в зависимости от типа
        if user_type in ['admin', 'global_admin', 'streamer']:
            # Определяем файлы для обновления
            if user_type == 'admin':
                files_bot = [os.path.join(BASE_DIR, 'admins.json')]
                files_admin = [os.path.join(ADMIN_DIR, 'admins.json')]
            elif user_type == 'global_admin':
                files_bot = [os.path.join(BASE_DIR, 'global_admins.json'), os.path.join(BASE_DIR, 'admins.json')]
                files_admin = [os.path.join(ADMIN_DIR, 'global_admins.json'), os.path.join(ADMIN_DIR, 'admins.json')]
            else:  # streamer
                files_bot = [os.path.join(BASE_DIR, 'streamers.json')]
                files_admin = [os.path.join(ADMIN_DIR, 'streamers.json')]

            # Обновляем файлы бота
            for file_path in files_bot:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        users = json.load(f)

                    if user_id not in users:
                        users.append(user_id)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(users, f, ensure_ascii=False, indent=4)

                        logger.info(f"Пользователь {user_id} добавлен в файл {os.path.basename(file_path)} бота")

                        # Обновляем файлы админки
                        for file_path in files_admin:
                            if os.path.exists(file_path):
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    users = json.load(f)

                                if user_id not in users:
                                    users.append(user_id)

                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        json.dump(users, f, ensure_ascii=False, indent=4)

                                    logger.info(
                                        f"Пользователь {user_id} добавлен в файл {os.path.basename(file_path)} админки")

                    return True
                    except Exception as e:
                    logger.error(f"Ошибка при добавлении пользователя {user_id} типа {user_type}: {e}")
                    traceback.print_exc()
                    return False

            def remove_user_manually(user_id, user_type=None):
                """
                Удаляет пользователя вручную из соответствующих файлов

                :param user_id: ID пользователя
                :param user_type: Тип пользователя (user, admin, global_admin, streamer) или None для всех типов
                :return: True если успешно, False если произошла ошибка
                """
                user_id = str(user_id)  # Преобразуем ID в строку

                try:
                    # Определяем файлы для обновления
                    files_to_update = []

                    if user_type == 'user' or user_type is None:
                        files_to_update.append(('allowed_users.json', True))

                    if user_type == 'admin' or user_type is None:
                        files_to_update.append(('admins.json', True))

                    if user_type == 'global_admin' or user_type is None:
                        files_to_update.append(('global_admins.json', True))

                    if user_type == 'streamer' or user_type is None:
                        files_to_update.append(('streamers.json', True))

                    removed_from = []

                    # Обрабатываем каждый файл
                    for filename, remove_from_allowed in files_to_update:
                        # Обновляем файл бота
                        bot_file = os.path.join(BASE_DIR, filename)
                        if os.path.exists(bot_file):
                            with open(bot_file, 'r', encoding='utf-8') as f:
                                users = json.load(f)

                            if user_id in users:
                                users.remove(user_id)

                                with open(bot_file, 'w', encoding='utf-8') as f:
                                    json.dump(users, f, ensure_ascii=False, indent=4)

                                removed_from.append(f"{filename} (бот)")

                        # Обновляем файл админки
                        admin_file = os.path.join(ADMIN_DIR, filename)
                        if os.path.exists(admin_file):
                            with open(admin_file, 'r', encoding='utf-8') as f:
                                users = json.load(f)

                            if user_id in users:
                                users.remove(user_id)

                                with open(admin_file, 'w', encoding='utf-8') as f:
                                    json.dump(users, f, ensure_ascii=False, indent=4)

                                removed_from.append(f"{filename} (админка)")

                    if removed_from:
                        logger.info(f"Пользователь {user_id} удален из файлов: {', '.join(removed_from)}")
                        return True
                    else:
                        logger.warning(f"Пользователь {user_id} не найден в указанных файлах")
                        return False
                except Exception as e:
                    logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
                    traceback.print_exc()
                    return False

            def check_and_fix_bot_commands():
                """
                Проверяет и исправляет файл команд бота

                :return: True если были исправления, False если файл в порядке
                """
                bot_commands_file = os.path.join(BASE_DIR, 'bot_commands.json')

                if not os.path.exists(bot_commands_file):
                    # Создаем пустой файл
                    with open(bot_commands_file, 'w', encoding='utf-8') as f:
                        json.dump([], f)

                    logger.info(f"Создан пустой файл команд бота: {bot_commands_file}")
                    return True

                try:
                    # Проверяем содержимое файла
                    with open(bot_commands_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                        if not content:
                            # Файл пуст, создаем пустой список
                            with open(bot_commands_file, 'w', encoding='utf-8') as f:
                                json.dump([], f)

                            logger.info(f"Файл команд бота был пуст, создан пустой список")
                            return True

                        try:
                            commands = json.loads(content)

                            if not isinstance(commands, list):
                                # Неверная структура, создаем пустой список
                                with open(bot_commands_file, 'w', encoding='utf-8') as f:
                                    json.dump([], f)

                                logger.info(f"Исправлена структура файла команд бота (не был списком)")
                                return True

                            # Проверяем наличие зависших команд
                            fixed_commands = False
                            now = time.time()

                            for cmd in commands:
                                if cmd.get('status') == 'pending':
                                    try:
                                        # Проверяем возраст команды
                                        cmd_time = float(cmd.get('timestamp', '0'))
                                        if now - cmd_time > 300:  # 5 минут
                                            cmd['timestamp'] = '0'
                                            fixed_commands = True
                                    except:
                                        cmd['timestamp'] = '0'
                                        fixed_commands = True

                            # Если были исправления, сохраняем файл
                            if fixed_commands:
                                with open(bot_commands_file, 'w', encoding='utf-8') as f:
                                    json.dump(commands, f, ensure_ascii=False, indent=4)

                                logger.info(f"Исправлены метки времени для зависших команд")
                                return True

                            # Проверяем наличие устаревших команд
                            old_commands = [cmd for cmd in commands if cmd.get('status') in ['completed', 'error']]
                            if old_commands and len(old_commands) > 50:  # Если более 50 устаревших команд
                                # Оставляем только команды со статусом pending и последние 10 завершенных
                                pending_commands = [cmd for cmd in commands if cmd.get('status') == 'pending']
                                recent_commands = sorted(
                                    old_commands,
                                    key=lambda x: float(x.get('timestamp', '0')),
                                    reverse=True
                                )[:10]

                                # Обновляем список команд
                                commands = pending_commands + recent_commands

                                # Сохраняем обновленный список
                                with open(bot_commands_file, 'w', encoding='utf-8') as f:
                                    json.dump(commands, f, ensure_ascii=False, indent=4)

                                logger.info(f"Очищены устаревшие команды, оставлено {len(commands)} команд")
                                return True

                            return False
                        except json.JSONDecodeError:
                            # Создаем резервную копию поврежденного файла
                            backup_file = f"{bot_commands_file}.bad.{int(time.time())}"
                            shutil.copy2(bot_commands_file, backup_file)

                            # Создаем пустой список
                            with open(bot_commands_file, 'w', encoding='utf-8') as f:
                                json.dump([], f)

                            logger.info(
                                f"Исправлен поврежденный файл команд бота, создана резервная копия: {backup_file}")
                            return True
                except Exception as e:
                    logger.error(f"Ошибка при проверке файла команд бота: {e}")
                    traceback.print_exc()
                    return False

            def main():
                """Основная функция скрипта"""
                parser = argparse.ArgumentParser(description='Быстрая диагностика и исправление проблем синхронизации')
                parser.add_argument('--fix', action='store_true', help='Исправить все файлы')
                parser.add_argument('--bot-to-admin', action='store_true', help='Копировать файлы из бота в админку')
                parser.add_argument('--admin-to-bot', action='store_true', help='Копировать файлы из админки в бота')
                parser.add_argument('--permissions', action='store_true', help='Исправить права доступа к файлам')
                parser.add_argument('--extract-users', action='store_true', help='Извлечь данные пользователей')
                parser.add_argument('--add-user', type=str, help='Добавить пользователя (формат: ID:тип)')
                parser.add_argument('--remove-user', type=str, help='Удалить пользователя (формат: ID[:тип])')
                parser.add_argument('--bot-commands', action='store_true',
                                    help='Проверить и исправить файл команд бота')

                args = parser.parse_args()

                if args.fix:
                    fixed_count = fix_all_files()
                    print(f"Исправлено {fixed_count} файлов")

                if args.bot_to_admin:
                    copied_count = copy_files_from_bot_to_admin()
                    print(f"Скопировано {copied_count} файлов из бота в админку")

                if args.admin_to_bot:
                    copied_count = copy_files_from_admin_to_bot()
                    print(f"Скопировано {copied_count} файлов из админки в бота")

                if args.permissions:
                    fixed_count = check_file_permissions()
                    print(f"Исправлены права доступа для {fixed_count} файлов")

                if args.extract_users:
                    extract_user_data(force=True)

                if args.add_user:
                    parts = args.add_user.split(':')
                    user_id = parts[0]
                    user_type = parts[1] if len(parts) > 1 else 'user'

                    if user_type not in ['user', 'admin', 'global_admin', 'streamer']:
                        print(f"Неверный тип пользователя: {user_type}")
                        print("Доступные типы: user, admin, global_admin, streamer")
                        return 1

                    success = add_user_manually(user_id, user_type)
                    if success:
                        print(f"Пользователь {user_id} добавлен как {user_type}")
                    else:
                        print(f"Ошибка при добавлении пользователя {user_id}")

                if args.remove_user:
                    parts = args.remove_user.split(':')
                    user_id = parts[0]
                    user_type = parts[1] if len(parts) > 1 else None

                    success = remove_user_manually(user_id, user_type)
                    if success:
                        print(f"Пользователь {user_id} удален")
                    else:
                        print(f"Ошибка при удалении пользователя {user_id}")

                if args.bot_commands:
                    fixed = check_and_fix_bot_commands()
                    if fixed:
                        print("Файл команд бота исправлен")
                    else:
                        print("Файл команд бота в порядке")

                # Если не указаны аргументы, просто проверяем систему
                if not any([args.fix, args.bot_to_admin, args.admin_to_bot, args.permissions,
                            args.extract_users, args.add_user, args.remove_user, args.bot_commands]):
                    print("Проверка системы...")

                    # Проверяем наличие директорий
                    print(f"Директория бота: {os.path.exists(BASE_DIR)}")
                    print(f"Директория админки: {os.path.exists(ADMIN_DIR)}")

                    # Проверяем наличие файлов
                    print("\nПроверка файлов:")
                    for filename in SYNC_FILES:
                        bot_file = os.path.join(BASE_DIR, filename)
                        admin_file = os.path.join(ADMIN_DIR, filename)

                        print(f"{filename}:")
                        print(f"  Бот: {'Существует' if os.path.exists(bot_file) else 'Отсутствует'}")
                        if os.path.exists(bot_file):
                            print(f"    Размер: {os.path.getsize(bot_file)} байт")

                        print(f"  Админка: {'Существует' if os.path.exists(admin_file) else 'Отсутствует'}")
                        if os.path.exists(admin_file):
                            print(f"    Размер: {os.path.getsize(admin_file)} байт")

                    # Проверяем данные пользователей
                    has_issues = extract_user_data(force=False)
                    if not has_issues:
                        print("\nДанные пользователей в порядке")

                    # Проверяем файл команд бота
                    bot_commands_file = os.path.join(BASE_DIR, 'bot_commands.json')
                    print(f"\nФайл команд бота: {'Существует' if os.path.exists(bot_commands_file) else 'Отсутствует'}")

                    if os.path.exists(bot_commands_file):
                        print(f"  Размер: {os.path.getsize(bot_commands_file)} байт")

                        try:
                            with open(bot_commands_file, 'r', encoding='utf-8') as f:
                                commands = json.load(f)

                            pending_count = sum(1 for cmd in commands if cmd.get('status') == 'pending')
                            completed_count = sum(1 for cmd in commands if cmd.get('status') == 'completed')
                            error_count = sum(1 for cmd in commands if cmd.get('status') == 'error')

                            print(f"  Всего команд: {len(commands)}")
                            print(f"  Ожидающих: {pending_count}")
                            print(f"  Выполненных: {completed_count}")
                            print(f"  Ошибок: {error_count}")
                        except Exception as e:
                            print(f"  Ошибка при чтении файла команд: {e}")

                return 0

            if __name__ == "__main__":
                sys.exit(main())