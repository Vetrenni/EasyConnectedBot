#!/usr/bin/env python
"""
Скрипт для быстрого исправления проблем синхронизации и коммуникации между ботом и админкой
"""
import os
import sys
import subprocess
import time
import argparse
import json
import shutil
import traceback
import logging
import signal
from datetime import datetime

# Настройка логирования для отслеживания проблем
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fix")

# Получаем абсолютный путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_DIR = os.path.join(BASE_DIR, 'admin')


def check_file_exists(filepath, default_content=None):
    """Проверяет существование файла и создает его с дефолтным содержимым если его нет"""
    if not os.path.exists(filepath):
        logger.info(f"Файл {filepath} не существует, создаю...")
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if default_content is not None:
            with open(filepath, 'w', encoding='utf-8') as f:
                if isinstance(default_content, (dict, list)):
                    json.dump(default_content, f, ensure_ascii=False, indent=4)
                else:
                    f.write(default_content)
        return False
    return True


def check_json_file_valid(filepath, default_structure=None):
    """Проверяет целостность JSON-файла"""
    if not os.path.exists(filepath):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Файл {filepath} пуст")
                return False

            json_data = json.loads(content)

            # Проверяем соответствие типу данных
            if default_structure is not None:
                if isinstance(default_structure, list) and not isinstance(json_data, list):
                    logger.warning(f"Файл {filepath} имеет неправильную структуру (должен быть список)")
                    return False
                elif isinstance(default_structure, dict) and not isinstance(json_data, dict):
                    logger.warning(f"Файл {filepath} имеет неправильную структуру (должен быть словарь)")
                    return False

            return True
    except json.JSONDecodeError:
        logger.error(f"Файл {filepath} содержит неправильный JSON")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке файла {filepath}: {e}")
        return False


def backup_file(filepath):
    """Создает резервную копию файла"""
    if not os.path.exists(filepath):
        return False

    try:
        backup_path = f"{filepath}.backup.{int(time.time())}"
        shutil.copy2(filepath, backup_path)
        logger.info(f"Создана резервная копия файла {filepath} -> {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании резервной копии файла {filepath}: {e}")
        return False


def synchronize_file(src, dst):
    """Копирует файл из src в dst с созданием резервной копии"""
    if not os.path.exists(src):
        logger.error(f"Исходный файл {src} не существует")
        return False

    try:
        # Создаем резервную копию целевого файла, если он существует
        if os.path.exists(dst):
            backup_file(dst)

        # Копируем файл
        shutil.copy2(src, dst)
        logger.info(f"Успешно скопирован файл {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при синхронизации файла {src} -> {dst}: {e}")
        return False


def fix_permissions():
    """Исправляет права доступа файлов для синхронизации"""
    critical_files = [
        'admins.json',
        'global_admins.json',
        'allowed_users.json',
        'streamers.json',
        'user_stats.json',
        'user_settings.json',
        'chats.json',
        'bot_commands.json'
    ]

    fixed_count = 0

    for filename in critical_files:
        bot_file = os.path.join(BASE_DIR, filename)
        admin_file = os.path.join(ADMIN_DIR, filename)

        for filepath in [bot_file, admin_file]:
            if os.path.exists(filepath):
                try:
                    # Устанавливаем разрешения на чтение и запись для всех
                    os.chmod(filepath, 0o666)
                    logger.info(f"Установлены права доступа 666 для {filepath}")
                    fixed_count += 1
                except Exception as e:
                    logger.error(f"Не удалось установить права доступа для {filepath}: {e}")

    return fixed_count


def sync_bot_to_admin():
    """Копирует файлы из директории бота в директорию админки"""
    sync_files = [
        'admins.json',
        'global_admins.json',
        'allowed_users.json',
        'streamers.json',
        'user_stats.json',
        'user_settings.json',
        'chats.json',
        'bot_commands.json'
    ]

    success_count = 0

    for filename in sync_files:
        src = os.path.join(BASE_DIR, filename)
        dst = os.path.join(ADMIN_DIR, filename)

        if synchronize_file(src, dst):
            success_count += 1

    return success_count


