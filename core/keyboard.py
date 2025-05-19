from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton


class Keyboards:
    @staticmethod
    def main_menu(is_admin=False, is_global_admin=False, is_streamer=False) -> ReplyKeyboardMarkup:
        keyboard = []

        if is_streamer:
            keyboard.append([KeyboardButton(text='Внести оплату')])
        else:
            keyboard.append([KeyboardButton(text='Отправить отчет')])
            keyboard.append([KeyboardButton(text='Статистика')])
            keyboard.append([KeyboardButton(text='Настройки')])

        if is_admin or is_global_admin:
            keyboard.append([KeyboardButton(text='Админ-панель')])
            keyboard.append([KeyboardButton(text='Чаты')])

        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def admin_panel(is_global_admin=False) -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton(text='Добавить пользователя')],
        ]

        if is_global_admin:
            keyboard.append([KeyboardButton(text='Выдать админа')])

        keyboard.append([KeyboardButton(text='Сделать стриммером')])
        keyboard.append([KeyboardButton(text='Назад в меню')])
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def chat_list(chats: dict) -> InlineKeyboardMarkup:
        """Клавиатура со списком открытых чатов"""
        keyboard = []
        for chat_id, chat in chats.items():
            # Получаем ID пользователя из чата для отображения
            user_id = chat.get('user_id', 'Неизвестный')
            # Добавляем первые 30 символов первого сообщения для контекста
            first_message = ""
            if chat.get("messages") and len(chat["messages"]) > 0:
                first_message = chat["messages"][0].get("text", "")
                if len(first_message) > 30:
                    first_message = first_message[:30] + "..."

            btn_text = f"Чат {user_id}"
            if first_message:
                btn_text += f": {first_message}"

            keyboard.append([
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data=f"chat:{chat_id}"
                )
            ])

        print(f"Создана клавиатура с {len(keyboard)} чатами")
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def chat_actions(chat_id: str) -> InlineKeyboardMarkup:
        """Клавиатура с действиями для чата"""
        keyboard = [
            [InlineKeyboardButton(text="Закрыть чат", callback_data=f"close_chat:{chat_id}")],
            [InlineKeyboardButton(text="Назад к списку чатов", callback_data="back_to_chats")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def settings_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton(text='Метод выплаты')],
            [KeyboardButton(text='Реквизиты')],
            [KeyboardButton(text='Страна')],
            [KeyboardButton(text='Банк')],
            [KeyboardButton(text='Назад в меню')],
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def back_main() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Назад в меню')]],
            resize_keyboard=True
        )

    @staticmethod
    def back_settings() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Назад в настройки')]],
            resize_keyboard=True
        )

    @staticmethod
    def remove() -> ReplyKeyboardRemove:
        return ReplyKeyboardRemove()