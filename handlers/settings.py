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
from states.forms import SettingsForm

router = Router()
storage = DataStorage()
kb = Keyboards()


@router.message(F.text == "Настройки")
async def settings_menu(message: types.Message):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=kb.remove())
        return

    await message.answer("Выберите настройку для изменения:", reply_markup=kb.settings_menu())


@router.message(F.text == "Метод выплаты")
async def set_payout_method_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        return

    current_settings = storage.get_user_settings(user_id)
    current_method = current_settings.get('payout_method', 'Не указано')

    await message.answer(
        f"Текущий метод выплаты: {current_method}\n\n"
        "Введите новый метод выплаты:",
        reply_markup=kb.back_settings()
    )
    await state.set_state(SettingsForm.payout_method)


@router.message(SettingsForm.payout_method, F.text == "Назад в настройки")
async def back_from_payout_method(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)


@router.message(SettingsForm.payout_method)
async def set_payout_method_process(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        await state.clear()
        return

    payout_method = message.text.strip()

    if len(payout_method) > 100:
        await message.answer("Слишком длинный текст. Пожалуйста, введите более короткое значение.")
        return

    storage.update_settings(user_id, 'payout_method', payout_method)
    await message.answer(f"Метод выплаты обновлен: {payout_method}", reply_markup=kb.settings_menu())
    await state.clear()


@router.message(F.text == "Реквизиты")
async def set_requisites_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        return

    current_settings = storage.get_user_settings(user_id)
    current_requisites = current_settings.get('requisites', 'Не указано')

    await message.answer(
        f"Текущие реквизиты: {current_requisites}\n\n"
        "Введите новые реквизиты:",
        reply_markup=kb.back_settings()
    )
    await state.set_state(SettingsForm.requisites)


@router.message(SettingsForm.requisites, F.text == "Назад в настройки")
async def back_from_requisites(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)


@router.message(SettingsForm.requisites)
async def set_requisites_process(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        await state.clear()
        return

    requisites = message.text.strip()

    if len(requisites) > 200:
        await message.answer("Слишком длинный текст. Пожалуйста, введите более короткое значение.")
        return

    storage.update_settings(user_id, 'requisites', requisites)
    await message.answer(f"Реквизиты обновлены: {requisites}", reply_markup=kb.settings_menu())
    await state.clear()


@router.message(F.text == "Страна")
async def set_country_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        return

    current_settings = storage.get_user_settings(user_id)
    current_country = current_settings.get('country', 'Не указано')

    await message.answer(
        f"Текущая страна: {current_country}\n\n"
        "Введите новую страну:",
        reply_markup=kb.back_settings()
    )
    await state.set_state(SettingsForm.country)


@router.message(SettingsForm.country, F.text == "Назад в настройки")
async def back_from_country(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)


@router.message(SettingsForm.country)
async def set_country_process(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        await state.clear()
        return

    country = message.text.strip()

    if len(country) > 50:
        await message.answer("Слишком длинный текст. Пожалуйста, введите более короткое значение.")
        return

    storage.update_settings(user_id, 'country', country)
    await message.answer(f"Страна обновлена: {country}", reply_markup=kb.settings_menu())
    await state.clear()


@router.message(F.text == "Банк")
async def set_bank_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        return

    current_settings = storage.get_user_settings(user_id)
    current_bank = current_settings.get('bank', 'Не указано')

    await message.answer(
        f"Текущий банк: {current_bank}\n\n"
        "Введите новый банк:",
        reply_markup=kb.back_settings()
    )
    await state.set_state(SettingsForm.bank)


@router.message(SettingsForm.bank, F.text == "Назад в настройки")
async def back_from_bank(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)


@router.message(SettingsForm.bank)
async def set_bank_process(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not storage.is_allowed(user_id):
        await message.answer("У вас нет доступа к этому боту.", reply_markup=kb.remove())
        await state.clear()
        return

    bank = message.text.strip()

    if len(bank) > 50:
        await message.answer("Слишком длинный текст. Пожалуйста, введите более короткое значение.")
        return

    storage.update_settings(user_id, 'bank', bank)
    await message.answer(f"Банк обновлен: {bank}", reply_markup=kb.settings_menu())
    await state.clear()