def sync_admin_to_bot():
    """Копирует файлы из директории админки в директорию бота"""
    sync_files = [
        'admins.json',
        'global_admins.json',
        'allowed_users.json',
        'streamers.json',
        'user_stats.json',
        'user_settings.json',
        'chats.json',
        'bot_commands.json'
    ]

    success_count = 0

    for filename in sync_files:
        src = os.path.join(ADMIN_DIR, filename)
        dst = os.path.join(BASE_DIR, filename)

        if synchronize_file(src, dst):
            success_count += 1

    return success_count


def repair_json_files():
    """Проверяет и восстанавливает поврежденные JSON-файлы"""
    critical_files = {
        'admins.json': [],
        'global_admins.json': [],
        'allowed_users.json': [],
        'streamers.json': [],
        'user_stats.json': {},
        'user_settings.json': {},
        'chats.json': {},
        'bot_commands.json': []
    }

    repaired_count = 0

    for filename, default_structure in critical_files.items():
        bot_file = os.path.join(BASE_DIR, filename)
        admin_file = os.path.join(ADMIN_DIR, filename)

        # Проверяем файл в директории бота
        check_file_exists(bot_file, default_structure)
        if not check_json_file_valid(bot_file, default_structure):
            logger.warning(f"Файл {bot_file} поврежден, создаю резервную копию и восстанавливаю")
            if os.path.exists(bot_file):
                backup_file(bot_file)
            with open(bot_file, 'w', encoding='utf-8') as f:
                json.dump(default_structure, f, ensure_ascii=False, indent=4)
            repaired_count += 1

        # Проверяем файл в директории админки
        check_file_exists(admin_file, default_structure)
        if not check_json_file_valid(admin_file, default_structure):
            logger.warning(f"Файл {admin_file} поврежден, создаю резервную копию и восстанавливаю")
            if os.path.exists(admin_file):
                backup_file(admin_file)
            with open(admin_file, 'w', encoding='utf-8') as f:
                json.dump(default_structure, f, ensure_ascii=False, indent=4)
            repaired_count += 1

    return repaired_count


