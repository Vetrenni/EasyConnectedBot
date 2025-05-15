import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = '7673946117:AAEzu5CSMfABRgvi9036Pz6cHJ08hP317z0'
ANDREY_USER_ID = 5838284980  # <-- сюда вставьте user_id Андрея

STATS_FILE = "user_stats.json"
SETTINGS_FILE = "user_settings.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отправить отчет')],
        [KeyboardButton(text='Создать запрос на выплату')],
        [KeyboardButton(text='Статистика')],
        [KeyboardButton(text='Настройки')],
    ],
    resize_keyboard=True
)

settings_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Метод выплаты')],
        [KeyboardButton(text='Реквизиты')],
        [KeyboardButton(text='Страна')],
        [KeyboardButton(text='Банк')],
        [KeyboardButton(text='Назад в меню')],
    ],
    resize_keyboard=True
)

back_main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Назад в меню')]],
    resize_keyboard=True
)

back_settings_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Назад в настройки')]],
    resize_keyboard=True
)

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_stats = load_json(STATS_FILE)
user_settings = load_json(SETTINGS_FILE)

class ReportForm(StatesGroup):
    streamer_id = State()
    hours = State()
    amount = State()
    confirm = State()

class SettingsForm(StatesGroup):
    payout_method = State()
    requisites = State()
    country = State()
    bank = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=main_menu_kb
    )

@dp.message(F.text == "Отправить отчет")
async def start_report(message: types.Message, state: FSMContext):
    await message.answer("Введите номер стриммера:", reply_markup=back_main_kb)
    await state.set_state(ReportForm.streamer_id)

@dp.message(ReportForm.streamer_id, F.text == "Назад в меню")
@dp.message(ReportForm.hours, F.text == "Назад в меню")
@dp.message(ReportForm.amount, F.text == "Назад в меню")
@dp.message(ReportForm.confirm, F.text == "Назад в меню")
async def back_from_report(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb)

@dp.message(ReportForm.streamer_id)
async def process_streamer_id(message: types.Message, state: FSMContext):
    await state.update_data(streamer_id=message.text)
    await message.answer("Введите количество часов:", reply_markup=back_main_kb)
    await state.set_state(ReportForm.hours)

@dp.message(ReportForm.hours)
async def process_hours(message: types.Message, state: FSMContext):
    await state.update_data(hours=message.text)
    await message.answer("Введите сумму:", reply_markup=back_main_kb)
    await state.set_state(ReportForm.amount)

@dp.message(ReportForm.amount)
async def process_amount(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    data = await state.get_data()
    text = (
        f"Проверьте введённые данные:\n"
        f"Номер стриммера: {data['streamer_id']}\n"
        f"Количество часов: {data['hours']}\n"
        f"Сумма: {data['amount']}\n\n"
        "Если всё верно, напишите 'Да'. Для отмены — 'Нет'."
    )
    await message.answer(text, reply_markup=back_main_kb)
    await state.set_state(ReportForm.confirm)

@dp.message(ReportForm.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        user_id = str(message.from_user.id)
        try:
            hours = float(data['hours'])
            amount = float(data['amount'])
        except ValueError:
            await message.answer("Ошибка: количество часов и сумма должны быть числами.", reply_markup=main_menu_kb)
            await state.clear()
            return

        if user_id not in user_stats:
            user_stats[user_id] = {"hours": 0.0, "amount": 0.0}
        user_stats[user_id]["hours"] += hours
        user_stats[user_id]["amount"] += amount
        save_json(STATS_FILE, user_stats)

        report_text = (
            f"Новый отчет!\n"
            f"Номер стриммера: {data['streamer_id']}\n"
            f"Количество часов: {data['hours']}\n"
            f"Сумма: {data['amount']}\n"
            f"Отправитель: @{message.from_user.username or message.from_user.id}"
        )
        try:
            await bot.send_message(ANDREY_USER_ID, report_text)
            await message.answer("Ваш отчет отправлен!", reply_markup=main_menu_kb)
        except Exception as e:
            await message.answer("Ошибка при отправке отчета администратору.", reply_markup=main_menu_kb)
    else:
        await message.answer("Отправка отчета отменена.", reply_markup=main_menu_kb)
    await state.clear()

@dp.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    user_id = str(message.from_user.id)
    stats = user_stats.get(user_id)
    if stats:
        await message.answer(
            f"Ваша статистика:\n"
            f"Общее количество часов: {stats['hours']}\n"
            f"Общая сумма: {stats['amount']}",
            reply_markup=main_menu_kb
        )
    else:
        await message.answer("У вас пока нет отправленных отчетов.", reply_markup=main_menu_kb)

@dp.message(F.text == "Настройки")
async def settings_menu(message: types.Message):
    user_id = str(message.from_user.id)
    settings = user_settings.get(user_id, {})
    payout_method = settings.get("payout_method", "не указано")
    requisites = settings.get("requisites", "не указано")
    country = settings.get("country", "не указано")
    bank = settings.get("bank", "не указано")
    text = (
        f"Ваши текущие настройки:\n"
        f"Метод выплаты: {payout_method}\n"
        f"Реквизиты: {requisites}\n"
        f"Страна: {country}\n"
        f"Банк: {bank}\n\n"
        "Выберите, что хотите изменить:"
    )
    await message.answer(text, reply_markup=settings_menu_kb)

@dp.message(F.text == "Назад в меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb)

@dp.message(F.text == "Метод выплаты")
async def set_payout_method(message: types.Message, state: FSMContext):
    await message.answer("Введите метод выплаты (например, PayPal, карта и т.д.):", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.payout_method)

@dp.message(SettingsForm.payout_method, F.text == "Назад в настройки")
async def back_from_settings_payout(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)

@dp.message(SettingsForm.payout_method)
async def save_payout_method(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["payout_method"] = message.text
    save_json("user_settings.json", user_settings)
    await message.answer("Метод выплаты сохранён.", reply_markup=settings_menu_kb)
    await state.clear()

@dp.message(F.text == "Реквизиты")
async def set_requisites(message: types.Message, state: FSMContext):
    await message.answer("Введите ваши реквизиты:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.requisites)

@dp.message(SettingsForm.requisites, F.text == "Назад в настройки")
async def back_from_settings_requisites(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)

@dp.message(SettingsForm.requisites)
async def save_requisites(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["requisites"] = message.text
    save_json("user_settings.json", user_settings)
    await message.answer("Реквизиты сохранены.", reply_markup=settings_menu_kb)
    await state.clear()

@dp.message(F.text == "Страна")
async def set_country(message: types.Message, state: FSMContext):
    await message.answer("Введите вашу страну:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.country)

@dp.message(SettingsForm.country, F.text == "Назад в настройки")
async def back_from_settings_country(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)

@dp.message(SettingsForm.country)
async def save_country(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["country"] = message.text
    save_json("user_settings.json", user_settings)
    await message.answer("Страна сохранена.", reply_markup=settings_menu_kb)
    await state.clear()

@dp.message(F.text == "Банк")
async def set_bank(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш банк:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.bank)

@dp.message(SettingsForm.bank, F.text == "Назад в настройки")
async def back_from_settings_bank(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)

@dp.message(SettingsForm.bank)
async def save_bank(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["bank"] = message.text
    save_json("user_settings.json", user_settings)
    await message.answer("Банк сохранён.", reply_markup=settings_menu_kb)
    await state.clear()

@dp.message(F.text == "Назад в настройки")
async def back_to_settings(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())