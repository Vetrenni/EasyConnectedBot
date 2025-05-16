import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = '7673946117:AAEzu5CSMfABRgvi9036Pz6cHJ08hP317z0'

# Пути к файлам
STATS_FILE = "user_stats.json"
SETTINGS_FILE = "user_settings.json"
ALLOWED_USERS_FILE = "allowed_users.json"
ADMINS_FILE = "admins.json"
GLOBAL_ADMINS_FILE = "global_admins.json"

# Изначальные глобальные админы
INITIAL_GLOBAL_ADMINS = ['5838284980']  # <-- впиши свои ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE] else {}
                return json.loads(content)
        except:
            return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE] else {}
    return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE] else {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загружаем данные
user_stats = load_json(STATS_FILE)
user_settings = load_json(SETTINGS_FILE)
allowed_users = set(load_json(ALLOWED_USERS_FILE) or [])
admins = set(str(x) for x in load_json(ADMINS_FILE) or [])
global_admins = set(str(x) for x in load_json(GLOBAL_ADMINS_FILE) or [])

# Изначальные глобальные админы
for gid in INITIAL_GLOBAL_ADMINS:
    global_admins.add(str(gid))
save_json(GLOBAL_ADMINS_FILE, list(global_admins))

# --- Клавиатуры ---
def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Отправить отчет')],
            [KeyboardButton(text='Статистика')],
            [KeyboardButton(text='Настройки')],
        ],
        resize_keyboard=True
    )

def get_settings_menu_kb(is_admin=False, is_global_admin=False):
    kb = [
        [KeyboardButton(text='Метод выплаты')],
        [KeyboardButton(text='Реквизиты')],
        [KeyboardButton(text='Страна')],
        [KeyboardButton(text='Банк')],
    ]
    if is_admin or is_global_admin:
        kb.append([KeyboardButton(text='Админ-панель')])
    kb.append([KeyboardButton(text='Назад в меню')])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_admin_panel_kb(is_global_admin=False):
    kb = [
        [KeyboardButton(text='Добавить пользователя')],
        [KeyboardButton(text='Убрать пользователя')],
    ]
    if is_global_admin:
        kb.append([KeyboardButton(text='Выдать админа')])
        kb.append([KeyboardButton(text='Удалить админа')])
        kb.append([KeyboardButton(text='Статистика пользователей')])
    kb.append([KeyboardButton(text='Назад в настройки')])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- FSM ---
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
    add_user = State()
    remove_user = State()
    give_admin = State()
    remove_admin = State()

# --- Проверки ---
def is_allowed(user_id):
    return str(user_id) in allowed_users or is_admin(user_id) or is_global_admin(user_id)

def is_admin(user_id):
    return str(user_id) in admins

def is_global_admin(user_id):
    return str(user_id) in global_admins

# --- Обработчики ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer("Привет! Выберите действие:", reply_markup=main_menu_kb())

