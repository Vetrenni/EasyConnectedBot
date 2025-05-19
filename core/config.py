import json
import os


class Config:
    def __init__(self, config_file='config/config.json'):
        self.config_file = config_file

        # Создаем директорию config если её нет
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        # Проверяем существование файла конфигурации
        if not os.path.exists(config_file):
            # Создаем файл с дефолтными значениями
            default_config = {
                'BOT_TOKEN': 'YOUR_BOT_TOKEN_HERE',
                'initial_global_admins': [],
                'files': {
                    'stats': 'user_stats.json',
                    'settings': 'user_settings.json',
                    'allowed_users': 'allowed_users.json',
                    'admins': 'admins.json',
                    'global_admins': 'global_admins.json'
                }
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)

            self.BOT_TOKEN = default_config['BOT_TOKEN']
            self.INITIAL_GLOBAL_ADMINS = default_config['initial_global_admins']
            self.FILES = default_config['files']
        else:
            # Загружаем конфигурацию из файла
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Используем ключ 'BOT_TOKEN'
            self.BOT_TOKEN = config.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
            self.INITIAL_GLOBAL_ADMINS = config.get('initial_global_admins', [])
            self.FILES = config.get('files', {
                'stats': 'user_stats.json',
                'settings': 'user_settings.json',
                'allowed_users': 'allowed_users.json',
                'admins': 'admins.json',
                'global_admins': 'global_admins.json'
            })