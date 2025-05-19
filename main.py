import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import setup_routers

# Настройка логирования
logging.basicConfig(level=logging.INFO)


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
                # Инициализация бота и диспетчера
                bot = Bot(token=token)
                dp = Dispatcher(storage=MemoryStorage())

                # Подключение роутеров
                dp.include_router(setup_routers())

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