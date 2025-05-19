from flask import session, redirect, url_for, flash
from functools import wraps
import json
import os

GLOBAL_ADMINS_FILE = "../global_admins.json"

def load_global_admins():
    if os.path.exists(GLOBAL_ADMINS_FILE):
        try:
            with open(GLOBAL_ADMINS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []
    return []


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Необходимо войти в систему', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)

    return decorated_function


def is_admin(user_id):
    """Проверяет, является ли пользователь глобальным администратором"""
    global_admins = load_global_admins()
    user_id_str = str(user_id)
    return user_id_str in global_admins


def add_global_admin(user_id):
    """Добавляет пользователя в список глобальных администраторов"""
    global_admins = load_global_admins()
    user_id_str = str(user_id)

    if user_id_str not in global_admins:
        global_admins.append(user_id_str)

        with open(GLOBAL_ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(global_admins, f, ensure_ascii=False, indent=4)

        return True
    return False


def remove_global_admin(user_id):
    """Удаляет пользователя из списка глобальных администраторов"""
    global_admins = load_global_admins()
    user_id_str = str(user_id)

    if user_id_str in global_admins:
        global_admins.remove(user_id_str)

        with open(GLOBAL_ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(global_admins, f, ensure_ascii=False, indent=4)

        return True
    return False