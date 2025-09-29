import os
import logging
import csv
import json
from datetime import datetime
from io import StringIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

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
        self.data_file = 'events_data.json'
        self._init_data_file()
    
    def _init_data_file(self):
        """Инициализация файла данных"""
        try:
            # Если файла нет - создаем пустой
            if not os.path.exists(self.data_file):
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                logger.info("✅ Файл данных инициализирован")
            else:
                logger.info("✅ Файл данных уже существует")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации файла: {e}")
    
    def save_event(self, user_id, event_type):
        """Сохранение события в файл"""
        try:
            # Читаем существующие данные
            with open(self.data_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            # Добавляем новое событие
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_event = {
                'user_id': user_id,
                'event_type': event_type,
                'timestamp': timestamp
            }
            events.append(new_event)
            
            # Сохраняем обратно
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Событие сохранено: user={user_id}, type={event_type}")
            return timestamp
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            return None
    
    def get_user_events(self, user_id):
        """Получение всех событий пользователя"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            # Фильтруем по user_id
            user_events = [e for e in events if e['user_id'] == user_id]
            # Сортируем по времени
            user_events.sort(key=lambda x: x['timestamp'])
            
            return [(e['event_type'], e['timestamp']) for e in user_events]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения событий: {e}")
            return []
    
    def export_to_csv(self, user_id):
        """Экспорт событий в CSV"""
        try:
            events = self.get_user_events(user_id)
            
            # Создаем CSV в памяти
            output = StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow(['Тип события', 'Время', 'Описание'])
            
            # Данные
            for event_type, timestamp in events:
                description = EVENT_TYPES.get(event_type, 'Неизвестно')
                writer.writerow([event_type, timestamp, description])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта CSV: {e}")
            return ""

# Создаем экземпляр трекера
tracker = SleepTrackerBot()

def start(update, context):
    """Обработчик команды /start"""
    try:
        welcome_text = """
👋 Привет! Я бот для отслеживания распорядка дня.

📊 Отслеживай:
• Сон и пробуждение
• Приемы пищи  
• Тренировки

🎯 Используй кнопки для записи!
📥 /csv - скачать данные в CSV
"""
        
        keyboard = [
            [
                InlineKeyboardButton("😴 Легла спать", callback_data='sleep'),
                InlineKeyboardButton("🌅 Встала утром", callback_data='wake_up')
            ],
            [
                InlineKeyboardButton("🍳 Завтрак", callback_data='breakfast'),
                InlineKeyboardButton("🍲 Обед", callback_data='lunch'), 
                InlineKeyboardButton("🍽️ Ужин", callback_data='dinner')
            ],
            [
                InlineKeyboardButton("💪 Начала тренировку", callback_data='workout_start'),
                InlineKeyboardButton("✅ Закончила тренировку", callback_data='workout_end')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info(f"✅ Пользователь {update.effective_user.id} запустил бота")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}")

def csv_command(update, context):
    """Обработчик команды /csv - экспорт в CSV"""
    try:
        user_id = update.effective_user.id
        events = tracker.get_user_events(user_id)
        
        if not events:
            update.message.reply_text("📝 У вас еще нет записанных событий.")
            return
        
        # Создаем CSV
        csv_data = tracker.export_to_csv(user_id)
        
        if csv_data:
            # Отправляем файл
            update.message.reply_document(
                document=('events.csv', csv_data.encode('utf-8')),
                caption="📊 Ваши данные в CSV формате"
            )
            logger.info(f"✅ Пользователь {user_id} экспортировал CSV")
        else:
            update.message.reply_text("❌ Ошибка при создании CSV файла")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в csv_command: {e}")
        update.message.reply_text("❌ Ошибка при экспорте данных")

def button_handler(update, context):
    """Обработчик нажатий на кнопки"""
    try:
        query = update.callback_query
        query.answer()
        
        user_id = query.from_user.id
        event_type = query.data
        
        if event_type in EVENT_TYPES:
            # Сохраняем событие
            timestamp = tracker.save_event(user_id, event_type)
            
            if timestamp:
                event_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                formatted_time = event_time.strftime('%H:%M:%S')
                
                # Обновляем сообщение с кнопками
                keyboard = [
                    [
                        InlineKeyboardButton("😴 Легла спать", callback_data='sleep'),
                        InlineKeyboardButton("🌅 Встала утром", callback_data='wake_up')
                    ],
                    [
                        InlineKeyboardButton("🍳 Завтрак", callback_data='breakfast'),
                        InlineKeyboardButton("🍲 Обед", callback_data='lunch'),
                        InlineKeyboardButton("🍽️ Ужин", callback_data='dinner')
                    ],
                    [
                        InlineKeyboardButton("💪 Начала тренировку", callback_data='workout_start'),
                        InlineKeyboardButton("✅ Закончила тренировку", callback_data='workout_end')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                query.edit_message_text(
                    text=f"✅ {EVENT_TYPES[event_type]} записано в {formatted_time}",
                    reply_markup=reply_markup
                )
            else:
                query.edit_message_text("❌ Ошибка при сохранении события")
                
    except Exception as e:
        logger.error(f"❌ Ошибка в button_handler: {e}")

def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f"❌ Ошибка бота: {context.error}")

def main():
    """Основная функция"""
    try:
        # Получаем токен из переменных окружения
        TOKEN = os.environ.get('BOT_TOKEN')
        
        if not TOKEN:
            logger.error("❌ Токен не найден! Установи переменную BOT_TOKEN")
            return
        
        logger.info("✅ Токен получен, запускаем бота...")
        
        # Создаем бота
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("csv", csv_command))
        dp.add_handler(CallbackQueryHandler(button_handler))
        dp.add_error_handler(error_handler)
        
        # Запускаем бота
        logger.info("✅ Бот запущен и работает! 🚀")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")

if __name__ == "__main__":
    main()
