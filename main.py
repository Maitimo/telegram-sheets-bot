from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.routes import router
from aiohttp import web

# 1. Функція для перевірки статусу Render
async def handle_health(request):
    return web.Response(text="Bot is active!")

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

# Добавьте эту строчку для проверки!
print("Токен бота знайдено")

dp = Dispatcher()
dp.include_router(router)


async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передає порт через змінну оточення PORT (за замовчуванням 10000 або 8080)
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# 2. Оновлена головна функція main()
async def main():
    # Запускаємо вебсервер для Render
    await start_dummy_server()
    
    # Запускаємо сам бот
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())