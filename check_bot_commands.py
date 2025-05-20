#!/usr/bin/env python
"""
Скрипт для проверки очереди команд бота и мониторинга их выполнения
"""
import os
import sys
import json
import logging
import time
import traceback
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("commands.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("check_bot_commands")

# Получаем абсолютный путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Путь к файлу с командами бота
BOT_COMMANDS_FILE = os.path.join(BASE_DIR, "bot_commands.json")


def send_test_message(user_id):
    """
    Отправляет тестовое сообщение через систему команд

    :param user_id: ID пользователя для отправки сообщения
    :return: True если команда добавлена, иначе False
    """
    try:
        from bot_command import send_message_to_user

        message = f"Тестовое сообщение от системы диагностики. Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result = send_message_to_user(user_id, message)

        if result:
            logger.info(f"Тестовая команда отправки сообщения пользователю {user_id} добавлена в очередь")
        else:
            logger.error(f"Не удалось добавить тестовую команду для пользователя {user_id}")

        return result
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового сообщения: {e}")
        traceback.print_exc()
        return False


def check_bot_commands_file():
    """
    Проверяет файл команд бота и его содержимое

    :return: (файл_существует, структура_корректна, количество_команд)
    """
    if not os.path.exists(BOT_COMMANDS_FILE):
        logger.warning(f"Файл команд бота не существует: {BOT_COMMANDS_FILE}")
        return False, False, 0

    try:
        with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()

            if not content:
                logger.warning(f"Файл команд бота пуст: {BOT_COMMANDS_FILE}")
                return True, False, 0

            try:
                commands = json.loads(content)

                if not isinstance(commands, list):
                    logger.warning(f"Неверная структура файла команд (не список): {BOT_COMMANDS_FILE}")
                    return True, False, 0

                return True, True, len(commands)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка разбора JSON в файле команд: {e}")
                return True, False, 0
    except Exception as e:
        logger.error(f"Ошибка при проверке файла команд: {e}")
        traceback.print_exc()
        return True, False, 0


def analyze_commands():
    """
    Анализирует команды в файле и выводит статистику

    :return: {total, pending, completed, error, unknown}
    """
    stats = {
        'total': 0,
        'pending': 0,
        'completed': 0,
        'error': 0,
        'unknown': 0
    }

    exists, valid, count = check_bot_commands_file()

    if not exists or not valid:
        return stats

    try:
        with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)

        stats['total'] = len(commands)

        for cmd in commands:
            status = cmd.get('status', 'unknown')
            stats[status] = stats.get(status, 0) + 1

        return stats
    except Exception as e:
        logger.error(f"Ошибка при анализе команд: {e}")
        traceback.print_exc()
        return stats


def reset_pending_commands():
    """
    Сбрасывает метки времени для зависших команд со статусом pending

    :return: количество сброшенных команд
    """
    exists, valid, count = check_bot_commands_file()

    if not exists or not valid or count == 0:
        return 0

    try:
        with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)

        reset_count = 0
        now = time.time()

        for cmd in commands:
            if cmd.get('status') == 'pending':
                try:
                    # Проверяем возраст команды
                    cmd_time = float(cmd.get('timestamp', '0'))

                    # Если команда висит больше 10 минут, сбрасываем её метку времени
                    if now - cmd_time > 600:  # 10 минут в секундах
                        cmd['timestamp'] = '0'
                        reset_count += 1
                except:
                    # Если не удалось преобразовать timestamp, просто сбрасываем его
                    cmd['timestamp'] = '0'
                    reset_count += 1

        if reset_count > 0:
            # Сохраняем обновленные команды
            with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(commands, f, ensure_ascii=False, indent=4)

            logger.info(f"Сброшены метки времени для {reset_count} зависших команд")

        return reset_count
    except Exception as e:
        logger.error(f"Ошибка при сбросе меток времени команд: {e}")
        traceback.print_exc()
        return 0


def clear_completed_commands():
    """
    Удаляет выполненные и ошибочные команды из файла

    :return: количество удаленных команд
    """
    exists, valid, count = check_bot_commands_file()

    if not exists or not valid or count == 0:
        return 0

    try:
        with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)

        # Оставляем только команды со статусом pending
        pending_commands = [cmd for cmd in commands if cmd.get('status') == 'pending']

        removed_count = len(commands) - len(pending_commands)

        if removed_count > 0:
            # Сохраняем обновленные команды
            with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(pending_commands, f, ensure_ascii=False, indent=4)

            logger.info(f"Удалено {removed_count} выполненных/ошибочных команд")

        return removed_count
    except Exception as e:
        logger.error(f"Ошибка при очистке выполненных команд: {e}")
        traceback.print_exc()
        return 0


def monitor_commands(interval=5, duration=60):
    """
    Мониторит файл команд в течение указанного времени

    :param interval: Интервал проверки в секундах
    :param duration: Продолжительность мониторинга в секундах
    """
    logger.info(f"Запуск мониторинга команд на {duration} секунд с интервалом {interval} секунд")

    start_time = time.time()
    end_time = start_time + duration

    try:
        while time.time() < end_time:
            stats = analyze_commands()
            logger.info(f"Статистика команд: всего={stats['total']}, ожидают={stats['pending']}, "
                        f"выполнено={stats['completed']}, ошибок={stats['error']}")

            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Мониторинг остановлен пользователем")

    logger.info("Мониторинг завершен")


def main():
    """Основная функция скрипта"""
    import argparse

    parser = argparse.ArgumentParser(description='Проверка и управление очередью команд бота')
    parser.add_argument('--send-test', type=str, help='Отправить тестовое сообщение указанному пользователю')
    parser.add_argument('--reset', action='store_true', help='Сбросить метки времени для зависших команд')
    parser.add_argument('--clear', action='store_true', help='Удалить выполненные и ошибочные команды')
    parser.add_argument('--monitor', action='store_true', help='Мониторить очередь команд')
    parser.add_argument('--interval', type=int, default=5, help='Интервал мониторинга в секундах')
    parser.add_argument('--duration', type=int, default=60, help='Продолжительность мониторинга в секундах')

    args = parser.parse_args()

    # Проверка файла команд
    exists, valid, count = check_bot_commands_file()

    logger.info(f"Проверка файла команд: существует={exists}, корректен={valid}, команд={count}")

    if args.send_test:
        send_test_message(args.send_test)

    if args.reset:
        reset_pending_commands()

    if args.clear:
        clear_completed_commands()

    if args.monitor:
        monitor_commands(args.interval, args.duration)

    if not any([args.send_test, args.reset, args.clear, args.monitor]):
        # Если не указаны аргументы, просто выводим статистику
        stats = analyze_commands()
        print(f"Статистика команд: всего={stats['total']}, ожидают={stats['pending']}, "
              f"выполнено={stats['completed']}, ошибок={stats['error']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())