import os
from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.routes import router
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# 1. Завантажуємо змінні оточення
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
BASE_WEBHOOK_URL = getenv("RENDER_EXTERNAL_URL")  # Render створює цю змінну автоматично

if not TOKEN:
    raise ValueError("BOT_TOKEN не знайдено в змінних оточення!")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

# 2. Створюємо об'єкти Bot та Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)

# 3. Обробники подій запуску та зупинки вебхука
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

# 4. Перевірка здоров'я для Render
async def handle_health(request):
    return web.Response(text="Bot is active!")

# 5. Головна функція запуску
def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/", handle_health)

    # Налаштовуємо обробку запитів від Telegram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()