def check_bot_commands():
    """Проверяет файл команд бота и исправляет его при необходимости"""
    bot_commands_file = os.path.join(BASE_DIR, 'bot_commands.json')

    # Проверяем существование файла
    if not os.path.exists(bot_commands_file):
        with open(bot_commands_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        logger.info(f"Создан пустой файл команд бота")
        return True

    try:
        # Проверяем содержимое файла
        with open(bot_commands_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                with open(bot_commands_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
                logger.info(f"Файл команд бота был пуст, создан пустой список")
                return True

            try:
                commands = json.loads(content)

                if not isinstance(commands, list):
                    backup_file(bot_commands_file)
                    with open(bot_commands_file, 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=4)
                    logger.info(f"Исправлена структура файла команд бота (не был списком)")
                    return True

                # Проверяем зависшие команды
                fixed = False
                for cmd in commands:
                    if cmd.get('status') == 'pending':
                        cmd['timestamp'] = '0'  # Сбрасываем метку времени для ускорения обработки
                        fixed = True

                if fixed:
                    with open(bot_commands_file, 'w', encoding='utf-8') as f:
                        json.dump(commands, f, ensure_ascii=False, indent=4)
                    logger.info(f"Сброшены метки времени для зависших команд")
                    return True

                return False
            except json.JSONDecodeError:
                backup_file(bot_commands_file)
                with open(bot_commands_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
                logger.info(f"Файл команд бота был поврежден и восстановлен")
                return True
    except Exception as e:
        logger.error(f"Ошибка при проверке файла команд бота: {e}")
        traceback.print_exc()
        return False


def test_bot_commands():
    """Тестирует систему команд бота"""
    from bot_command import send_message_to_user

    # Находим ID глобального админа из файла
    global_admins_file = os.path.join(BASE_DIR, 'global_admins.json')
    if not os.path.exists(global_admins_file):
        logger.error("Файл global_admins.json не найден")
        return False

    try:
        with open(global_admins_file, 'r', encoding='utf-8') as f:
            global_admins = json.load(f)

        if not global_admins:
            logger.error("В файле global_admins.json нет администраторов")
            return False

        admin_id = global_admins[0]

        # Отправляем тестовое сообщение
        message = f"Тестовое сообщение от fix.py. Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        success = send_message_to_user(admin_id, message)

        if success:
            logger.info(f"Тестовое сообщение успешно отправлено администратору {admin_id}")
            return True
        else:
            logger.error(f"Не удалось отправить тестовое сообщение администратору {admin_id}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при тестировании команд бота: {e}")
        traceback.print_exc()
        return False


def check_pid_file():
    """Проверяет файл PID бота и запускает бота при необходимости"""
    pid_file = os.path.join(BASE_DIR, 'bot.pid')

    # Если файл PID не существует, значит бот не запущен
    if not os.path.exists(pid_file):
        logger.info("Файл PID не найден, бот не запущен")
        return False

    try:
        # Проверяем PID бота
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Проверяем, существует ли процесс
        try:
            import psutil
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                cmd_line = process.cmdline()

                # Проверяем, что это процесс бота
                if 'python' in process.name().lower() and any('main.py' in cmd for cmd in cmd_line):
                    logger.info(f"Бот запущен, PID: {pid}")
                    return True
                else:
                    logger.warning(f"Процесс с PID {pid} существует, но это не бот")
                    return False
            else:
                logger.warning(f"Процесс с PID {pid} не существует")
                return False
        except ImportError:
            # Если psutil не установлен, используем более простой метод
            try:
                os.kill(pid, 0)  # Проверка существования процесса
                logger.info(f"Процесс с PID {pid} существует, но невозможно проверить, что это бот")
                return True
            except OSError:
                logger.warning(f"Процесс с PID {pid} не существует")
                return False
    except Exception as e:
        logger.error(f"Ошибка при проверке файла PID: {e}")
        return False


def start_bot():
    """Запускает бота"""
    logger.info("Запуск бота...")

    try:
        # Запускаем бота с рабочей директорией в BASE_DIR
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, 'main.py')],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Даем процессу время на инициализацию
        time.sleep(5)

        # Проверяем, запустился ли процесс
        if process.poll() is None:
            logger.info(f"Бот успешно запущен с PID {process.pid}")
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Бот не запустился. Код выхода: {process.returncode}")
            logger.error(f"Стандартный вывод: {stdout.decode('utf-8', errors='ignore')}")
            logger.error(f"Ошибки: {stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        traceback.print_exc()
        return False


def stop_bot():
    """Останавливает бота"""
    pid_file = os.path.join(BASE_DIR, 'bot.pid')

    if not os.path.exists(pid_file):
        logger.warning(f"Файл PID бота не найден: {pid_file}")
        return True  # Считаем, что бот и так не запущен

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        try:
            import psutil
            if psutil.pid_exists(pid):
                # Получаем объект процесса
                process = psutil.Process(pid)

                # Проверяем, что это процесс бота
                cmd_line = process.cmdline()
                if 'python' in process.name().lower() and any('main.py' in cmd for cmd in cmd_line):
                    logger.info(f"Завершение процесса бота с PID {pid}")
                    process.terminate()  # SIGTERM

                    # Ждем завершения процесса
                    try:
                        process.wait(timeout=10)  # Ждем до 10 секунд
                    except psutil.TimeoutExpired:
                        # Если процесс не завершается, делаем kill
                        logger.warning(f"Процесс не завершился по SIGTERM, принудительное завершение")
                        process.kill()  # SIGKILL
                        process.wait(timeout=5)

                    logger.info(f"Бот с PID {pid} остановлен")
                else:
                    logger.warning(f"Процесс с PID {pid} не является ботом")
            else:
                logger.warning(f"Процесс с PID {pid} не существует")
        except ImportError:
            # Если psutil не установлен, используем os.kill
            # Это зависит от системы
            if os.name == 'posix':  # Linux/Unix
                try:
                    # Отправляем сигнал SIGTERM
                    os.kill(pid, 15)  # 15 = SIGTERM
                    time.sleep(5)

                    # Проверяем, завершился ли процесс
                    try:
                        os.kill(pid, 0)  # Проверка существования процесса
                        # Если мы дошли сюда, процесс все еще существует
                        os.kill(pid, 9)  # 9 = SIGKILL
                    except OSError:
                        # Процесс уже завершен
                        pass

                    logger.info(f"Бот с PID {pid} остановлен через os.kill")
                except OSError:
                    logger.warning(f"Процесс с PID {pid} не существует")
            else:  # Windows
                try:
                    import subprocess
                    # На Windows используем taskkill
                    subprocess.run(['taskkill', '/PID', str(pid), '/F'], capture_output=True)
                    logger.info(f"Бот с PID {pid} остановлен через taskkill")
                except Exception as e:
                    logger.error(f"Ошибка при остановке процесса с PID {pid}: {e}")

        # Удаляем файл PID
        os.remove(pid_file)
        return True
    except Exception as e:
        logger.error(f"Ошибка при остановке бота: {e}")
        traceback.print_exc()
        return False


def fix_all():
    """Выполняет все исправления и синхронизацию"""
    logger.info("=== Выполнение полного исправления системы ===")

    # Шаг 1: Проверяем и восстанавливаем структуру JSON-файлов
    repaired = repair_json_files()
    logger.info(f"Восстановлено {repaired} JSON-файлов")

    # Шаг 2: Проверяем права доступа
    fixed = fix_permissions()
    logger.info(f"Исправлены права доступа для {fixed} файлов")

    # Шаг 3: Синхронизация из админки в бота
    synced = sync_admin_to_bot()
    logger.info(f"Синхронизировано {synced} файлов из админки в бота")

    # Шаг 4: Проверяем файл команд бота
    check_bot_commands()
    logger.info("Проверка файла команд бота завершена")

    # Шаг 5: Останавливаем и запускаем бота
    if check_pid_file():
        logger.info("Бот запущен, останавливаем...")
        stop_bot()
        time.sleep(2)

    start_bot()
    logger.info("Бот запущен заново")

    # Шаг 6: Синхронизация из бота в админку
    synced = sync_bot_to_admin()
    logger.info(f"Синхронизировано {synced} файлов из бота в админку")

    # Шаг 7: Тестирование команд бота
    test_bot_commands()

    logger.info("=== Полное исправление системы завершено ===")
    return True


def diagnose():
    """Выполняет диагностику системы и возвращает список проблем"""
    logger.info("=== Выполнение диагностики системы ===")
    issues = []

    # Проверка существования файлов
    critical_files = [
        'admins.json',
        'global_admins.json',
        'allowed_users.json',
        'streamers.json',
        'user_stats.json',
        'user_settings.json',
        'chats.json',
        'bot_commands.json'
    ]

    for filename in critical_files:
        bot_file = os.path.join(BASE_DIR, filename)
        admin_file = os.path.join(ADMIN_DIR, filename)

        if not os.path.exists(bot_file):
            issues.append(f"Файл {filename} отсутствует в директории бота")
        elif os.path.getsize(bot_file) == 0:
            issues.append(f"Файл {filename} в директории бота пуст")

        if not os.path.exists(admin_file):
            issues.append(f"Файл {filename} отсутствует в директории админки")
        elif os.path.getsize(admin_file) == 0:
            issues.append(f"Файл {filename} в директории админки пуст")

        # Проверка синхронизации
        if os.path.exists(bot_file) and os.path.exists(admin_file):
            try:
                with open(bot_file, 'r', encoding='utf-8') as f:
                    bot_content = f.read()
                with open(admin_file, 'r', encoding='utf-8') as f:
                    admin_content = f.read()

                if bot_content != admin_content:
                    issues.append(f"Файл {filename} не синхронизирован между ботом и админкой")
            except Exception as e:
                issues.append(f"Ошибка при проверке синхронизации файла {filename}: {e}")

    # Проверка PID-файла и процесса бота
    if not check_pid_file():
        issues.append("Бот не запущен или файл PID отсутствует")

    # Проверка файла команд бота
    bot_commands_file = os.path.join(BASE_DIR, 'bot_commands.json')
    if not os.path.exists(bot_commands_file):
        issues.append("Файл команд бота отсутствует")
    else:
        try:
            with open(bot_commands_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    issues.append("Файл команд бота пуст")
                else:
                    commands = json.loads(content)

                    if not isinstance(commands, list):
                        issues.append("Файл команд бота имеет неправильную структуру (не список)")

                    pending_count = sum(1 for cmd in commands if cmd.get('status') == 'pending')
                    if pending_count > 0:
                        issues.append(f"В очереди команд бота {pending_count} необработанных команд")
        except json.JSONDecodeError:
            issues.append("Файл команд бота содержит невалидный JSON")
        except Exception as e:
            issues.append(f"Ошибка при проверке файла команд бота: {e}")

    logger.info(f"Обнаружено {len(issues)} проблем:")
    for issue in issues:
        logger.info(f"- {issue}")

    logger.info("=== Диагностика системы завершена ===")
    return issues


def file_lock(file_path, mode='r'):
    """
    Открывает файл, с поддержкой кроссплатформенности.
    На Windows просто открывает файл без блокировки.

    :param file_path: Путь к файлу
    :param mode: Режим открытия файла ('r' для чтения, 'w' для записи)
    :return: Открытый файловый объект
    """
    try:
        f = open(file_path, mode, encoding='utf-8')

        # Блокировка файла только на Unix-системах
        if os.name == 'posix':
            try:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (ImportError, IOError, OSError) as e:
                logger.warning(f"Не удалось получить блокировку для файла {file_path}: {e}")

        return f
    except Exception as e:
        logger.error(f"Ошибка при открытии файла {file_path}: {e}")
        return None

def main():
    """Основная функция скрипта"""
    parser = argparse.ArgumentParser(description='Скрипт для исправления проблем синхронизации и коммуникации')
    parser.add_argument('--fix-all', action='store_true', help='Выполнить все исправления')
    parser.add_argument('--diagnose', action='store_true', help='Выполнить диагностику системы')
    parser.add_argument('--repair-json', action='store_true', help='Восстановить структуру JSON-файлов')
    parser.add_argument('--fix-permissions', action='store_true', help='Исправить права доступа файлов')
    parser.add_argument('--sync-to-bot', action='store_true', help='Синхронизировать файлы из админки в бота')
    parser.add_argument('--sync-to-admin', action='store_true', help='Синхронизировать файлы из бота в админку')
    parser.add_argument('--check-bot-commands', action='store_true', help='Проверить и исправить файл команд бота')
    parser.add_argument('--test-bot-commands', action='store_true', help='Протестировать систему команд бота')
    parser.add_argument('--restart-bot', action='store_true', help='Перезапустить бота')

    args = parser.parse_args()

    if args.fix_all:
        fix_all()

    if args.diagnose:
        issues = diagnose()
        if not issues:
            print("Проблем не обнаружено!")
        else:
            print(f"Обнаружено {len(issues)} проблем:")
            for issue in issues:
                print(f"- {issue}")

    if args.repair_json:
        repaired = repair_json_files()
        print(f"Восстановлено {repaired} JSON-файлов")

    if args.fix_permissions:
        fixed = fix_permissions()
        print(f"Исправлены права доступа для {fixed} файлов")

    if args.sync_to_bot:
        synced = sync_admin_to_bot()
        print(f"Синхронизировано {synced} файлов из админки в бота")

    if args.sync_to_admin:
        synced = sync_bot_to_admin()
        print(f"Синхронизировано {synced} файлов из бота в админку")

    if args.check_bot_commands:
        check_bot_commands()
        print("Проверка файла команд бота завершена")

    if args.test_bot_commands:
        success = test_bot_commands()
        if success:
            print("Тестирование команд бота успешно завершено")
        else:
            print("Тестирование команд бота завершилось с ошибками")

    if args.restart_bot:
        if check_pid_file():
            print("Бот запущен, останавливаем...")
            stop_bot()
            time.sleep(2)

        success = start_bot()
        if success:
            print("Бот успешно перезапущен")
        else:
            print("Ошибка при перезапуске бота")

    # Если не указано никаких аргументов, выполняем диагностику
    if not any(vars(args).values()):
        issues = diagnose()
        if issues:
            print(f"Обнаружено {len(issues)} проблем:")
            for issue in issues:
                print(f"- {issue}")

            # Спрашиваем, нужно ли исправить найденные проблемы
            answer = input("Хотите исправить найденные проблемы? (y/n): ").strip().lower()
            if answer == 'y':
                fix_all()
        else:
            print("Проблем не обнаружено!")

if __name__ == "__main__":
    sys.exit(main())