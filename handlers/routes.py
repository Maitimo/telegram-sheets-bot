import os
import asyncio
import gspread
from datetime import datetime
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, 
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# 1. Описуємо стани FSM
class OrderForm(StatesGroup):
    name = State()
    phone = State()
    service = State()

# Словник повернень (Поточний крок -> Попередній крок та текст)
PREVIOUS_STEPS = {
    OrderForm.phone.state: (OrderForm.name, "Повертаємося назад. Введіть ваше ім'я заново:"),
    OrderForm.service.state: (OrderForm.phone, "Повертаємося назад. Введіть ваш номер телефону:"),
}

# --- КЛАВІАТУРИ ---

# Початкова Inline-клавіатура
start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📝 Записатися на послугу", callback_data="start_booking")]
    ]
)

# Inline-клавіатура послуг
services_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 Карьєрний аудит", callback_data="service_Карьерний аудит")],
        [InlineKeyboardButton(text="💡 Консультація", callback_data="service_Консультація")],
        [InlineKeyboardButton(text="🤖 Розробка бота", callback_data="service_Розробка бота")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel")]
    ]
)

# Навігаційна Reply-клавіатура для текстових кроків
nav_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="⬅️ Назад"), 
            KeyboardButton(text="❌ Скасувати")
        ]
    ],
    resize_keyboard=True
)


# --- ГЛОБАЛЬНІ КОМАНДИ ТА НАВІГАЦІЯ (Стоять вгорі!) ---

# 2. Старт: показуємо початкову кнопку
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вітаю! Натисніть кнопку нижче, щоб розпочати запис:",
        reply_markup=start_keyboard
    )

# Хендлер скасування через команду /cancel або Reply-кнопку "❌ Скасувати"
@router.message(Command("cancel"))
@router.message(F.text == "❌ Скасувати")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Запис скасовано. Ви повернулися в головне меню.", 
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Вітаю! Натисніть кнопку нижче, щоб розпочати запис:", 
        reply_markup=start_keyboard
    )

# Хендлер скасування через Inline-кнопку "❌ Скасувати"
@router.callback_query(F.data == "cancel")
async def cancel_callback_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Запис скасовано.") 
    await call.answer()

# Універсальний хендлер кнопки "⬅️ Назад"
@router.message(F.text == "⬅️ Назад")
async def process_back_button(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    # 1. Якщо для поточного стану є крок назад у словнику
    if current_state in PREVIOUS_STEPS:
        previous_state, text = PREVIOUS_STEPS[current_state]
        await state.set_state(previous_state)
        await message.answer(text, reply_markup=nav_reply_keyboard)
        
    # 2. Якщо користувач на найпершому кроці (введення імені) або без стану
    else:
        await state.clear()
        await message.answer("Ви повернулися в головне меню.", reply_markup=ReplyKeyboardRemove())
        await message.answer("Вітаю! Натисніть кнопку нижче, щоб розпочати запис:", reply_markup=start_keyboard)


# --- ОСНОВНИЙ ЛАНЦЮЖОК ЗБОРУ ДАНИХ (FSM) ---

# 3. Натискання "Записатися": старт FSM і запит імені
@router.callback_query(F.data == "start_booking")
async def start_booking_callback(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderForm.name)
    await call.message.answer(
        "Введіть ваше ім'я для запису:", 
        reply_markup=nav_reply_keyboard
    )
    await call.answer()

# 4. Збір імені -> запит телефону
@router.message(OrderForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.phone)
    # кнопка з запитом телефону
    phone_keybord = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Надіслати номер телефону", request_contact=True)],
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Скасувати")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Тепер введіть ваш номер телефону:", 
        reply_markup=phone_keybord
    )

# 5. Збір телефону -> вивід інлайн-кнопок послуг
@router.message(OrderForm.phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext):
    # Обробка кнопки "Назад"
    if message.text == "⬅️ Назад":
        await state.set_state(OrderForm.name)
        await message.answer(
            "Повертаємося назад. Введіть ваше ім'я:",
            reply_markup=get_cancel_keyboard()
        )
        return
    # Отримуємо номер: або з об'єкта contact, або з текстового повідомлення
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text

    await state.update_data(phone=phone_number)
    await state.set_state(OrderForm.service)
    
    # Видаляємо Reply-клавіатуру з кнопкою контакту та показуємо Inline-послуги
    await message.answer(
        f"Приймаю телефон: **{phone_number}**.\nТепер оберіть послугу:",
        reply_markup=services_keyboard,
        parse_mode="Markdown"
    )

# 6. Фінальний крок: Обробка натискання кнопки послуги та запис у Google Таблицю
@router.callback_query(OrderForm.service, F.data.startswith("service_"))
async def process_service_callback(call: CallbackQuery, state: FSMContext):
    selected_service = call.data.replace("service_", "")
    await state.update_data(service=selected_service)
    
    user_data = await state.get_data()
    
    # 1. ГЕНЕРУЄМО ДАТУ
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 2. ДОДАЄМО created_at ЧЕТВЕРТИМ ЕЛЕМЕНТОМ
    row_to_add = [user_data['name'], user_data['phone'], user_data['service'], created_at]
    
    def save_to_sheets():
        spreadsheet_name = os.getenv("SPREADSHEET_NAME", "Записи з Telegram-бота")
        creds_path = "/etc/secrets/credentials.json" if os.path.exists("/etc/secrets/credentials.json") else "credentials.json"
        gc = gspread.service_account(filename=creds_path)
        sh = gc.open(spreadsheet_name)
        worksheet = sh.sheet1
        worksheet.append_row(row_to_add)

    await asyncio.to_thread(save_to_sheets)

    # сповіщення адміністратора
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        admin_text =(
        "🚀 **НОВА ЗАЯВКА!**\n\n"
            f"👤 **Ім'я:** {user_data['name']}\n"
            f"📞 **Телефон:** {user_data['phone']}\n"
            f"💼 **Послуга:** {user_data['service']}\n"
            f"🕒 **Дата:** {created_at}\n\n"
            f"🔗 **Профіль клієнта:** [{call.from_user.full_name}](tg://user?id={call.from_user.id})"

        )
        try:
            await call.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Помилка при сповіщенні адміністратора: {e}")

   # Відповідь користувачу
    await call.message.edit_text(
        f"✅ Дякуємо! Ви обрали: **{selected_service}**.\nВаші дані успішно збережено в Google Таблицю.", 
        parse_mode="Markdown"
    )
    await call.answer()
    await state.clear()