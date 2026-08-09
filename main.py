from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.routes import router

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

# Добавьте эту строчку для проверки!
print("Токен бота знайдено")

dp = Dispatcher()
dp.include_router(router)



async def main():
    bot = Bot(token=TOKEN)

    # Пропускаємо накопичені повідомлення за час, поки бот був вимкнений
    await bot.delete_webhook(drop_pending_updates=True)

    print("Start...")
    await dp.start_polling(bot)   


if __name__ == "__main__":
    asyncio.run(main())
