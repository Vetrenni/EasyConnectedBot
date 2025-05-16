import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = '7673946117:AAEzu5CSMfABRgvi9036Pz6cHJ08hP317z0'

STATS_FILE = "user_stats.json"
SETTINGS_FILE = "user_settings.json"
ALLOWED_USERS_FILE = "allowed_users.json"
ADMINS_FILE = "admins.json"
GLOBAL_ADMINS_FILE = "global_admins.json"

# --- Здесь укажи id глобальных админов через запятую ---
INITIAL_GLOBAL_ADMINS = ['5838284980']  # <-- впиши нужные id строками

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
        except Exception:
            return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE] else {}
    return [] if filename in [ADMINS_FILE, GLOBAL_ADMINS_FILE] else {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_stats = load_json(STATS_FILE)
user_settings = load_json(SETTINGS_FILE)
allowed_users = set(load_json(ALLOWED_USERS_FILE) or [])
admins = set(str(x) for x in load_json(ADMINS_FILE) or [])
global_admins = set(str(x) for x in load_json(GLOBAL_ADMINS_FILE) or [])

# Добавляем глобальных админов из исходного кода, если их ещё нет
for gid in INITIAL_GLOBAL_ADMINS:
    global_admins.add(str(gid))
save_json(GLOBAL_ADMINS_FILE, list(global_admins))

def main_menu_kb(is_global_admin=False):
    keyboard = [
        [KeyboardButton(text='Отправить отчет')],
        [KeyboardButton(text='Статистика')],
        [KeyboardButton(text='Настройки')],
    ]
    if is_global_admin:
        keyboard.append([KeyboardButton(text='Выдать админа')])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_settings_menu_kb(is_admin=False, is_global_admin=False):
    keyboard = [
        [KeyboardButton(text='Метод выплаты')],
        [KeyboardButton(text='Реквизиты')],
        [KeyboardButton(text='Страна')],
        [KeyboardButton(text='Банк')],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text='Добавить пользователя')])
    if is_global_admin:
        keyboard.append([KeyboardButton(text='Выдать админа')])
    keyboard.append([KeyboardButton(text='Назад в меню')])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

back_main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Назад в меню')]],
    resize_keyboard=True
)
back_settings_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Назад в настройки')]],
    resize_keyboard=True
)

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
    give_admin = State()

def is_allowed(user_id):
    return str(user_id) in allowed_users or is_admin(user_id) or is_global_admin(user_id)

def is_admin(user_id):
    return str(user_id) in admins

def is_global_admin(user_id):
    return str(user_id) in global_admins

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=main_menu_kb(is_global_admin(message.from_user.id))
    )

