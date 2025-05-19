import sys
import os

# Получаем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from core.keyboard import Keyboards
from core.storage import DataStorage
from states.forms import SettingsForm, ChatForm

router = Router()
storage = DataStorage()
kb = Keyboards()


# ====== ОБРАБОТЧИКИ ДЛЯ ЧАТОВ ======

@router.message(F.text == "Чаты")
async def show_chats(message: types.Message, state: FSMContext):
    """Показать список всех активных чатов"""
    user_id = message.from_user.id

    print(f"Пользователь {user_id} запросил список чатов")
    print(f"Права администратора: {storage.is_admin(user_id)}")
    print(f"Права глобального администратора: {storage.is_global_admin(user_id)}")

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        return

    # Получаем все открытые чаты
    open_chats = storage.get_open_chats()

    if not open_chats:
        await message.answer(
            "В данный момент нет активных чатов.",
            reply_markup=kb.main_menu(
                is_admin=storage.is_admin(user_id),
                is_global_admin=storage.is_global_admin(user_id),
                is_streamer=storage.is_streamer(user_id)
            )
        )
        return

    await message.answer(
        "Выберите чат для просмотра:",
        reply_markup=kb.chat_list(open_chats)
    )

    await state.set_state(ChatForm.selecting_chat)
    print(f"Установлено состояние ChatForm.selecting_chat для пользователя {user_id}")


@router.callback_query(F.data.startswith("chat:"))
async def show_chat(callback: types.CallbackQuery, state: FSMContext):
    """Показать содержимое выбранного чата"""
    user_id = callback.from_user.id

    print(f"Пользователь {user_id} выбрал чат из списка")

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await callback.answer("У вас нет прав для этого действия.")
        return

    # Извлекаем ID чата из callback_data
    chat_id = callback.data.split(":")[1]
    print(f"Выбран чат с ID: {chat_id}")

    # Получаем данные чата
    chat = storage.get_chat(chat_id)

    if not chat:
        await callback.answer("Чат не найден.")
        await callback.message.edit_text(
            "Чат не найден. Пожалуйста, вернитесь в главное меню."
        )
        return

    # Формируем текст с сообщениями чата
    chat_text = f"Чат {chat_id} с пользователем {chat['user_id']}\n\n"

    for msg in chat["messages"]:
        sender = "Администратор" if (
                    storage.is_admin(msg["user_id"]) or storage.is_global_admin(msg["user_id"])) else "Стриммер"
        chat_text += f"{sender} ({msg['user_id']}):\n{msg['text']}\n\n"

    # Добавляем информацию о статусе чата
    if chat["status"] == "closed":
        chat_text += f"Чат закрыт: {chat['closed_at']}"

    # Отправляем содержимое чата и клавиатуру с действиями
    await callback.message.edit_text(
        chat_text,
        reply_markup=kb.chat_actions(chat_id) if chat["status"] == "open" else None
    )

    # Сохраняем ID чата в данных состояния
    await state.update_data(current_chat_id=chat_id)
    await state.set_state(ChatForm.waiting_for_message)
    print(f"Установлено состояние ChatForm.waiting_for_message для пользователя {user_id}")

    await callback.answer()


@router.callback_query(F.data.startswith("close_chat:"))
async def close_chat(callback: types.CallbackQuery, state: FSMContext):
    """Закрыть выбранный чат"""
    user_id = callback.from_user.id

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await callback.answer("У вас нет прав для этого действия.")
        return

    # Извлекаем ID чата из callback_data
    chat_id = callback.data.split(":")[1]
    print(f"Попытка закрыть чат с ID: {chat_id}")

    # Закрываем чат
    success = storage.close_chat(chat_id)

    if not success:
        await callback.answer("Не удалось закрыть чат.")
        return

    # Получаем обновленные данные чата
    chat = storage.get_chat(chat_id)

    # Формируем обновленный текст сообщения
    chat_text = f"Чат {chat_id} с пользователем {chat['user_id']}\n\n"

    for msg in chat["messages"]:
        sender = "Администратор" if (
                    storage.is_admin(msg["user_id"]) or storage.is_global_admin(msg["user_id"])) else "Стриммер"
        chat_text += f"{sender} ({msg['user_id']}):\n{msg['text']}\n\n"

    chat_text += f"Чат закрыт: {chat['closed_at']}"

    # Обновляем сообщение
    await callback.message.edit_text(chat_text)

    # Уведомляем пользователя о закрытии чата
    try:
        streamer_id = int(chat['user_id'])
        await callback.bot.send_message(
            streamer_id,
            f"Ваш чат был закрыт администратором."
        )
        print(f"Отправлено уведомление стриммеру {streamer_id} о закрытии чата")
    except Exception as e:
        print(f"Ошибка при отправке уведомления стриммеру: {e}")

    await callback.answer("Чат успешно закрыт.")
    await state.clear()


