from telegram.ext import Updater, CommandHandler
import logging

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для команды /start
def start(update, context):
    update.message.reply_text("Привееет! 🎉")

def main():
    # Твой токен бота
    TOKEN = "7578614408:AAH2vKc9k0Y7q8vx1s7v8v8N9tN9tN9tN9t"
    
    # Создаем бота
    updater = Updater(TOKEN, use_context=True)
    
    # Добавляем обработчик команды /start
    updater.dispatcher.add_handler(CommandHandler("start", start))
    
    # Запускаем бота
    logger.info("Бот запускается...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
