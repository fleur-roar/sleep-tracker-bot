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
