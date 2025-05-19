import sys
import os

# Получаем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext

from core.keyboard import Keyboards
from core.storage import DataStorage
from states.forms import ChatForm

router = Router()
storage = DataStorage()
kb = Keyboards()


@router.message(F.text == "Внести оплату")
async def start_payment_chat(message: types.Message, state: FSMContext):
    """Начало процесса создания чата для внесения оплаты"""
    user_id = message.from_user.id

    print(f"Пользователь {user_id} нажал на 'Внести оплату'")
    print(f"Является ли стриммером: {storage.is_streamer(user_id)}")

    if not storage.is_streamer(user_id):
        await message.answer("У вас нет прав для этого действия.")
        return

    await message.answer(
        "Опишите детали оплаты, которую вы хотите внести. Это сообщение будет отправлено администраторам.",
        reply_markup=kb.back_main()
    )

    await state.set_state(ChatForm.waiting_for_initial_message)
    print(f"Установлено состояние ChatForm.waiting_for_initial_message для пользователя {user_id}")


@router.message(ChatForm.waiting_for_initial_message)
async def process_initial_message(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка сообщения и создание чата"""
    user_id = message.from_user.id

    print(f"Получено сообщение от пользователя {user_id} в состоянии ChatForm.waiting_for_initial_message")

    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Действие отменено.",
            reply_markup=kb.main_menu(
                is_admin=storage.is_admin(user_id),
                is_global_admin=storage.is_global_admin(user_id),
                is_streamer=storage.is_streamer(user_id)
            )
        )
        return

    print(f"Стриммер {user_id} пытается создать чат с сообщением: {message.text}")

    # Создаем новый чат
    try:
        chat_id = storage.create_chat(user_id, message.text)
        print(f"Чат успешно создан с ID: {chat_id}")
    except Exception as e:
        print(f"ОШИБКА при создании чата: {e}")
        await message.answer(
            "Произошла ошибка при создании чата. Пожалуйста, попробуйте позже.",
            reply_markup=kb.main_menu(
                is_admin=storage.is_admin(user_id),
                is_global_admin=storage.is_global_admin(user_id),
                is_streamer=storage.is_streamer(user_id)
            )
        )
        await state.clear()
        return

    await message.answer(
        "Ваше сообщение отправлено администраторам. Ожидайте ответа.",
        reply_markup=kb.main_menu(
            is_admin=storage.is_admin(user_id),
            is_global_admin=storage.is_global_admin(user_id),
            is_streamer=storage.is_streamer(user_id)
        )
    )

    # Уведомляем администраторов о новом чате
    admin_message = (
        f"Новое сообщение от стриммера (ID: {user_id}):\n\n"
        f"{message.text}\n\n"
        f"Используйте команду /chats для просмотра всех активных чатов."
    )

    # Отправляем сообщение всем админам
    admin_ids = set(storage.admins) | set(storage.global_admins)
    print(f"Отправка уведомлений админам: {admin_ids}")

    for admin_id in admin_ids:
        try:
            await bot.send_message(int(admin_id), admin_message)
            print(f"Уведомление отправлено админу {admin_id}")
        except Exception as e:
            print(f"Ошибка отправки сообщения админу {admin_id}: {e}")

    await state.clear()