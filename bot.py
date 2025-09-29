import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для типов событий
EVENT_TYPES = {
    'sleep': "Легла спать",
    'wake_up': "Встала утром", 
    'breakfast': "Завтрак",
    'lunch': "Обед",
    'dinner': "Ужин",
    'workout_start': "Начала тренировку",
    'workout_end': "Закончила тренировку"
}

class SleepTrackerBot:
    def __init__(self):
        self.db_path = 'sleep_tracker.db'
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT,
                timestamp DATETIME
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_event(self, user_id: int, event_type: str):
        """Сохранение события в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            'INSERT INTO events (user_id, event_type, timestamp) VALUES (?, ?, ?)',
            (user_id, event_type, timestamp)
        )
        conn.commit()
        conn.close()
        logger.info(f"Событие сохранено: user={user_id}, type={event_type}")
        return timestamp

# Инициализация бота
tracker = SleepTrackerBot()

# Токен бота
TOKEN = os.environ.get('BOT_TOKEN', '7578614408:AAH2vKc9k0Y7q8vx1s7v8v8N9tN9tN9tN9t')

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    welcome_text = """
    👋 Привет! Я бот для отслеживания твоего распорядка дня.

    📊 Я помогу тебе отслеживать:
    • Время сна и пробуждения
    • Приемы пищи
    • Тренировки

    🎯 Используй кнопки ниже для записи событий!
    """
    
    keyboard = [
        [
            InlineKeyboardButton("Легла спать", callback_data='sleep'),
            InlineKeyboardButton("Встала утром", callback_data='wake_up')
        ],
        [
            InlineKeyboardButton("Завтрак", callback_data='breakfast'),
            InlineKeyboardButton("Обед", callback_data='lunch'),
            InlineKeyboardButton("Ужин", callback_data='dinner')
        ],
        [
            InlineKeyboardButton("Начала тренировку", callback_data='workout_start'),
            InlineKeyboardButton("Закончила тренировку", callback_data='workout_end')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup)
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")

def button_handler(update: Update, context: CallbackContext):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    event_type = query.data
    
    if event_type in EVENT_TYPES:
        try:
            # Сохраняем событие
            timestamp = tracker.save_event(user_id, event_type)
            
            # Форматируем время для ответа
            event_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            formatted_time = event_time.strftime('%H:%M:%S')
            
            # Обновляем клавиатуру
            keyboard = [
                [
                    InlineKeyboardButton("Легла спать", callback_data='sleep'),
                    InlineKeyboardButton("Встала утром", callback_data='wake_up')
                ],
                [
                    InlineKeyboardButton("Завтрак", callback_data='breakfast'),
                    InlineKeyboardButton("Обед", callback_data='lunch'),
                    InlineKeyboardButton("Ужин", callback_data='dinner')
                ],
                [
                    InlineKeyboardButton("Начала тренировку", callback_data='workout_start'),
                    InlineKeyboardButton("Закончила тренировку", callback_data='workout_end')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем подтверждение
            query.edit_message_text(
                text=f"✅ {EVENT_TYPES[event_type]} записано в {formatted_time}",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка сохранения события: {e}")
            query.edit_message_text(
                text="❌ Произошла ошибка при сохранении события"
            )

def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция"""
    # Создаем Updater и передаем ему токен
    updater = Updater(TOKEN, use_context=True)
    
    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
    
    # Добавляем обработчики
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запускается...")
    updater.start_polling()
    
    # Запускаем бота до тех пор, пока пользователь не остановит его
    updater.idle()

if __name__ == "__main__":
    main()