@router.callback_query(F.data == "back_to_chats")
async def back_to_chats_list(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку чатов"""
    user_id = callback.from_user.id

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await callback.answer("У вас нет прав для этого действия.")
        return

    # Получаем все открытые чаты
    open_chats = storage.get_open_chats()

    if not open_chats:
        await callback.message.edit_text(
            "В данный момент нет активных чатов."
        )
        await state.clear()
        return

    await callback.message.edit_text(
        "Выберите чат для просмотра:",
        reply_markup=kb.chat_list(open_chats)
    )

    await state.set_state(ChatForm.selecting_chat)
    await callback.answer()


@router.message(ChatForm.waiting_for_message)
async def process_admin_reply(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка ответа администратора в чате"""
    user_id = message.from_user.id

    print(f"Получен ответ администратора {user_id} в чате")

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        await state.clear()
        return

    # Получаем ID текущего чата из данных состояния
    data = await state.get_data()
    chat_id = data.get('current_chat_id')

    if not chat_id:
        await message.answer("Чат не найден. Пожалуйста, выберите чат снова.")
        await state.clear()
        return

    print(f"Администратор отвечает в чат {chat_id}")

    # Получаем данные чата
    chat = storage.get_chat(chat_id)

    if not chat or chat["status"] == "closed":
        await message.answer("Чат закрыт или не существует.")
        await state.clear()
        return

    # Добавляем сообщение в чат
    success = storage.add_message_to_chat(chat_id, user_id, message.text)

    if not success:
        await message.answer("Не удалось отправить сообщение.")
        return

    # Отправляем сообщение стриммеру
    try:
        streamer_id = int(chat['user_id'])
        await bot.send_message(
            streamer_id,
            f"Новое сообщение от администратора:\n\n{message.text}"
        )
        print(f"Сообщение успешно отправлено стриммеру {streamer_id}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения стриммеру: {e}")
        await message.answer("Не удалось отправить сообщение стриммеру.")

    # Формируем обновленный текст с сообщениями чата
    chat_text = f"Чат {chat_id} с пользователем {chat['user_id']}\n\n"

    # Получаем обновленные данные чата
    updated_chat = storage.get_chat(chat_id)

    for msg in updated_chat["messages"]:
        sender = "Администратор" if (
                    storage.is_admin(msg["user_id"]) or storage.is_global_admin(msg["user_id"])) else "Стриммер"
        chat_text += f"{sender} ({msg['user_id']}):\n{msg['text']}\n\n"

    # Отправляем обновленное содержимое чата
    await message.answer(
        chat_text,
        reply_markup=kb.chat_actions(chat_id)
    )


@router.message(Command("chats"))
async def cmd_chats(message: types.Message, state: FSMContext):
    """Обработка команды /chats"""
    print(f"Получена команда /chats от пользователя {message.from_user.id}")
    await show_chats(message, state)


# ====== ОБРАБОТЧИКИ ДЛЯ АДМИН-ПАНЕЛИ ======

@router.message(F.text == "Админ-панель")
async def admin_panel(message: types.Message):
    """Показать админ-панель"""
    user_id = message.from_user.id

    print(f"Пользователь {user_id} запросил админ-панель")

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        return

    await message.answer(
        "Выберите действие:",
        reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
    )


@router.message(F.text == "Добавить пользователя")
async def add_user_start(message: types.Message, state: FSMContext):
    """Добавление пользователя"""
    user_id = message.from_user.id

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        return

    await message.answer(
        "Введите ID пользователя для добавления:",
        reply_markup=kb.back_main()
    )
    await state.set_state(SettingsForm.add_user)


@router.message(SettingsForm.add_user)
async def add_user_process(message: types.Message, state: FSMContext):
    """Обработка добавления пользователя"""
    user_id = message.from_user.id

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        await state.clear()
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=kb.main_menu(
                storage.is_admin(user_id),
                storage.is_global_admin(user_id),
                storage.is_streamer(user_id)
            )
        )
        return

    try:
        new_user_id = message.text.strip()

        if not new_user_id.isdigit():
            await message.answer("ID пользователя должен быть числом. Попробуйте еще раз.")
            return

        storage.add_user(new_user_id)

        await message.answer(
            f"Пользователь с ID {new_user_id} успешно добавлен.",
            reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
        )

        # Уведомляем пользователя о том, что он получил доступ
        try:
            await message.bot.send_message(
                int(new_user_id),
                "Вам был предоставлен доступ к боту. Используйте /start для начала работы."
            )
            print(f"Уведомление отправлено пользователю {new_user_id}")
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {new_user_id}: {e}")

        await state.clear()
    except Exception as e:
        print(f"Ошибка при добавлении пользователя: {e}")
        await message.answer(
            "Произошла ошибка при добавлении пользователя.",
            reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
        )
        await state.clear()


