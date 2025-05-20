import os
import sys
import subprocess
import time
import threading

# Получаем абсолютный путь к текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_DIR = os.path.join(BASE_DIR, '')
ADMIN_DIR = os.path.join(BOT_DIR, 'admin')


def run_bot():
    """Запуск Telegram-бота"""
    print(f"Запуск Telegram-бота из директории {BOT_DIR}...")

    # Проверяем существование файла main.py
    main_py_path = os.path.join(BOT_DIR, 'main.py')
    if not os.path.exists(main_py_path):
        print(f"Ошибка: Файл {main_py_path} не найден!")
        print("Доступные файлы в директории:")
        for file in os.listdir(BOT_DIR):
            print(f"- {file}")
        return

    # Сохраняем текущую директорию
    original_dir = os.getcwd()

    try:
        # Переходим в директорию бота
        os.chdir(BOT_DIR)
        print(f"Изменена рабочая директория на {os.getcwd()}")

        # Запускаем бота
        subprocess.call([sys.executable, 'main.py'])
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        # Возвращаемся в исходную директорию
        os.chdir(original_dir)


def run_admin():
    """Запуск админ-панели"""
    print(f"Запуск админ-панели из директории {ADMIN_DIR}...")

    # Проверяем существование файла app.py
    app_py_path = os.path.join(ADMIN_DIR, 'app.py')
    if not os.path.exists(app_py_path):
        print(f"Ошибка: Файл {app_py_path} не найден!")
        print("Доступные файлы в директории:")
        if os.path.exists(ADMIN_DIR):
            for file in os.listdir(ADMIN_DIR):
                print(f"- {file}")
        else:
            print(f"Директория {ADMIN_DIR} не существует!")
        return

    # Сохраняем текущую директорию
    original_dir = os.getcwd()

    try:
        # Переходим в директорию админки
        os.chdir(ADMIN_DIR)
        print(f"Изменена рабочая директория на {os.getcwd()}")

        # Запускаем админку
        subprocess.call([sys.executable, 'app.py'])
    except Exception as e:
        print(f"Ошибка при запуске админ-панели: {e}")
    finally:
        # Возвращаемся в исходную директорию
        os.chdir(original_dir)


def sync_files():
    """Синхронизация файлов данных между ботом и админкой"""
    print(f"Синхронизация файлов между {BOT_DIR} и {ADMIN_DIR}...")

    # Проверяем существование файла sync_bot.py
    sync_py_path = os.path.join(ADMIN_DIR, 'sync_bot.py')
    if not os.path.exists(sync_py_path):
        print(f"Ошибка: Файл {sync_py_path} не найден!")
        return

    # Сохраняем текущую директорию
    original_dir = os.getcwd()

    try:
        # Переходим в директорию админки
        os.chdir(ADMIN_DIR)
        print(f"Изменена рабочая директория на {os.getcwd()}")

        # Запускаем синхронизацию
        subprocess.call([sys.executable, 'sync_bot.py', '--direction=to_admin'])
    except Exception as e:
        print(f"Ошибка при синхронизации файлов: {e}")
    finally:
        # Возвращаемся в исходную директорию
        os.chdir(original_dir)


def show_directory_structure():
    """Показывает структуру директорий для отладки"""
    print("\n=== Структура директорий ===")
    print(f"Текущая директория: {os.getcwd()}")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"BOT_DIR: {BOT_DIR}")
    print(f"ADMIN_DIR: {ADMIN_DIR}")

    print("\nСодержимое BASE_DIR:")
    for item in os.listdir(BASE_DIR):
        print(f"- {item}")

    print("\nСодержимое родительской директории:")
    parent_dir = os.path.dirname(BASE_DIR)
    for item in os.listdir(parent_dir):
        print(f"- {item}")


if __name__ == "__main__":
    # Показываем структуру директорий для отладки
    show_directory_structure()

    # Вручную указываем пути (закомментируйте после настройки)
    # BOT_DIR = "C:/Users/New/PycharmProjects/PythonProject/my_bot"
    # ADMIN_DIR = "C:/Users/New/PycharmProjects/PythonProject/my_bot/admin"

    # Предлагаем пользователю указать директории
    print("\nТекущие пути:")
    print(f"Директория бота: {BOT_DIR}")
    print(f"Директория админки: {ADMIN_DIR}")

    use_custom = input("Использовать эти пути? (y/n): ").strip().lower()
    if use_custom != 'y':
        BOT_DIR = input("Введите полный путь к директории бота: ").strip()
        ADMIN_DIR = input("Введите полный путь к директории админки: ").strip()

    # Проверяем указанные пути
    if not os.path.exists(BOT_DIR):
        print(f"Ошибка: Директория бота {BOT_DIR} не существует!")
        sys.exit(1)

    if not os.path.exists(ADMIN_DIR):
        print(f"Ошибка: Директория админки {ADMIN_DIR} не существует!")
        sys.exit(1)

    main_py = os.path.join(BOT_DIR, 'main.py')
    app_py = os.path.join(ADMIN_DIR, 'app.py')

    if not os.path.exists(main_py):
        print(f"Ошибка: Файл {main_py} не найден!")
        sys.exit(1)

    if not os.path.exists(app_py):
        print(f"Ошибка: Файл {app_py} не найден!")
        sys.exit(1)

    # Файл синхронизации может отсутствовать
    sync_py = os.path.join(ADMIN_DIR, 'sync_bot.py')
    if not os.path.exists(sync_py):
        print(f"Предупреждение: Файл синхронизации {sync_py} не найден. Синхронизация будет пропущена.")
        do_sync = False
    else:
        do_sync = True

    # Запуск системы
    print("\n=== Запуск системы ===")

    # Синхронизируем файлы, если возможно
    if do_sync:
        print("Синхронизация файлов...")
        sync_files()

    # Спрашиваем, что запустить
    start_bot = input("Запустить бота? (y/n): ").strip().lower() == 'y'
    start_admin = input("Запустить админ-панель? (y/n): ").strip().lower() == 'y'

    bot_thread = None
    admin_thread = None

    if start_bot:
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.start()
        print("Бот запущен в отдельном потоке.")

    if start_admin:
        # Даем боту время на инициализацию, если он запущен
        if start_bot:
            time.sleep(2)

        admin_thread = threading.Thread(target=run_admin)
        admin_thread.start()
        print("Админ-панель запущена в отдельном потоке.")

    # Ждем завершения потоков
    if bot_thread:
        bot_thread.join()

    if admin_thread:
        admin_thread.join()