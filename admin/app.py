from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import json
import os
import sys
from functools import wraps

# Добавляем родительскую директорию в путь, чтобы импортировать модули бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import DataStorage
from core.config import Config

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Измените на более безопасный ключ

storage = DataStorage()
config = Config()

# Данные для входа (в реальном приложении храните это в более безопасном месте)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin")


# Вспомогательная функция для проверки аутентификации
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Необходимо войти в систему', 'warning')
            return redirect(url_for('login'))
        return func(*args, **kwargs)

    return wrapper


@app.route('/')
@login_required
def index():
    users_count = len(storage.allowed_users)
    admins_count = len(storage.admins)
    streamers_count = len(storage.streamers)
    chats_count = len(storage.get_open_chats())

    return render_template(
        'index.html',
        users_count=users_count,
        admins_count=admins_count,
        streamers_count=streamers_count,
        chats_count=chats_count
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/users')
@login_required
def users():
    # Получаем список обычных пользователей (не админы и не стриммеры)
    users_data = []
    for user_id in storage.allowed_users:
        if user_id in storage.admins or user_id in storage.streamers:
            continue

        stats = storage.get_user_stats(user_id)
        settings = storage.get_user_settings(user_id)

        users_data.append({
            'id': user_id,
            'stats': stats,
            'settings': settings
        })

    return render_template('users.html', users=users_data)


@app.route('/streamers')
@login_required
def streamers():
    # Получаем список стриммеров
    streamers_data = []
    for user_id in storage.streamers:
        settings = storage.get_user_settings(user_id)

        streamers_data.append({
            'id': user_id,
            'settings': settings
        })

    return render_template('streamers.html', streamers=streamers_data)


@app.route('/user/<user_id>')
@login_required
def user_detail(user_id):
    if user_id not in storage.allowed_users:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('users'))

    stats = storage.get_user_stats(user_id)
    settings = storage.get_user_settings(user_id)
    is_admin = storage.is_admin(user_id)
    is_global_admin = storage.is_global_admin(user_id)
    is_streamer = storage.is_streamer(user_id)

    user_data = {
        'id': user_id,
        'stats': stats,
        'settings': settings,
        'is_admin': is_admin,
        'is_global_admin': is_global_admin,
        'is_streamer': is_streamer
    }

    return render_template('user_detail.html', user=user_data)


