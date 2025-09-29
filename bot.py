import os
import logging
import csv
import json
from datetime import datetime, timedelta
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
    'sleep': "😴 Легла спать",
    'wake_up': "🌅 Встала утром", 
    'breakfast': "🍳 Завтрак",
    'lunch': "🍲 Обед", 
    'dinner': "🍽️ Ужин",
    'workout_start': "💪 Начала тренировку",
    'workout_end': "✅ Закончила тренировку"
}

# Символы для графиков
GRAPH_SYMBOLS = {
    'sleep': '😴',
    'wake_up': '🌅', 
    'breakfast': '🍳',
    'lunch': '🍲',
    'dinner': '🍽️',
    'workout_start': '💪',
    'workout_end': '✅'
}

class SleepTrackerBot:
    def __init__(self):
        self.data_file = 'events_data.json'
        self._init_data_file()
    
    def _init_data_file(self):
        """Инициализация файла данных"""
        try:
            if not os.path.exists(self.data_file):
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                logger.info("✅ Файл данных инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации файла: {e}")
    
    def save_event(self, user_id, event_type):
        """Сохранение события в файл"""
        try:
            # Читаем существующие данные
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
            else:
                events = []
            
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
            if not os.path.exists(self.data_file):
                return []
                
            with open(self.data_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            user_events = [e for e in events if e['user_id'] == user_id]
            user_events.sort(key=lambda x: x['timestamp'])
            
            return [(e['event_type'], e['timestamp']) for e in user_events]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения событий: {e}")
            return []
    
    def get_week_events(self, user_id):
        """Получение событий за последние 7 дней"""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            all_events = self.get_user_events(user_id)
            
            week_events = []
            for event_type, timestamp_str in all_events:
                event_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                if event_time >= week_ago:
                    week_events.append((event_type, timestamp_str))
            
            return week_events
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения событий за неделю: {e}")
            return []
    
    def create_week_chart(self, user_id):
        """Создание текстового графика за неделю"""
        try:
            week_events = self.get_week_events(user_id)
            
            if not week_events:
                return "📊 За последнюю неделю событий не было"
            
            # Группируем события по дням
            days_events = {}
            for event_type, timestamp_str in week_events:
                event_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                day_key = event_time.strftime('%Y-%m-%d')
                day_name = event_time.strftime('%a')  # Сокр. название дня
                
                if day_key not in days_events:
                    days_events[day_key] = {'name': day_name, 'events': []}
                
                time_str = event_time.strftime('%H:%M')
                days_events[day_key]['events'].append((time_str, event_type))
            
            # Сортируем дни по дате
            sorted_days = sorted(days_events.items())
            
            # Создаем график
            chart = "📊 АКТИВНОСТЬ ЗА НЕДЕЛЮ:\n\n"
            
            for day_key, day_data in sorted_days[-7:]:  # Последние 7 дней
                date_obj = datetime.strptime(day_key, '%Y-%m-%d')
                date_str = date_obj.strftime('%d.%m')
                
                chart += f"📅 {date_str} ({day_data['name']}):\n"
                
                if day_data['events']:
                    # Сортируем события по времени
                    day_data['events'].sort()
                    
                    for time_str, event_type in day_data['events']:
                        symbol = GRAPH_SYMBOLS.get(event_type, '•')
                        name = EVENT_TYPES.get(event_type, 'Событие')
                        chart += f"   {symbol} {time_str} - {name}\n"
                else:
                    chart += "   ─── событий не было ───\n"
                
                chart += "\n"
            
            # Статистика
            total_events = len(week_events)
            unique_days = len(days_events)
            chart += f"📈 ИТОГО: {total_events} событий за {unique_days} дней"
            
            return chart
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания графика: {e}")
            return "❌ Ошибка при создании графика"
    
    def create_hourly_chart(self, user_id):
        """Создание графика по часам за неделю"""
        try:
            week_events = self.get_week_events(user_id)
            
            if not week_events:
                return "⏰ За последнюю неделю событий не было"
            
            # Считаем события по часам
            hourly_count = {i: 0 for i in range(24)}
            
            for event_type, timestamp_str in week_events:
                event_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                hour = event_time.hour
                hourly_count[hour] += 1
            
            # Создаем график
            chart = "⏰ АКТИВНОСТЬ ПО ЧАСАМ (неделя):\n\n"
            
            max_count = max(hourly_count.values()) if hourly_count.values() else 1
            
            for hour in range(24):
                count = hourly_count[hour]
                # Создаем строку графика
                bar_length = int((count / max_count) * 10) if max_count > 0 else 0
                bar = '█' * bar_length
                
                hour_str = f"{hour:02d}:00"
                chart += f"{hour_str} {bar} {count} событий\n"
            
            total_events = len(week_events)
            most_active_hour = max(hourly_count, key=hourly_count.get) if hourly_count else "нет"
            chart += f"\n📊 Всего событий: {total_events}"
            chart += f"\n🎯 Самый активный час: {most_active_hour}:00"
            
            return chart
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания часового графика: {e}")
            return "❌ Ошибка при создании графика"
    
    def export_to_csv(self, user_id):
        """Экспорт событий в CSV"""
        try:
            events = self.get_user_events(user_id)
            
            # Создаем CSV в памяти как строку
            output = StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow(['Тип события', 'Время', 'Описание'])
            
            # Данные
            for event_type, timestamp in events:
                description = EVENT_TYPES.get(event_type, 'Неизвестно')
                writer.writerow([event_type, timestamp, description])
            
            # Возвращаем строку (не bytes!)
            csv_string = output.getvalue()
            output.close()
            
            return csv_string
            
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

🎯 Команды:
/start - показать кнопки
/stats - статистика за неделю  
/chart - график по часам
/csv - скачать данные в CSV
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

def stats_command(update, context):
    """Обработчик команды /stats - статистика за неделю"""
    try:
        user_id = update.effective_user.id
        chart = tracker.create_week_chart(user_id)
        
        # Разбиваем на части если слишком длинное сообщение
        if len(chart) > 4000:
            parts = [chart[i:i+4000] for i in range(0, len(chart), 4000)]
            for part in parts:
                update.message.reply_text(part)
        else:
            update.message.reply_text(chart)
            
        logger.info(f"✅ Пользователь {user_id} запросил статистику")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в stats_command: {e}")
        update.message.reply_text("❌ Ошибка при получении статистики")

def chart_command(update, context):
    """Обработчик команды /chart - график по часам"""
    try:
        user_id = update.effective_user.id
        chart = tracker.create_hourly_chart(user_id)
        update.message.reply_text(chart)
        logger.info(f"✅ Пользователь {user_id} запросил часовой график")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в chart_command: {e}")
        update.message.reply_text("❌ Ошибка при создании графика")

def csv_command(update, context):
    """Обработчик команды /csv - экспорт в CSV"""
    try:
        user_id = update.effective_user.id
        events = tracker.get_user_events(user_id)
        
        if not events:
            update.message.reply_text("📝 У вас еще нет записанных событий.")
            return
        
        csv_data = tracker.export_to_csv(user_id)
        
        if csv_data:
            # Кодируем в bytes только при отправке
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
            timestamp = tracker.save_event(user_id, event_type)
            
            if timestamp:
                event_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                formatted_time = event_time.strftime('%H:%M:%S')
                
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
        TOKEN = os.environ.get('BOT_TOKEN')
        
        if not TOKEN:
            logger.error("❌ Токен не найден! Установи переменную BOT_TOKEN")
            return
        
        logger.info("✅ Токен получен, запускаем бота...")
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("stats", stats_command))
        dp.add_handler(CommandHandler("chart", chart_command))
        dp.add_handler(CommandHandler("csv", csv_command))
        dp.add_handler(CallbackQueryHandler(button_handler))
        dp.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен и работает! 🚀")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")

if __name__ == "__main__":
    main()
