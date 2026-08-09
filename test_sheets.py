import os
from datetime import datetime

@router.callback_query(OrderForm.service, F.data.startswith("service_"))
async def process_service_callback(call: CallbackQuery, state: FSMContext):
    selected_service = call.data.replace("service_", "")
    await state.update_data(service=selected_service)
    
    # Отримуємо зібрані дані з FSM
    user_data = await state.get_data()
    
    # Синхронна функція для роботи з Google Таблицею (приймає дані як аргумент)
    def save_to_sheets(data):
        spreadsheet_name = os.getenv("SPREADSHEET_NAME", "Записи з Telegram-бота")
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open(spreadsheet_name)
        worksheet = sh.sheet1
        
        # 1. Створюємо шапку, якщо таблиця порожня
        if not worksheet.row_values(1):
            worksheet.append_row(["Ім'я", "Телефон", "Послуга", "Дата"])
            
        # 2. Формуємо рядок з датою
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        row_to_add = [data['name'], data['phone'], data['service'], created_at]
        
        # 3. Додаємо в таблицю
        worksheet.append_row(row_to_add)

    # Запускаємо в окремому потоці, передаючи user_data
    await asyncio.to_thread(save_to_sheets, user_data)
    
    await call.message.edit_text(
        f"✅ Дякуємо! Ви обрали: **{selected_service}**.\nВаші дані успішно збережено в Google Таблицю.", 
        parse_mode="Markdown"
    )
    await call.answer()
    await state.clear()