@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    user_id = request.form.get('user_id')
    if not user_id or not user_id.isdigit():
        flash('ID пользователя должен быть числом', 'danger')
        return redirect(url_for('users'))

        storage.add_user(user_id)
        flash(f'Пользователь с ID {user_id} успешно добавлен', 'success')
        return redirect(url_for('users'))

    @app.route('/users/delete/<user_id>', methods=['POST'])
    @login_required
    def delete_user(user_id):
        if storage.is_admin(user_id) or storage.is_global_admin(user_id) or storage.is_streamer(user_id):
            flash(f'Невозможно удалить пользователя с особыми правами', 'danger')
            return redirect(url_for('users'))

        if user_id in storage.allowed_users:
            storage.remove_user(user_id)
            flash(f'Пользователь с ID {user_id} удален', 'success')
        else:
            flash(f'Пользователь с ID {user_id} не найден', 'danger')

        return redirect(url_for('users'))

    @app.route('/admins')
    @login_required
    def admins():
        admins_data = []
        for admin_id in storage.admins:
            is_global = admin_id in storage.global_admins
            settings = storage.get_user_settings(admin_id)

            admins_data.append({
                'id': admin_id,
                'is_global': is_global,
                'settings': settings
            })

        return render_template('admins.html', admins=admins_data)

    @app.route('/admins/add', methods=['POST'])
    @login_required
    def add_admin():
        admin_id = request.form.get('admin_id')
        if not admin_id or not admin_id.isdigit():
            flash('ID администратора должен быть числом', 'danger')
            return redirect(url_for('admins'))

        storage.add_admin(admin_id)
        if admin_id not in storage.allowed_users:
            storage.add_user(admin_id)

        flash(f'Администратор с ID {admin_id} успешно добавлен', 'success')
        return redirect(url_for('admins'))

    @app.route('/admins/delete/<admin_id>', methods=['POST'])
    @login_required
    def delete_admin(admin_id):
        if admin_id in storage.global_admins:
            flash('Нельзя удалить глобального администратора', 'danger')
        elif admin_id in storage.admins:
            storage.remove_admin(admin_id)
            flash(f'Администратор с ID {admin_id} удален', 'success')
        else:
            flash(f'Администратор с ID {admin_id} не найден', 'danger')

        return redirect(url_for('admins'))

    @app.route('/streamers/add', methods=['POST'])
    @login_required
    def add_streamer():
        streamer_id = request.form.get('streamer_id')
        if not streamer_id or not streamer_id.isdigit():
            flash('ID стриммера должен быть числом', 'danger')
            return redirect(url_for('streamers'))

        storage.add_streamer(streamer_id)
        if streamer_id not in storage.allowed_users:
            storage.add_user(streamer_id)

        flash(f'Стриммер с ID {streamer_id} успешно добавлен', 'success')
        return redirect(url_for('streamers'))

    @app.route('/streamers/delete/<streamer_id>', methods=['POST'])
    @login_required
    def delete_streamer(streamer_id):
        if streamer_id in storage.streamers:
            storage.remove_streamer(streamer_id)
            flash(f'Стриммер с ID {streamer_id} удален', 'success')
        else:
            flash(f'Стриммер с ID {streamer_id} не найден', 'danger')

        return redirect(url_for('streamers'))

    @app.route('/chats')
    @login_required
    def chats():
        # Получаем все чаты (и открытые, и закрытые)
        all_chats = storage.chats

        # Форматируем данные для шаблона
        chats_data = []
        for chat_id, chat in all_chats.items():
            # Получаем настройки пользователя для отображения имени/ника
            user_id = chat['user_id']
            user_settings = storage.get_user_settings(user_id)

            chats_data.append({
                'id': chat_id,
                'user_id': user_id,
                'status': chat['status'],
                'created_at': chat['created_at'],
                'closed_at': chat['closed_at'],
                'message_count': len(chat['messages']),
                'settings': user_settings
            })

        return render_template('chats.html', chats=chats_data)

    @app.route('/chat/<chat_id>')
    @login_required
    def chat_detail(chat_id):
        chat = storage.get_chat(chat_id)

        if not chat:
            flash('Чат не найден', 'danger')
            return redirect(url_for('chats'))

        # Получаем настройки пользователя для отображения имени/ника
        user_id = chat['user_id']
        user_settings = storage.get_user_settings(user_id)

        # Добавляем информацию об отправителе к каждому сообщению
        messages = []
        for msg in chat['messages']:
            sender_id = msg['user_id']
            sender_type = 'Администратор'

            if storage.is_streamer(sender_id):
                sender_type = 'Стриммер'
            elif storage.is_global_admin(sender_id):
                sender_type = 'Глобальный администратор'

            messages.append({
                'sender_id': sender_id,
                'sender_type': sender_type,
                'text': msg['text'],
                'timestamp': msg['timestamp']
            })

        chat_data = {
            'id': chat_id,
            'user_id': user_id,
            'status': chat['status'],
            'created_at': chat['created_at'],
            'closed_at': chat['closed_at'],
            'messages': messages,
            'user_settings': user_settings
        }

        return render_template('chat_detail.html', chat=chat_data)

    @app.route('/chat/close/<chat_id>', methods=['POST'])
    @login_required
    def close_chat(chat_id):
        if storage.close_chat(chat_id):
            flash(f'Чат {chat_id} успешно закрыт', 'success')
        else:
            flash(f'Не удалось закрыть чат {chat_id}', 'danger')

        return redirect(url_for('chat_detail', chat_id=chat_id))

    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        if request.method == 'POST':
            # Обновление настроек администратора
            new_username = request.form.get('username')
            new_password = request.form.get('password')

            global ADMIN_USERNAME, ADMIN_PASSWORD_HASH

            if new_username:
                ADMIN_USERNAME = new_username

            if new_password:
                ADMIN_PASSWORD_HASH = generate_password_hash(new_password)

            flash('Настройки успешно обновлены', 'success')

        return render_template('settings.html', username=ADMIN_USERNAME)

    if __name__ == '__main__':
        app.run(debug=True)