@router.message(F.text == "Выдать админа")
async def give_admin_start(message: types.Message, state: FSMContext):
    """Выдача прав администратора"""
    user_id = message.from_user.id

    if not storage.is_global_admin(user_id):
        await message.answer("У вас нет прав для этого действия.")
        return

    await message.answer(
        "Введите ID пользователя для выдачи прав администратора:",
        reply_markup=kb.back_main()
    )
    await state.set_state(SettingsForm.give_admin)


@router.message(SettingsForm.give_admin)
async def give_admin_process(message: types.Message, state: FSMContext):
    """Обработка выдачи прав администратора"""
    user_id = message.from_user.id

    if not storage.is_global_admin(user_id):
        await message.answer("У вас нет прав для этого действия.")
        await state.clear()
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=kb.main_menu(
                storage.is_admin(user_id),
                storage.is_global_admin(user_id),
                storage.is_streamer(user_id)
            )
        )
        return

    try:
        new_admin_id = message.text.strip()

        if not new_admin_id.isdigit():
            await message.answer("ID пользователя должен быть числом. Попробуйте еще раз.")
            return

        # Добавляем пользователя в список разрешенных, если его там нет
        if not storage.is_allowed(new_admin_id):
            storage.add_user(new_admin_id)

        storage.add_admin(new_admin_id)

        await message.answer(
            f"Пользователь с ID {new_admin_id} успешно получил права администратора.",
            reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
        )

        # Уведомляем пользователя о том, что он получил права администратора
        try:
            await message.bot.send_message(
                int(new_admin_id),
                "Вам были выданы права администратора в боте."
            )
            print(f"Уведомление о правах админа отправлено пользователю {new_admin_id}")
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {new_admin_id}: {e}")

        await state.clear()
    except Exception as e:
        print(f"Ошибка при выдаче прав администратора: {e}")
        await message.answer(
            "Произошла ошибка при выдаче прав администратора.",
            reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
        )
        await state.clear()


@router.message(F.text == "Сделать стриммером")
async def make_streamer_start(message: types.Message, state: FSMContext):
    """Назначение пользователя стриммером"""
    user_id = message.from_user.id

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        return

    await message.answer(
        "Введите ID пользователя для назначения стриммером:",
        reply_markup=kb.back_main()
    )
    await state.set_state(SettingsForm.make_streamer)


@router.message(SettingsForm.make_streamer)
async def make_streamer_process(message: types.Message, state: FSMContext):
    """Обработка назначения пользователя стриммером"""
    user_id = message.from_user.id

    if not (storage.is_admin(user_id) or storage.is_global_admin(user_id)):
        await message.answer("У вас нет прав для этого действия.")
        await state.clear()
        return

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=kb.main_menu(
                storage.is_admin(user_id),
                storage.is_global_admin(user_id),
                storage.is_streamer(user_id)
            )
        )
        return

    try:
        streamer_id = message.text.strip()

        if not streamer_id.isdigit():
            await message.answer("ID пользователя должен быть числом. Попробуйте еще раз.")
            return

        storage.add_streamer(streamer_id)

        await message.answer(
            f"Пользователь с ID {streamer_id} успешно назначен стриммером.",
            reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
        )

        # Уведомляем пользователя о том, что он стал стриммером
        try:
            await message.bot.send_message(
                int(streamer_id),
                "Вам были выданы права стриммера в боте. Используйте /start для обновления меню."
            )
            print(f"Уведомление о правах стриммера отправлено пользователю {streamer_id}")
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {streamer_id}: {e}")

        await state.clear()
    except Exception as e:
        print(f"Ошибка при назначении стриммером: {e}")
        await message.answer(
            "Произошла ошибка при назначении пользователя стриммером.",
            reply_markup=kb.admin_panel(storage.is_global_admin(user_id))
        )
        await state.clear()