@dp.message(F.text == "Отправить отчет")
async def start_report(message: types.Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer("Введите номер стриммера:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReportForm.streamer_id)

@dp.message(ReportForm.streamer_id, F.text == "Назад в меню")
@dp.message(ReportForm.hours, F.text == "Назад в меню")
@dp.message(ReportForm.amount, F.text == "Назад в меню")
@dp.message(ReportForm.confirm, F.text == "Назад в меню")
async def back_from_report(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb())

@dp.message(ReportForm.streamer_id)
async def process_streamer_id(message: types.Message, state: FSMContext):
    await state.update_data(streamer_id=message.text)
    await message.answer("Введите количество часов:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReportForm.hours)

@dp.message(ReportForm.hours)
async def process_hours(message: types.Message, state: FSMContext):
    await state.update_data(hours=message.text)
    await message.answer("Введите сумму:", reply_markup=ReplyKeyboardRemove())
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
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReportForm.confirm)

@dp.message(ReportForm.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        user_id = str(message.from_user.id)
        try:
            hours = float(data['hours'])
            amount = float(data['amount'])
        except:
            await message.answer("Ошибка: часы и сумма должны быть числами.", reply_markup=main_menu_kb())
            await state.clear()
            return
        if user_id not in user_stats:
            user_stats[user_id] = {'hours': 0, 'amount': 0}
        user_stats[user_id]['hours'] += hours
        user_stats[user_id]['amount'] += amount
        save_json(STATS_FILE, user_stats)

        # Получаем настройки пользователя
        settings = user_settings.get(user_id, {})
        payout_method = settings.get("payout_method", "не указано")
        requisites = settings.get("requisites", "не указано")
        country = settings.get("country", "не указано")
        bank = settings.get("bank", "не указано")

        report_text = (
            f"Новый отчет!\n"
            f"Номер стриммера: {data['streamer_id']}\n"
            f"Часы: {data['hours']}\n"
            f"Сумма: {data['amount']}\n"
            f"Отправитель: @{message.from_user.username or message.from_user.id}\n\n"
            f"Настройки:\n"
            f"Метод выплаты: {payout_method}\n"
            f"Реквизиты: {requisites}\n"
            f"Страна: {country}\n"
            f"Банк: {bank}"
        )
        # Отправляем всем админам и глобальным админам
        recipients = set(admins) | set(global_admins)
        for uid in recipients:
            try:
                await bot.send_message(int(uid), report_text)
            except:
                pass
        # Отправляем гифку
        try:
            with open("roblox-robux.gif", "rb") as gif:
                await message.answer_animation(gif)
        except:
            pass
        await message.answer("Ваш отчет отправлен!", reply_markup=main_menu_kb())
    else:
        await message.answer("Отмена отправки.", reply_markup=main_menu_kb())
    await state.clear()

@dp.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа.", reply_markup=ReplyKeyboardRemove())
        return
    user_id = str(message.from_user.id)
    stats = user_stats.get(user_id, {})
    await message.answer(
        f"Ваша статистика:\n"
        f"Всего часов: {stats.get('hours', 0)}\n"
        f"Общая сумма: {stats.get('amount', 0)}",
        reply_markup=main_menu_kb()
    )

@dp.message(F.text == "Настройки")
async def settings_menu(message: types.Message):
    user_id = str(message.from_user.id)
    settings = user_settings.get(user_id, {})
    payout_method = settings.get("payout_method", "не указано")
    requisites = settings.get("requisites", "не указано")
    country = settings.get("country", "не указано")
    bank = settings.get("bank", "не указано")
    stats = user_stats.get(user_id, {})
    total_hours = stats.get('hours', 0)
    total_amount = stats.get('amount', 0)
    text = (
        f"Ваши настройки:\n"
        f"Метод выплаты: {payout_method}\n"
        f"Реквизиты: {requisites}\n"
        f"Страна: {country}\n"
        f"Банк: {bank}\n\n"
        f"Статистика:\n"
        f"Всего часов: {total_hours}\n"
        f"Общая сумма: {total_amount}\n\n"
        "Выберите, что изменить:"
    )
    is_admin_ = is_admin(message.from_user.id)
    is_global_admin_ = is_global_admin(message.from_user.id)
    await message.answer(text, reply_markup=get_settings_menu_kb(is_admin_, is_global_admin_))

@dp.message(F.text == "Админ-панель")
async def admin_panel(message: types.Message):
    is_global_admin_ = is_global_admin(message.from_user.id)
    await message.answer("Админ-панель:", reply_markup=get_admin_panel_kb(is_global_admin_))

@dp.message(F.text == "Статистика пользователей")
async def stats_users(message: types.Message):
    if not is_global_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    if not user_stats:
        await message.answer("Нет данных.")
        return
    lines = ["Статистика по пользователям:"]
    for uid, stats in user_stats.items():
        try:
            user = await bot.get_chat(int(uid))
            name = user.username or user.full_name
        except:
            name = f"User {uid}"
        lines.append(f"{name}:\n  Часов: {stats.get('hours',0)}\n  Общая сумма: {stats.get('amount',0)}\n")
    await message.answer("\n".join(lines))

# Обработка кнопок в настройках
@dp.message(F.text == "Метод выплаты")
async def set_payout_method(message: types.Message, state: FSMContext):
    await message.answer("Введите метод выплаты (например, PayPal, карта и т.д.):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SettingsForm.payout_method)

@dp.message(F.text == "Реквизиты")
async def set_requisites(message: types.Message, state: FSMContext):
    await message.answer("Введите ваши реквизиты:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SettingsForm.requisites)

@dp.message(F.text == "Страна")
async def set_country(message: types.Message, state: FSMContext):
    await message.answer("Введите вашу страну:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SettingsForm.country)

@dp.message(F.text == "Банк")
async def set_bank(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш банк:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(SettingsForm.bank)

# Сохранение данных из ввода
@dp.message(SettingsForm.payout_method)
async def save_payout_method(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["payout_method"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Метод выплаты сохранён.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(SettingsForm.requisites)
async def save_requisites(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["requisites"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Реквизиты сохранены.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(SettingsForm.country)
async def save_country(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["country"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Страна сохранена.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(SettingsForm.bank)
async def save_bank(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["bank"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Банк сохранён.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
