import sys
import os

# Получаем путь к корневой директории проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from core.keyboard import Keyboards
from core.storage import DataStorage
from states.forms import ReportForm

router = Router()
storage = DataStorage()
kb = Keyboards()


@router.message(F.text == "Отправить отчет")
async def start_report(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=kb.remove())
        return

    if storage.is_streamer(user_id):
        await message.answer(
            "Эта функция недоступна для стриммеров.",
            reply_markup=kb.main_menu(False, False, True)
        )
        return

    await message.answer("Введите ID стриммера:", reply_markup=kb.back_main())
    await state.set_state(ReportForm.streamer_id)


@router.message(ReportForm.streamer_id)
async def process_streamer_id(message: types.Message, state: FSMContext):
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Отправка отчета отменена.",
            reply_markup=kb.main_menu(
                storage.is_admin(message.from_user.id),
                storage.is_global_admin(message.from_user.id),
                storage.is_streamer(message.from_user.id)
            )
        )
        return

    streamer_id = message.text.strip()
    if not streamer_id.isdigit() or not storage.is_streamer(streamer_id):
        await message.answer("Неверный ID стриммера. Пожалуйста, введите корректный ID.")
        return

    await state.update_data(streamer_id=streamer_id)
    await message.answer("Введите количество часов:", reply_markup=kb.back_main())
    await state.set_state(ReportForm.hours)


@router.message(ReportForm.hours)
async def process_hours(message: types.Message, state: FSMContext):
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Отправка отчета отменена.",
            reply_markup=kb.main_menu(
                storage.is_admin(message.from_user.id),
                storage.is_global_admin(message.from_user.id),
                storage.is_streamer(message.from_user.id)
            )
        )
        return

    try:
        hours = float(message.text.replace(',', '.'))
        if hours <= 0:
            raise ValueError("Часы должны быть положительным числом")

        await state.update_data(hours=hours)
        await message.answer("Введите сумму:", reply_markup=kb.back_main())
        await state.set_state(ReportForm.amount)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число часов.")


@router.message(ReportForm.amount)
async def process_amount(message: types.Message, state: FSMContext):
    if message.text == "Назад в меню":
        await state.clear()
        await message.answer(
            "Отправка отчета отменена.",
            reply_markup=kb.main_menu(
                storage.is_admin(message.from_user.id),
                storage.is_global_admin(message.from_user.id),
                storage.is_streamer(message.from_user.id)
            )
        )
        return

    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        # Получаем все данные из состояния
        data = await state.get_data()
        streamer_id = data['streamer_id']
        hours = data['hours']

        # Обновляем статистику пользователя
        storage.update_stats(message.from_user.id, hours, amount)

        # Формируем сообщение об успешной отправке отчета
        success_message = (
            f"Отчет успешно отправлен!\n"
            f"ID стриммера: {streamer_id}\n"
            f"Количество часов: {hours}\n"
            f"Сумма: {amount}"
        )

        await message.answer(
            success_message,
            reply_markup=kb.main_menu(
                storage.is_admin(message.from_user.id),
                storage.is_global_admin(message.from_user.id),
                storage.is_streamer(message.from_user.id)
            )
        )

        # Очищаем состояние
        await state.clear()

    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")