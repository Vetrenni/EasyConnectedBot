import json
import os
import uuid
from datetime import datetime


class DataStorage:
    def __init__(self):
        # Загружаем конфигурацию, если она есть
        config_path = 'config/config.json'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                initial_global_admins = config.get('initial_global_admins', [])
                files_config = config.get('files', {})
            except Exception as e:
                print(f"Ошибка при загрузке конфигурации: {e}")
                initial_global_admins = []
                files_config = {}
        else:
            initial_global_admins = []
            files_config = {}

        self.admin_file = files_config.get('admins', "admins.json")
        self.global_admin_file = files_config.get('global_admins', "global_admins.json")
        self.user_file = files_config.get('allowed_users', "allowed_users.json")
        self.streamer_file = "streamers.json"
        self.stats_file = files_config.get('stats', "user_stats.json")
        self.settings_file = files_config.get('settings', "user_settings.json")
        self.chats_file = "chats.json"

        print(f"Файлы хранения данных:")
        print(f"- Админы: {self.admin_file}")
        print(f"- Глобальные админы: {self.global_admin_file}")
        print(f"- Пользователи: {self.user_file}")
        print(f"- Стриммеры: {self.streamer_file}")
        print(f"- Статистика: {self.stats_file}")
        print(f"- Настройки: {self.settings_file}")
        print(f"- Чаты: {self.chats_file}")
        print(f"Путь к файлу чатов: {os.path.abspath(self.chats_file)}")

        # Проверяем существование всех файлов и создаем их при необходимости
        self._check_file(self.admin_file, [])
        self._check_file(self.global_admin_file, initial_global_admins)
        self._check_file(self.user_file, [])
        self._check_file(self.streamer_file, [])
        self._check_file(self.stats_file, {})
        self._check_file(self.settings_file, {})
        self._check_file(self.chats_file, {})

        # Загружаем все данные
        self.admins = self._load_from_file(self.admin_file)
        self.global_admins = self._load_from_file(self.global_admin_file)
        self.allowed_users = self._load_from_file(self.user_file)
        self.streamers = self._load_from_file(self.streamer_file)
        self.user_stats = self._load_from_file(self.stats_file)
        self.user_settings = self._load_from_file(self.settings_file)
        self.chats = self._load_from_file(self.chats_file)

        # Добавляем всех глобальных админов из конфигурации, если их еще нет в файле
        for admin_id in initial_global_admins:
            if admin_id not in self.global_admins:
                self.global_admins.append(admin_id)
                self._save_to_file(self.global_admin_file, self.global_admins)

        print(f"Загружено админов: {len(self.admins)}")
        print(f"Загружено глобальных админов: {len(self.global_admins)}")
        print(f"Загружено пользователей: {len(self.allowed_users)}")
        print(f"Загружено стриммеров: {len(self.streamers)}")
        print(f"Загружено чатов: {len(self.chats)}")

    def _check_file(self, file_path, default_data):
        """Проверка существования файла и создание его при необходимости"""
        if not os.path.exists(file_path):
            print(f"Создание файла {file_path} с данными по умолчанию")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)

    def _load_from_file(self, file_path):
        """Загрузка данных из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке данных из {file_path}: {e}")
            return [] if file_path.endswith(
                ('admins.json', 'global_admins.json', 'allowed_users.json', 'streamers.json')) else {}

    def _save_to_file(self, file_path, data):
        """Сохранение данных в файл"""
        try:
            print(f"Сохранение данных в файл {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Данные успешно сохранены в {file_path}")
        except Exception as e:
            print(f"ОШИБКА при сохранении в файл {file_path}: {e}")
            raise

    def is_admin(self, user_id):
        """Проверка, является ли пользователь администратором"""
        return str(user_id) in self.admins

    def is_global_admin(self, user_id):
        """Проверка, является ли пользователь глобальным администратором"""
        return str(user_id) in self.global_admins

    def is_allowed(self, user_id):
        """Проверка, разрешен ли доступ пользователю"""
        return (str(user_id) in self.allowed_users or
                self.is_admin(user_id) or
                self.is_global_admin(user_id) or
                self.is_streamer(user_id))

    def is_streamer(self, user_id):
        """Проверка, является ли пользователь стриммером"""
        return str(user_id) in self.streamers

    def add_user(self, user_id):
        """Добавление пользователя в список разрешенных"""
        if str(user_id) not in self.allowed_users:
            self.allowed_users.append(str(user_id))
            self._save_to_file(self.user_file, self.allowed_users)

    def remove_user(self, user_id):
        """Удаление пользователя из списка разрешенных"""
        if str(user_id) in self.allowed_users:
            self.allowed_users.remove(str(user_id))
            self._save_to_file(self.user_file, self.allowed_users)

    def add_admin(self, user_id):
        """Добавление пользователя в список администраторов"""
        if str(user_id) not in self.admins:
            self.admins.append(str(user_id))
            self._save_to_file(self.admin_file, self.admins)

    def remove_admin(self, user_id):
        """Удаление пользователя из списка администраторов"""
        if str(user_id) in self.admins:
            self.admins.remove(str(user_id))
            self._save_to_file(self.admin_file, self.admins)

    def add_streamer(self, user_id):
        """Добавление пользователя в список стриммеров"""
        if str(user_id) not in self.streamers:
            # Добавляем также в разрешенных пользователей, если еще не добавлен
            if str(user_id) not in self.allowed_users:
                self.add_user(user_id)

            self.streamers.append(str(user_id))
            self._save_to_file(self.streamer_file, self.streamers)
            print(f"Пользователь {user_id} добавлен в список стриммеров")

    def remove_streamer(self, user_id):
        """Удаление пользователя из списка стриммеров"""
        if str(user_id) in self.streamers:
            self.streamers.remove(str(user_id))
            self._save_to_file(self.streamer_file, self.streamers)

    def update_stats(self, user_id, hours, amount):
        """Обновление статистики пользователя"""
        user_id = str(user_id)

        if user_id not in self.user_stats:
            self.user_stats[user_id] = {'hours': 0, 'amount': 0}

        current_stats = self.user_stats[user_id]
        self.user_stats[user_id] = {
            'hours': current_stats['hours'] + hours,
            'amount': current_stats['amount'] + amount
        }

        self._save_to_file(self.stats_file, self.user_stats)

    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        user_id = str(user_id)
        return self.user_stats.get(user_id, {'hours': 0, 'amount': 0})

    def update_settings(self, user_id, key, value):
        """Обновление настроек пользователя"""
        user_id = str(user_id)

        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}

        self.user_settings[user_id][key] = value
        self._save_to_file(self.settings_file, self.user_settings)

    def get_user_settings(self, user_id):
        """Получение настроек пользователя"""
        user_id = str(user_id)
        return self.user_settings.get(user_id, {})

    def create_chat(self, user_id, initial_message):
        """Создание нового чата"""
        chat_id = str(uuid.uuid4())
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        chat_data = {
            'user_id': str(user_id),
            'status': 'open',
            'created_at': now,
            'closed_at': None,
            'messages': [
                {
                    'user_id': str(user_id),
                    'text': initial_message,
                    'timestamp': now
                }
            ]
        }

        print(f"Создание нового чата: {chat_id} от пользователя {user_id}")
        print(f"Данные чата: {chat_data}")

        self.chats[chat_id] = chat_data

        # Сохраняем в файл
        try:
            self._save_to_file(self.chats_file, self.chats)
            print(f"Чаты сохранены в файл {self.chats_file}")
            print(f"Всего чатов после добавления: {len(self.chats)}")
        except Exception as e:
            print(f"ОШИБКА при сохранении чатов: {e}")

        return chat_id

    def add_message_to_chat(self, chat_id, user_id, message_text):
        """Добавление сообщения в чат"""
        if chat_id not in self.chats or self.chats[chat_id]['status'] == 'closed':
            print(f"Попытка добавить сообщение в несуществующий или закрытый чат: {chat_id}")
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_message = {
            'user_id': str(user_id),
            'text': message_text,
            'timestamp': now
        }

        print(f"Добавление сообщения в чат {chat_id} от пользователя {user_id}")

        self.chats[chat_id]['messages'].append(new_message)

        try:
            self._save_to_file(self.chats_file, self.chats)
            print(f"Чаты с новым сообщением сохранены в файл {self.chats_file}")
        except Exception as e:
            print(f"ОШИБКА при сохранении чатов после добавления сообщения: {e}")
            return False

        return True

    def close_chat(self, chat_id):
        """Закрытие чата"""
        if chat_id not in self.chats or self.chats[chat_id]['status'] == 'closed':
            print(f"Попытка закрыть несуществующий или уже закрытый чат: {chat_id}")
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.chats[chat_id]['status'] = 'closed'
        self.chats[chat_id]['closed_at'] = now

        print(f"Закрытие чата {chat_id}")

        try:
            self._save_to_file(self.chats_file, self.chats)
            print(f"Чаты после закрытия сохранены в файл {self.chats_file}")
        except Exception as e:
            print(f"ОШИБКА при сохранении чатов после закрытия: {e}")
            return False

        return True

    def get_chat(self, chat_id):
        """Получение данных чата"""
        chat = self.chats.get(chat_id)
        print(f"Запрос чата {chat_id}: {'найден' if chat else 'не найден'}")
        return chat

    def get_open_chats(self):
        """Получение всех открытых чатов"""
        print(f"Получение открытых чатов. Всего чатов: {len(self.chats)}")

        open_chats = {
            chat_id: chat_data
            for chat_id, chat_data in self.chats.items()
            if chat_data['status'] == 'open'
        }

        print(f"Найдено открытых чатов: {len(open_chats)}")
        for chat_id in open_chats:
            print(f"- Открытый чат {chat_id} с пользователем {open_chats[chat_id]['user_id']}")

        return open_chats