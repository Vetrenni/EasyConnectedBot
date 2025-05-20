from core.storage import DataStorage
import os
import json
import logging

logger = logging.getLogger(__name__)


class SyncedDataStorage(DataStorage):
    """Простая версия SyncedDataStorage, которая наследует все методы от DataStorage"""

    def __init__(self):
        super().__init__()
        logger.info("Инициализировано синхронизированное хранилище данных")
        # Все методы наследуются от базового класса

    def _reload_all(self):
        """Перезагружает все данные из файлов"""
        self._reload_users()
        self._reload_admins()
        self._reload_global_admins()
        self._reload_streamers()
        self._reload_stats()
        self._reload_settings()
        self._reload_chats()

    def _reload_users(self):
        """Перезагружает список пользователей из файла"""
        if os.path.exists(self.user_file):
            try:
                with open(self.user_file, 'r', encoding='utf-8') as f:
                    self.allowed_users = json.load(f)
                logger.debug(f"Перезагружены пользователи: {len(self.allowed_users)}")
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке пользователей: {e}")

    def _reload_admins(self):
        """Перезагружает список администраторов из файла"""
        if os.path.exists(self.admin_file):
            try:
                with open(self.admin_file, 'r', encoding='utf-8') as f:
                    self.admins = json.load(f)
                logger.debug(f"Перезагружены администраторы: {len(self.admins)}")
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке администраторов: {e}")

    def _reload_global_admins(self):
        """Перезагружает список глобальных администраторов из файла"""
        if os.path.exists(self.global_admin_file):
            try:
                with open(self.global_admin_file, 'r', encoding='utf-8') as f:
                    self.global_admins = json.load(f)
                logger.debug(f"Перезагружены глобальные администраторы: {len(self.global_admins)}")
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке глобальных администраторов: {e}")

    def _reload_streamers(self):
        """Перезагружает список стриммеров из файла"""
        if os.path.exists(self.streamer_file):
            try:
                with open(self.streamer_file, 'r', encoding='utf-8') as f:
                    self.streamers = json.load(f)
                logger.debug(f"Перезагружены стриммеры: {len(self.streamers)}")
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке стриммеров: {e}")

    def _reload_stats(self):
        """Перезагружает статистику пользователей из файла"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.user_stats = json.load(f)
                logger.debug(f"Перезагружена статистика пользователей")
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке статистики: {e}")

    def _reload_settings(self):
        """Перезагружает настройки пользователей из файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.user_settings = json.load(f)
                logger.debug(f"Перезагружены настройки пользователей")
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке настроек: {e}")

    # Переопределяем методы для добавления/удаления с явным сохранением

    def add_user(self, user_id):
        """Добавление пользователя в список разрешенных"""
        user_id_str = str(user_id)
        print(f"Попытка добавления пользователя {user_id_str} в allowed_users")
        print(f"Текущий список allowed_users: {self.allowed_users}")

        if user_id_str not in self.allowed_users:
            # Перезагружаем данные, чтобы избежать проблем с синхронизацией
            self._reload_users()

            # Проверяем еще раз после перезагрузки
            if user_id_str not in self.allowed_users:
                self.allowed_users.append(user_id_str)
                self._save_to_file(self.user_file, self.allowed_users)
                print(f"Пользователь {user_id_str} успешно добавлен в allowed_users")
                print(f"Обновленный список allowed_users: {self.allowed_users}")
                return True

        print(f"Пользователь {user_id_str} уже есть в allowed_users")
        return False

    def remove_user(self, user_id):
        """Удаление пользователя из списка разрешенных"""
        user_id = str(user_id)
        logger.debug(f"SyncedDataStorage: Попытка удаления пользователя {user_id}")

        # Сначала перезагружаем данные
        self._reload_users()
        self._reload_admins()
        self._reload_streamers()

        success = False

        # Удаляем из списка разрешенных пользователей
        if user_id in self.allowed_users:
            self.allowed_users.remove(user_id)
            self._save_to_file(self.user_file, self.allowed_users)
            logger.debug(f"SyncedDataStorage: Пользователь {user_id} удален из allowed_users")
            success = True

        # Если пользователь также админ или стример, удаляем и оттуда
        if user_id in self.admins:
            self.admins.remove(user_id)
            self._save_to_file(self.admin_file, self.admins)
            logger.debug(f"SyncedDataStorage: Пользователь {user_id} удален из admins")
            success = True

        if user_id in self.streamers:
            self.streamers.remove(user_id)
            self._save_to_file(self.streamer_file, self.streamers)
            logger.debug(f"SyncedDataStorage: Пользователь {user_id} удален из streamers")
            success = True

        return success

    def add_admin(self, user_id):
        """Добавление пользователя в список администраторов"""
        user_id_str = str(user_id)
        print(f"Попытка добавления администратора {user_id_str}")

        # Перезагружаем данные, чтобы избежать проблем с синхронизацией
        self._reload_admins()
        self._reload_users()

        if user_id_str not in self.admins:
            # Добавляем также в разрешенных пользователей, если еще не добавлен
            if user_id_str not in self.allowed_users:
                self.add_user(user_id_str)

            self.admins.append(user_id_str)
            self._save_to_file(self.admin_file, self.admins)
            print(f"Администратор {user_id_str} успешно добавлен")
            return True

        print(f"Администратор {user_id_str} уже существует")
        return False

    def remove_admin(self, user_id):
        """Удаление пользователя из списка администраторов"""
        user_id_str = str(user_id)
        logger.debug(f"SyncedDataStorage: Попытка удаления администратора {user_id_str}")

        # Сначала перезагружаем данные
        self._reload_admins()

        if user_id_str in self.admins:
            self.admins.remove(user_id_str)
            self._save_to_file(self.admin_file, self.admins)
            logger.debug(f"SyncedDataStorage: Администратор {user_id_str} успешно удален")
            return True

        logger.debug(f"SyncedDataStorage: Администратор {user_id_str} не найден")
        return False

    def add_streamer(self, user_id):
        """Добавление пользователя в список стриммеров"""
        user_id_str = str(user_id)
        print(f"Попытка добавления стриммера {user_id_str}")

        # Перезагружаем данные, чтобы избежать проблем с синхронизацией
        self._reload_streamers()
        self._reload_users()

        if user_id_str not in self.streamers:
            # Добавляем также в разрешенных пользователей, если еще не добавлен
            if user_id_str not in self.allowed_users:
                self.add_user(user_id_str)

            self.streamers.append(user_id_str)
            self._save_to_file(self.streamer_file, self.streamers)
            print(f"Стриммер {user_id_str} успешно добавлен")
            return True

        print(f"Стриммер {user_id_str} уже существует")
        return False

    def remove_streamer(self, user_id):
        """Удаление пользователя из списка стриммеров"""
        user_id_str = str(user_id)
        logger.debug(f"SyncedDataStorage: Попытка удаления стриммера {user_id_str}")

        # Сначала перезагружаем данные
        self._reload_streamers()

        if user_id_str in self.streamers:
            self.streamers.remove(user_id_str)
            self._save_to_file(self.streamer_file, self.streamers)
            logger.debug(f"SyncedDataStorage: Стриммер {user_id_str} успешно удален")
            return True

        logger.debug(f"SyncedDataStorage: Стриммер {user_id_str} не найден")
        return False