import os
import logging
from telegram.ext import Updater, CommandHandler

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для команды /start
def start(update, context):
    update.message.reply_text("Привееет! 🎉")

def main():
    # Получаем токен из переменных окружения
    TOKEN = os.environ.get('BOT_TOKEN')
    
    # Проверяем, что токен есть
    if not TOKEN:
        logger.error("❌ Токен не найден! Установи переменную BOT_TOKEN в настройках Railway")
        return
    
    logger.info("✅ Токен получен, запускаем бота...")
    
    # Создаем бота
    updater = Updater(TOKEN, use_context=True)
    
    # Добавляем обработчик команды /start
    updater.dispatcher.add_handler(CommandHandler("start", start))
    
    # Запускаем бота
    logger.info("Бот запущен и работает! 🚀")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
