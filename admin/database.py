import json
import os
from datetime import datetime

# Пути к файлам JSON (используются те же файлы, что и в боте)
STATS_FILE = "../user_stats.json"
SETTINGS_FILE = "../user_settings.json"
ALLOWED_USERS_FILE = "../allowed_users.json"
ADMINS_FILE = "../admins.json"
GLOBAL_ADMINS_FILE = "../global_admins.json"


def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE, ALLOWED_USERS_FILE] else {}
                return json.loads(content)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE, ALLOWED_USERS_FILE] else {}
    return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE, ALLOWED_USERS_FILE] else {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_list():
    """Получить список всех пользователей из allowed_users.json"""
    allowed_users = load_json(ALLOWED_USERS_FILE)
    user_stats = load_json(STATS_FILE)
    user_settings = load_json(SETTINGS_FILE)

    users = []
    for user_id in allowed_users:
        user_id = str(user_id)
        user = {
            'id': user_id,
            'stats': user_stats.get(user_id, {'hours': 0, 'amount': 0}),
            'settings': user_settings.get(user_id, {})
        }
        users.append(user)

    return users


def get_user_details(user_id):
    """Получить подробную информацию о пользователе"""
    allowed_users = load_json(ALLOWED_USERS_FILE)
    user_id = str(user_id)

    if user_id not in [str(u) for u in allowed_users]:
        return None

    user_stats = load_json(STATS_FILE)
    user_settings = load_json(SETTINGS_FILE)

    return {
        'id': user_id,
        'stats': user_stats.get(user_id, {'hours': 0, 'amount': 0}),
        'settings': user_settings.get(user_id, {
            'payout_method': '',
            'requisites': '',
            'country': '',
            'bank': ''
        }),
        'is_admin': user_id in [str(a) for a in load_json(ADMINS_FILE)],
        'is_global_admin': user_id in [str(a) for a in load_json(GLOBAL_ADMINS_FILE)]
    }


def get_admins():
    """Получить список обычных администраторов"""
    return load_json(ADMINS_FILE)


def get_global_admins():
    """Получить список глобальных администраторов"""
    return load_json(GLOBAL_ADMINS_FILE)


def add_user(user_id):
    """Добавить пользователя в allowed_users.json"""
    user_id = str(user_id)
    allowed_users = load_json(ALLOWED_USERS_FILE)

    if user_id in [str(u) for u in allowed_users]:
        return {'success': False, 'message': f'Пользователь с ID {user_id} уже существует'}

    allowed_users.append(user_id)
    save_json(ALLOWED_USERS_FILE, allowed_users)
    return {'success': True, 'message': f'Пользователь с ID {user_id} успешно добавлен'}


def remove_user(user_id):
    """Удалить пользователя из allowed_users.json"""
    user_id = str(user_id)
    allowed_users = load_json(ALLOWED_USERS_FILE)

    if user_id not in [str(u) for u in allowed_users]:
        return {'success': False, 'message': f'Пользователь с ID {user_id} не найден'}

    allowed_users = [str(u) for u in allowed_users if str(u) != user_id]
    save_json(ALLOWED_USERS_FILE, allowed_users)

    return {'success': True, 'message': f'Пользователь с ID {user_id} успешно удален'}


def add_admin(user_id):
    """Добавить администратора в admins.json"""
    user_id = str(user_id)
    admins = load_json(ADMINS_FILE)

    if user_id in [str(a) for a in admins]:
        return {'success': False, 'message': f'Пользователь с ID {user_id} уже администратор'}

    # Также добавляем пользователя в allowed_users, если его там нет
    allowed_users = load_json(ALLOWED_USERS_FILE)
    if user_id not in [str(u) for u in allowed_users]:
        allowed_users.append(user_id)
        save_json(ALLOWED_USERS_FILE, allowed_users)

    admins.append(user_id)
    save_json(ADMINS_FILE, admins)
    return {'success': True, 'message': f'Пользователь с ID {user_id} назначен администратором'}


def remove_admin(admin_id):
    """Удалить администратора из admins.json"""
    admin_id = str(admin_id)
    admins = load_json(ADMINS_FILE)

    if admin_id not in [str(a) for a in admins]:
        return {'success': False, 'message': f'Администратор с ID {admin_id} не найден'}

    # Проверка, является ли админ глобальным админом
    global_admins = load_json(GLOBAL_ADMINS_FILE)
    if admin_id in [str(a) for a in global_admins]:
        return {'success': False, 'message': f'Нельзя удалить глобального администратора'}

    admins = [str(a) for a in admins if str(a) != admin_id]
    save_json(ADMINS_FILE, admins)

    return {'success': True, 'message': f'Администратор с ID {admin_id} успешно удален'}


def update_user_settings(user_id, data):
    """Обновить настройки пользователя"""
    user_id = str(user_id)
    user_settings = load_json(SETTINGS_FILE)

    if user_id not in user_settings:
        user_settings[user_id] = {}

    for key, value in data.items():
        user_settings[user_id][key] = value

    save_json(SETTINGS_FILE, user_settings)
    return {'success': True, 'message': 'Настройки пользователя обновлены'}