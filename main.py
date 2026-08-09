import os
from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.routes import router
from aiohttp import web

# 1. Завантажуємо змінні оточення
load_dotenv()
TOKEN = getenv("BOT_TOKEN")

# Перевірка наявності токена
if not TOKEN:
    raise ValueError("BOT_TOKEN не знайдено в змінних оточення!")

print("Токен бота знайдено")

# 2. Створюємо об'єкти Bot та Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)

# 3. Сервер для підтримки роботи на Render
async def handle_health(request):
    return web.Response(text="Bot is active!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# 4. Головна функція
async def main():
    # Запускаємо мікро-вебсервер для Render
    await start_dummy_server()
    
    # Запускаємо бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())