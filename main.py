import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

from handlers import setup_routers

def write_pid_file():
    """Записывает PID процесса в файл"""
    pid_file = "bot.pid"
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        print(f"PID {os.getpid()} записан в файл {pid_file}")
    except Exception as e:
        print(f"Ошибка при записи PID в файл: {e}")

# В функции main() добавьте вызов этой функции в начале:
async def main():
    # Записываем PID процесса в файл
    write_pid_file()

# Настройка логирования
logging.basicConfig(level=logging.INFO)


# Функция для проверки команд бота
async def check_bot_commands(bot):
    """Проверяет наличие команд для бота и выполняет их"""
    bot_commands_file = "bot_commands.json"

    while True:
        if os.path.exists(bot_commands_file):
            try:
                # Проверяем, что файл не пустой
                if os.path.getsize(bot_commands_file) == 0:
                    # Создаем пустой массив в файле
                    with open(bot_commands_file, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                    await asyncio.sleep(3)
                    continue

                # Пытаемся загрузить содержимое файла
                with open(bot_commands_file, 'r', encoding='utf-8') as f:
                    try:
                        file_content = f.read()
                        if not file_content.strip():
                            commands = []
                        else:
                            commands = json.loads(file_content)
                    except json.JSONDecodeError as e:
                        print(f"Ошибка при разборе JSON: {e}")
                        # Создаем резервную копию
                        backup_file = f"{bot_commands_file}.bak.{int(time.time())}"
                        shutil.copy2(bot_commands_file, backup_file)
                        print(f"Создана резервная копия поврежденного файла: {backup_file}")
                        # Создаем пустой массив в файле
                        with open(bot_commands_file, 'w', encoding='utf-8') as f:
                            json.dump([], f)
                        await asyncio.sleep(3)
                        continue

                # Обрабатываем команды со статусом "pending"
                pending_commands = [cmd for cmd in commands if cmd.get("status") == "pending"]

                if pending_commands:
                    print(f"Найдено {len(pending_commands)} команд в очереди")

                    # Обновляем команды - сначала копируем список
                    updated_commands = commands.copy()

                    # Обрабатываем каждую команду
                    for cmd in pending_commands:
                        cmd_type = cmd.get("command")
                        params = cmd.get("params", {})
                        print(f"Обработка команды: {cmd_type} с параметрами {params}")

                        try:
            if cmd_type == "send_message":
                user_id = params.get("user_id")
                text = params.get("text")

                if user_id and text:
                    print(f"Отправка сообщения пользователю {user_id}: {text[:30]}...")
                    try:
                        # Преобразуем user_id в целое число
                        user_id_int = int(user_id)
                        await bot.send_message(user_id_int, text)

                        # Обновляем статус команды на "completed"
                        cmd_index = commands.index(cmd)
                        updated_commands[cmd_index]["status"] = "completed"
                        updated_commands[cmd_index]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        print(f"Сообщение успешно отправлено пользователю {user_id}")
                    except Exception as e:
                        # Обновляем статус команды на "error"
                        cmd_index = commands.index(cmd)
                        updated_commands[cmd_index]["status"] = "error"
                        updated_commands[cmd_index]["error"] = f"Ошибка отправки: {str(e)}"
                        print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
                else:
                    # Обновляем статус команды на "error"
                    cmd_index = commands.index(cmd)
                    updated_commands[cmd_index]["status"] = "error"
                    updated_commands[cmd_index]["error"] = "Missing user_id or text"
                    print(f"Отсутствует user_id или text в команде {cmd}")
            except Exception as e:
            # Обновляем статус команды на "error"
            cmd_index = commands.index(cmd)
            updated_commands[cmd_index]["status"] = "error"
            updated_commands[cmd_index]["error"] = str(e)
            print(f"Ошибка при обработке команды {cmd_type}: {e}")
            import traceback
            traceback.print_exc()

            # Сохраняем обновленные статусы
        try:
            with open(bot_commands_file, 'w', encoding='utf-8') as f:
                json.dump(updated_commands, f, ensure_ascii=False, indent=4)
            print("Статусы команд успешно обновлены")

            # Очистка обработанных команд
            # Удаляем команды со статусом "completed" или "error", которые старше 1 часа
            now = time.time()
            commands_to_keep = []
            for cmd in updated_commands:
                if cmd.get("status") == "pending":
                    commands_to_keep.append(cmd)
                elif cmd.get("status") in ["completed", "error"]:
                    # Проверяем возраст команды
                    cmd_time = float(cmd.get("timestamp", 0))
                    if now - cmd_time < 3600:  # 1 час в секундах
                        commands_to_keep.append(cmd)

            # Если произошла очистка, сохраняем очищенный список
            if len(commands_to_keep) < len(updated_commands):
                with open(bot_commands_file, 'w', encoding='utf-8') as f:
                    json.dump(commands_to_keep, f, ensure_ascii=False, indent=4)
                print(f"Очищено {len(updated_commands) - len(commands_to_keep)} обработанных команд")
        except Exception as e:
            print(f"Ошибка при сохранении обновленных статусов команд: {e}")
            import traceback
            traceback.print_exc()

        except Exception as e:
            print(f"Ошибка при обработке команд бота: {e}")
            import traceback
            traceback.print_exc()

            # Проверяем каждые 3 секунды
        await asyncio.sleep(3)


async def main():
    # Загрузка конфигурации
    config_path = 'config/config.json'

    print(f"Проверяем существование конфигурации: {os.path.exists(config_path)}")

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Проверяем оба возможных ключа для токена
            token = config.get('BOT_TOKEN') or config.get('token')
            print(f"Загруженный токен: {token[:5]}...{token[-5:] if token else None}")

            if token:
                # Синхронизация данных с админкой при запуске
                try:
                    print("Синхронизация данных с админкой при запуске...")
                    admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admin')
                    sys.path.append(admin_path)

                    from sync_bot import sync_all_from_admin_to_bot
                    sync_count = sync_all_from_admin_to_bot()
                    print(f"Синхронизация завершена: {sync_count} файлов обновлено")
                except Exception as e:
                    print(f"Ошибка при синхронизации с админкой: {e}")

                # Инициализация бота и диспетчера
                bot = Bot(token=token)
                dp = Dispatcher(storage=MemoryStorage())

                # Подключение роутеров
                dp.include_router(setup_routers())

                # Запускаем задачу проверки команд бота
                asyncio.create_task(check_bot_commands(bot))

                # Запуск бота в режиме long polling
                await bot.delete_webhook(drop_pending_updates=True)
                await dp.start_polling(bot)
            else:
                print("Токен не найден в конфигурационном файле")
        except Exception as e:
            print(f"Произошла ошибка при чтении конфигурации: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Файл конфигурации не найден")


if __name__ == "__main__":
    asyncio.run(main())
