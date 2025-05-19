import sys
import os

# Получаем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.keyboard import Keyboards
from core.storage import DataStorage

router = Router()
storage = DataStorage()
kb = Keyboards()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=kb.remove())
        return

    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=kb.main_menu(
            storage.is_admin(user_id),
            storage.is_global_admin(user_id),
            storage.is_streamer(user_id)
        )
    )


@router.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=kb.remove())
        return

    if storage.is_streamer(user_id):
        await message.answer("Эта функция недоступна для стриммеров.",
                             reply_markup=kb.main_menu(False, False, True))
        return

    stats = storage.get_user_stats(user_id)
    if stats and (stats['hours'] > 0 or stats['amount'] > 0):
        await message.answer(
            f"Ваша статистика:\n"
            f"Общее количество часов: {stats['hours']}\n"
            f"Общая сумма: {stats['amount']}",
            reply_markup=kb.main_menu(
                storage.is_admin(user_id),
                storage.is_global_admin(user_id),
                storage.is_streamer(user_id)
            )
        )
    else:
        await message.answer(
            "У вас пока нет отправленных отчетов.",
            reply_markup=kb.main_menu(
                storage.is_admin(user_id),
                storage.is_global_admin(user_id),
                storage.is_streamer(user_id)
            )
        )


@router.message(F.text == "Назад в меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=kb.main_menu(
            storage.is_admin(user_id),
            storage.is_global_admin(user_id),
            storage.is_streamer(user_id)
        )
    )