@dp.message(F.text == "Отправить отчет")
async def start_report(message: types.Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer("Введите номер стриммера:", reply_markup=back_main_kb)
    await state.set_state(ReportForm.streamer_id)

@dp.message(ReportForm.streamer_id, F.text == "Назад в меню")
@dp.message(ReportForm.hours, F.text == "Назад в меню")
@dp.message(ReportForm.amount, F.text == "Назад в меню")
@dp.message(ReportForm.confirm, F.text == "Назад в меню")
async def back_from_report(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb(is_global_admin(message.from_user.id)))

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
            await message.answer("Ошибка: количество часов и сумма должны быть числами.", reply_markup=main_menu_kb(is_global_admin(message.from_user.id)))
            await state.clear()
            return

        if user_id not in user_stats:
            user_stats[user_id] = {"hours": 0.0, "amount": 0.0}
        user_stats[user_id]["hours"] += hours
        user_stats[user_id]["amount"] += amount
        save_json(STATS_FILE, user_stats)

        # Прикрепляем настройки пользователя
        settings = user_settings.get(user_id, {})
        payout_method = settings.get("payout_method", "не указано")
        requisites = settings.get("requisites", "не указано")
        country = settings.get("country", "не указано")
        bank = settings.get("bank", "не указано")

        report_text = (
            f"Новый отчет!\n"
            f"Номер стриммера: {data['streamer_id']}\n"
            f"Количество часов: {data['hours']}\n"
            f"Сумма: {data['amount']}\n"
            f"Отправитель: @{message.from_user.username or message.from_user.id}\n\n"
            f"Настройки пользователя:\n"
            f"Метод выплаты: {payout_method}\n"
            f"Реквизиты: {requisites}\n"
            f"Страна: {country}\n"
            f"Банк: {bank}"
        )
        # Отправляем отчет всем admin и global_admin
        recipients = set(admins) | set(global_admins)
        for admin_user_id in recipients:
            try:
                await bot.send_message(int(admin_user_id), report_text)
            except Exception:
                pass
        await message.answer("Ваш отчет отправлен!", reply_markup=main_menu_kb(is_global_admin(message.from_user.id)))
    else:
        await message.answer("Отправка отчета отменена.", reply_markup=main_menu_kb(is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(F.text == "Статистика")
async def show_statistics(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())
        return
    user_id = str(message.from_user.id)
    stats = user_stats.get(user_id)
    if stats:
        await message.answer(
            f"Ваша статистика:\n"
            f"Общее количество часов: {stats['hours']}\n"
            f"Общая сумма: {stats['amount']}",
            reply_markup=main_menu_kb(is_global_admin(message.from_user.id))
        )
    else:
        await message.answer("У вас пока нет отправленных отчетов.", reply_markup=main_menu_kb(is_global_admin(message.from_user.id)))

@dp.message(F.text == "Настройки")
async def settings_menu(message: types.Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту. Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())
        return
    user_id = str(message.from_user.id)
    settings = user_settings.get(user_id, {})
    payout_method = settings.get("payout_method", "не указано")
    requisites = settings.get("requisites", "не указано")
    country = settings.get("country", "не указано")
    bank = settings.get("bank", "не указано")
    is_admin_ = is_admin(message.from_user.id)
    is_global_admin_ = is_global_admin(message.from_user.id)
    text = (
        f"Ваши текущие настройки:\n"
        f"Метод выплаты: {payout_method}\n"
        f"Реквизиты: {requisites}\n"
        f"Страна: {country}\n"
        f"Банк: {bank}\n\n"
        "Выберите, что хотите изменить:"
    )
    await message.answer(text, reply_markup=get_settings_menu_kb(is_admin_, is_global_admin_))

@dp.message(F.text == "Назад в меню")
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb(is_global_admin(message.from_user.id)))

@dp.message(F.text == "Метод выплаты")
async def set_payout_method(message: types.Message, state: FSMContext):
    await message.answer("Введите метод выплаты (например, PayPal, карта и т.д.):", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.payout_method)

@dp.message(SettingsForm.payout_method, F.text == "Назад в настройки")
async def back_from_settings_payout(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

@dp.message(SettingsForm.payout_method)
async def save_payout_method(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["payout_method"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Метод выплаты сохранён.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(F.text == "Реквизиты")
async def set_requisites(message: types.Message, state: FSMContext):
    await message.answer("Введите ваши реквизиты:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.requisites)

@dp.message(SettingsForm.requisites, F.text == "Назад в настройки")
async def back_from_settings_requisites(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

@dp.message(SettingsForm.requisites)
async def save_requisites(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["requisites"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Реквизиты сохранены.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(F.text == "Страна")
async def set_country(message: types.Message, state: FSMContext):
    await message.answer("Введите вашу страну:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.country)

@dp.message(SettingsForm.country, F.text == "Назад в настройки")
async def back_from_settings_country(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

@dp.message(SettingsForm.country)
async def save_country(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["country"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Страна сохранена.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(F.text == "Банк")
async def set_bank(message: types.Message, state: FSMContext):
    await message.answer("Введите ваш банк:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.bank)

@dp.message(SettingsForm.bank, F.text == "Назад в настройки")
async def back_from_settings_bank(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

@dp.message(SettingsForm.bank)
async def save_bank(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_settings.setdefault(user_id, {})["bank"] = message.text
    save_json(SETTINGS_FILE, user_settings)
    await message.answer("Банк сохранён.", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()

@dp.message(F.text == "Добавить пользователя")
async def add_user_start(message: types.Message, state: FSMContext):
    if not (is_admin(message.from_user.id) or is_global_admin(message.from_user.id)):
        await message.answer("У вас нет прав для этого действия.")
        return
    await message.answer("Введите Telegram user id пользователя, которому хотите дать доступ:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.add_user)

@dp.message(SettingsForm.add_user, F.text == "Назад в настройки")
async def back_from_add_user(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

@dp.message(SettingsForm.add_user)
async def add_user_process(message: types.Message, state: FSMContext):
    if not (is_admin(message.from_user.id) or is_global_admin(message.from_user.id)):
        await message.answer("У вас нет прав для этого действия.")
        await state.clear()
        return
    new_user_id = message.text.strip()
    if not new_user_id.isdigit():
        await message.answer("User id должен быть числом. Попробуйте ещё раз или нажмите 'Назад в настройки'.")
        return
    allowed_users.add(new_user_id)
    save_json(ALLOWED_USERS_FILE, list(allowed_users))
    await message.answer(f"Пользователь с user id {new_user_id} добавлен!", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), is_global_admin(message.from_user.id)))
    await state.clear()
    # Уведомление пользователя о доступе
    try:
        await bot.send_message(int(new_user_id), "Вам выдан доступ к боту! Теперь вы можете им пользоваться.")
    except Exception:
        pass

@dp.message(F.text == "Выдать админа")
async def give_admin_start(message: types.Message, state: FSMContext):
    if not is_global_admin(message.from_user.id):
        await message.answer("У вас нет прав для этого действия.")
        return
    await message.answer("Введите Telegram user id пользователя, которому хотите сделать админом:", reply_markup=back_settings_kb)
    await state.set_state(SettingsForm.give_admin)

@dp.message(SettingsForm.give_admin, F.text == "Назад в настройки")
async def back_from_give_admin(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

@dp.message(SettingsForm.give_admin)
async def give_admin_process(message: types.Message, state: FSMContext):
    if not is_global_admin(message.from_user.id):
        await message.answer("У вас нет прав для этого действия.")
        await state.clear()
        return
    new_admin_id = message.text.strip()
    if not new_admin_id.isdigit():
        await message.answer("User id должен быть числом. Попробуйте ещё раз или нажмите 'Назад в настройки'.")
        return
    admins.add(new_admin_id)
    save_json(ADMINS_FILE, list(admins))
    await message.answer(f"Пользователь с user id {new_admin_id} теперь админ!", reply_markup=get_settings_menu_kb(is_admin(message.from_user.id), True))
    await state.clear()
    # Уведомление пользователя о доступе
    try:
        await bot.send_message(int(new_admin_id), "Вам выдан статус администратора бота!")
    except Exception:
        pass

@dp.message(F.text == "Назад в настройки")
async def back_to_settings(message: types.Message, state: FSMContext):
    await state.clear()
    await settings_menu(message, state)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
