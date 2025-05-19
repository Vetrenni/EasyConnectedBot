import json
import os

def load_json(file_path):
    """Загрузить данные из JSON файла"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return {}
    return {}

def save_json(file_path, data):
    """Сохранить данные в JSON файл"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_settings(user_id):
    """Получить настройки пользователя"""
    settings_file = "../settings.json"
    settings = load_json(settings_file)
    return settings.get(str(user_id), {})