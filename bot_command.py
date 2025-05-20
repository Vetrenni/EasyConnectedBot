import os
import json
import logging
import time
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# Путь к файлу с командами бота
BOT_COMMANDS_FILE = "bot_commands.json"
# Максимальный размер файла команд (в байтах)
MAX_COMMANDS_FILE_SIZE = 1024 * 1024  # 1 МБ


def cleanup_commands_file():
    """
    Очищает файл команд от выполненных и устаревших команд
    """
    if not os.path.exists(BOT_COMMANDS_FILE):
        return

    try:
        with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)

        # Фильтруем команды, оставляя только ожидающие выполнения
        pending_commands = [cmd for cmd in commands if cmd.get('status') == 'pending']

        # Если есть изменения, сохраняем файл
        if len(commands) != len(pending_commands):
            with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(pending_commands, f, ensure_ascii=False, indent=4)
            logger.info(f"Очищено {len(commands) - len(pending_commands)} завершенных команд")
    except Exception as e:
        logger.error(f"Ошибка при очистке файла команд: {e}")


def send_bot_command(command, params):
    """
    Отправляет команду боту через файл

    :param command: Название команды
    :param params: Параметры команды
    :return: True если команда была добавлена в очередь
    """
    logger.debug(f"Отправка команды боту: {command} с параметрами {params}")

    # Очищаем файл команд от завершенных, если он существует
    if os.path.exists(BOT_COMMANDS_FILE):
        cleanup_commands_file()

    # Создаем структуру команды
    cmd = {
        "command": command,
        "params": params,
        "status": "pending",
        "timestamp": str(time.time())  # Используем время в секундах как временную метку
    }

    # Загружаем текущий список команд
    commands = []
    if os.path.exists(BOT_COMMANDS_FILE):
        try:
            with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                file_content = f.read()
                if file_content.strip():
                    commands = json.loads(file_content)
                else:
                    commands = []
        except Exception as e:
            logger.error(f"Ошибка при чтении файла команд: {e}")
            traceback.print_exc()
            # Создаем резервную копию поврежденного файла
            if os.path.exists(BOT_COMMANDS_FILE):
                backup_file = f"{BOT_COMMANDS_FILE}.bak.{int(time.time())}"
                try:
                    os.rename(BOT_COMMANDS_FILE, backup_file)
                    logger.info(f"Создана резервная копия поврежденного файла: {backup_file}")
                except:
                    pass
            commands = []

    # Проверяем размер файла команд
    if len(commands) > 100:  # Если слишком много команд
        logger.warning(f"Слишком много команд в очереди: {len(commands)}. Очистка.")
        # Оставляем только последние 50 команд
        commands = commands[-50:]

    # Добавляем новую команду
    commands.append(cmd)

    # Сохраняем обновленный список
    try:
        with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(commands, f, ensure_ascii=False, indent=4)
        logger.debug(f"Команда {command} добавлена в очередь")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении команды: {e}")
        traceback.print_exc()
        return False


def send_message_to_user(user_id, message_text):
    """
    Отправляет сообщение пользователю через бота

    :param user_id: ID пользователя
    :param message_text: Текст сообщения
    :return: True если команда была добавлена в очередь
    """
    logger.debug(f"Отправка сообщения пользователю {user_id}: {message_text[:50]}...")

    # Создаем структуру команды
    cmd = {
        "command": "send_message",
        "params": {
            "user_id": str(user_id),  # Преобразуем в строку для безопасности
            "text": message_text
        },
        "status": "pending",
        "timestamp": str(time.time())  # Используем время в секундах как временную метку
    }

    # Загружаем текущий список команд
    commands = []
    if os.path.exists(BOT_COMMANDS_FILE):
        try:
            with open(BOT_COMMANDS_FILE, 'r', encoding='utf-8') as f:
                file_content = f.read()
                if file_content.strip():
                    commands = json.loads(file_content)
                else:
                    commands = []
        except Exception as e:
            logger.error(f"Ошибка при чтении файла команд: {e}")
            traceback.print_exc()
            commands = []

    # Добавляем новую команду
    commands.append(cmd)

    # Сохраняем обновленный список
    try:
        with open(BOT_COMMANDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(commands, f, ensure_ascii=False, indent=4)
        logger.debug(f"Команда send_message добавлена в очередь для пользователя {user_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении команды: {e}")
        traceback.print_exc()
        return False