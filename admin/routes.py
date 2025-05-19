from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
from .auth import login_required, is_admin, add_global_admin, remove_global_admin, load_global_admins
from .utils import load_json, save_json, get_user_settings
import time
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

USERS_FILE = "../users.json"
LOGS_FILE = "../logs.json"
CONFIG_FILE = "../config.json"
SETTINGS_FILE = "../settings.json"
ADMIN_CREDENTIALS_FILE = "../admin_credentials.json"


def load_admin_credentials():
    if os.path.exists(ADMIN_CREDENTIALS_FILE):
        with open(ADMIN_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"username": "admin", "password": generate_password_hash("admin")}


def save_admin_credentials(credentials):
    with open(ADMIN_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(credentials, f, ensure_ascii=False, indent=4)


@admin_bp.route('/')
@login_required
def index():
    users = load_json(USERS_FILE)
    config = load_json(CONFIG_FILE)
    return render_template('admin/index.html', users=users, config=config)


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        credentials = load_admin_credentials()

        if username == credentials["username"] and check_password_hash(credentials["password"], password):
            session['logged_in'] = True
            flash('Успешный вход', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/update_credentials', methods=['POST'])
@login_required
def update_credentials():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Имя пользователя и пароль не могут быть пустыми', 'danger')
        return redirect(url_for('admin.settings'))

    credentials = {
        "username": username,
        "password": generate_password_hash(password)
    }

    save_admin_credentials(credentials)
    flash('Учетные данные администратора обновлены', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/settings')
@login_required
def settings():
    credentials = load_admin_credentials()
    config = load_json(CONFIG_FILE)
    global_admins = load_global_admins()
    return render_template('admin/settings.html',
                           username=credentials["username"],
                           config=config,
                           global_admins=global_admins)


@admin_bp.route('/update_config', methods=['POST'])
@login_required
def update_config():
    config = load_json(CONFIG_FILE)

    # Обновляем значения из формы
    for key in request.form:
        if key in config:
            # Преобразуем типы данных
            if isinstance(config[key], bool):
                config[key] = request.form.get(key) == 'on'
            elif isinstance(config[key], int):
                config[key] = int(request.form.get(key))
            elif isinstance(config[key], float):
                config[key] = float(request.form.get(key))
            else:
                config[key] = request.form.get(key)

    save_json(CONFIG_FILE, config)
    flash('Конфигурация обновлена', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/users')
@login_required
def users():
    users_data = load_json(USERS_FILE)
    settings_data = load_json(SETTINGS_FILE)
    return render_template('admin/users.html', users=users_data, settings=settings_data)


@admin_bp.route('/user/<user_id>')
@login_required
def user_details(user_id):
    users = load_json(USERS_FILE)
    settings = get_user_settings(user_id)

    if user_id in users:
        return render_template('admin/user_details.html',
                               user=users[user_id],
                               user_id=user_id,
                               settings=settings,
                               is_admin=is_admin(user_id))
    else:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.users'))


@admin_bp.route('/add_admin', methods=['POST'])
@login_required
def add_admin():
    user_id = request.form.get('user_id')
    if add_global_admin(user_id):
        flash('Пользователь добавлен как администратор', 'success')
    else:
        flash('Пользователь уже является администратором', 'warning')
    return redirect(url_for('admin.user_details', user_id=user_id))


@admin_bp.route('/remove_admin', methods=['POST'])
@login_required
def remove_admin():
    user_id = request.form.get('user_id')
    if remove_global_admin(user_id):
        flash('Пользователь удален из администраторов', 'success')
    else:
        flash('Пользователь не является администратором', 'warning')
    return redirect(url_for('admin.user_details', user_id=user_id))


@admin_bp.route('/logs')
@login_required
def logs():
    logs_data = load_json(LOGS_FILE)
    # Сортировка логов по времени в обратном порядке
    logs_data = sorted(logs_data, key=lambda x: x.get('timestamp', 0), reverse=True)

    # Преобразование timestamp в читаемую дату
    for log in logs_data:
        if 'timestamp' in log:
            log['datetime'] = datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('admin/logs.html', logs=logs_data)


@admin_bp.route('/api/update_user_settings', methods=['POST'])
@login_required
def update_user_settings():
    data = request.json
    user_id = data.get('user_id')
    settings = data.get('settings', {})

    if not user_id:
        return jsonify({'success': False, 'message': 'Не указан ID пользователя'})

    user_settings = load_json(SETTINGS_FILE)

    if user_id not in user_settings:
        user_settings[user_id] = {}

    for key, value in settings.items():
        user_settings[user_id][key] = value

    save_json(SETTINGS_FILE, user_settings)
    return jsonify({'success': True, 'message': 'Настройки пользователя обновлены'})