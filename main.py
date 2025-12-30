import telebot
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import signal
import sys
import os
import random

API_TOKEN = '7522419708:AAGp0LE1YxJwGMlwINBDwcqoneBsEowAw5Q'
bot = telebot.TeleBot(API_TOKEN)

# Флаг для остановки потоков
stop_flag = False

def load_birthdays(file_path):
    df = pd.read_excel(file_path)
    df['Дата рождения'] = pd.to_datetime(df['Дата рождения'], dayfirst=True)
    return df

def check_birthdays(df):
    today = datetime.now().date()
    today_day_month = (today.month, today.day)
    
    upcoming_birthdays = []
    
    # Проверяем на 8 дней вперед (сегодня + 7 дней)
    for i in range(8):  # От 0 до 7 дней
        check_date = today + timedelta(days=i)
        
        # Для каждой записи в DataFrame проверяем, совпадает ли день и месяц
        for index, row in df.iterrows():
            bd_date = row['Дата рождения'].date()
            bd_day_month = (bd_date.month, bd_date.day)
            check_day_month = (check_date.month, check_date.day)
            
            # Если день и месяц совпадают
            if bd_day_month == check_day_month:
                if i == 0:
                    message_type = "сегодня"
                else:
                    message_type = f"через {i} дней"
                upcoming_birthdays.append((row, message_type, check_date))
    
    return upcoming_birthdays

def send_messages(df):
    try:
        upcoming_birthdays = check_birthdays(df)
        
        # ID-шник чата
        chat_id = 1673134064
        
        # Получаем список картинок
        picture_folder = "pictureDR"
        images = []
        if os.path.exists(picture_folder):
            images = [f for f in os.listdir(picture_folder) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        
        if not upcoming_birthdays:
            print("На этой неделе дней рождений нет.")
        else:
            # Отправляем все сообщения
            for person, days_info, check_date in upcoming_birthdays:
                if days_info == "сегодня":
                    message = f"🎉 Поздравляем {person['ФИО']} с днём рождения! 🎂"
                    
                    # Отправляем с картинкой если есть
                    if images:
                        random_image = random.choice(images)
                        image_path = os.path.join(picture_folder, random_image)
                        
                        try:
                            with open(image_path, 'rb') as photo:
                                bot.send_photo(chat_id, photo, caption=message)
                            print(f"Отправлено с картинкой: {message}")
                        except Exception as e:
                            print(f"Ошибка отправки фото: {e}")
                            bot.send_message(chat_id, message)
                    else:
                        bot.send_message(chat_id, message)
                        print(f"Отправлено: {message}")
                else:
                    # Форматируем дату для отображения
                    date_str = check_date.strftime('%d.%m')
                    message = f"📅 У {person['ФИО']} день рождения {days_info} ({date_str})"
                    bot.send_message(chat_id, message)
                    print(f"Отправлено: {message}")
                
    except Exception as e:
        print(f"Ошибка при отправке сообщений: {e}")

def schedule_daily_check():
    global stop_flag
    birthdays_df = load_birthdays('birthdays.xlsx')
    
    # Отправляем сообщение сразу при запуске
    send_messages(birthdays_df)
    
    while not stop_flag:
        try:
            # Проверяем время - отправляем каждый день в 9:00
            current_time = datetime.now().time()
            
            if current_time.hour == 9 and current_time.minute == 0:
                send_messages(birthdays_df)
                # Ждем 61 секунду, чтобы не отправить дважды в одну минуту
                time.sleep(61)
            else:
                # Ждем 30 секунд и проверяем снова
                time.sleep(30)
                
        except Exception as e:
            print(f"Ошибка в потоке проверки: {e}")
            time.sleep(300)

def signal_handler(sig, frame):
    global stop_flag
    print("\nПолучен сигнал остановки...")
    stop_flag = True
    print("Бот остановлен.")
    sys.exit(0)

# Регистрируем обработчик Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print("Запуск бота... Нажмите Ctrl+C для остановки.")
    print(f"Сегодня: {datetime.now().strftime('%d.%m.%Y')}")
    
    birthdays_df = load_birthdays('birthdays.xlsx')
    
    # Выводим информацию о днях рождениях в консоль для отладки
    print("\nДни рождения в файле:")
    for _, row in birthdays_df.iterrows():
        print(f"{row['ФИО']}: {row['Дата рождения'].strftime('%d.%m.%Y')}")
    
    # Проверяем наличие папки с картинками
    picture_folder = "pictureDR"
    if os.path.exists(picture_folder):
        images = [f for f in os.listdir(picture_folder) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        print(f"\nНайдено картинок: {len(images)}")
    else:
        print("\nПапка pictureDR не найдена")
    
    # Запуск проверки в отдельном потоке
    daily_check_thread = threading.Thread(target=schedule_daily_check, daemon=True)
    daily_check_thread.start()
    
    print("\nБот запущен. Проверка дней рождений работает в фоне.")
    
    try:
        # Простой polling с возможностью остановки
        while not stop_flag:
            try:
                bot.polling(none_stop=True, timeout=10)
            except Exception as e:
                if not stop_flag:
                    print(f"Ошибка polling: {e}")
                    time.sleep(5)
                    
    except KeyboardInterrupt:
        print("\nОстановка по Ctrl+C...")
        stop_flag = True
    finally:
        print("Бот завершил работу.")