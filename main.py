import telebot
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import signal
import sys
import os
import random

API_TOKEN = 'ТОКЕН'
bot = telebot.TeleBot(API_TOKEN)

stop_flag = False
CHAT_ID = ID_ЧАТА

HOLIDAYS = {
    12: {31: "Новый год"},
    2: {23: "День защитника Отечества"},
    3: {8: "Международный женский день"},
    5: {1: "Праздник Весны и Труда", 9: "День Победы"},
    6: {12: "День России"},
    11: {4: "День народного единства"}
}

def check_holiday():
    today = datetime.now()
    month = today.month
    day = today.day
    if month in HOLIDAYS and day in HOLIDAYS[month]:
        return HOLIDAYS[month][day]
    return None

def get_holiday_image(holiday_name):
    picture_folder = "pictureHoliday"
    if not os.path.exists(picture_folder):
        return None
    
    today = datetime.now()
    date_str = f"{today.day:02d}.{today.month:02d}"
    
    for filename in os.listdir(picture_folder):
        if filename.startswith(date_str) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return os.path.join(picture_folder, filename)
    
    holiday_lower = holiday_name.lower()
    for filename in os.listdir(picture_folder):
        filename_lower = filename.lower()
        if (holiday_lower in filename_lower or 
            any(word in filename_lower for word in holiday_lower.split())) and \
           filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return os.path.join(picture_folder, filename)
    
    return None

def load_birthdays(file_path):
    df = pd.read_excel(file_path)
    df['Дата рождения'] = pd.to_datetime(df['Дата рождения'], dayfirst=True)
    return df

def check_birthdays(df):
    today = datetime.now().date()
    upcoming_birthdays = []
    
    for i in range(8):
        check_date = today + timedelta(days=i)
        
        for index, row in df.iterrows():
            bd_date = row['Дата рождения'].date()
            bd_day_month = (bd_date.month, bd_date.day)
            check_day_month = (check_date.month, check_date.day)
            
            if bd_day_month == check_day_month:
                if i == 0:
                    message_type = "сегодня"
                else:
                    message_type = f"через {i} дней"
                upcoming_birthdays.append((row, message_type, check_date))
    
    return upcoming_birthdays

def send_messages(df):
    try:
        holiday = check_holiday()
        if holiday:
            holiday_message = f"🎊 Сегодня {holiday}! 🎉"
            
            holiday_image = get_holiday_image(holiday)
            
            if holiday_image and os.path.exists(holiday_image):
                try:
                    with open(holiday_image, 'rb') as photo:
                        bot.send_photo(CHAT_ID, photo, caption=holiday_message)
                    print(f"Отправлен праздник с картинкой: {holiday_message}")
                except Exception as e:
                    print(f"Ошибка отправки фото праздника: {e}")
                    bot.send_message(CHAT_ID, holiday_message)
            else:
                bot.send_message(CHAT_ID, holiday_message)
                print(f"Отправлен праздник: {holiday_message}")
        
        upcoming_birthdays = check_birthdays(df)
        
        picture_folder = "pictureDR"
        images = []
        if os.path.exists(picture_folder):
            images = [f for f in os.listdir(picture_folder) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        
        if not upcoming_birthdays:
            print("На этой неделе дней рождений нет.")
        else:
            for person, days_info, check_date in upcoming_birthdays:
                if days_info == "сегодня":
                    message = f"🎉 Поздравляем {person['ФИО']} с днём рождения! 🎂"
                    
                    if images:
                        random_image = random.choice(images)
                        image_path = os.path.join(picture_folder, random_image)
                        
                        try:
                            with open(image_path, 'rb') as photo:
                                bot.send_photo(CHAT_ID, photo, caption=message)
                            print(f"Отправлено с картинкой: {message}")
                        except Exception as e:
                            print(f"Ошибка отправки фото: {e}")
                            bot.send_message(CHAT_ID, message)
                    else:
                        bot.send_message(CHAT_ID, message)
                        print(f"Отправлено: {message}")
                else:
                    date_str = check_date.strftime('%d.%m')
                    message = f"📅 У {person['ФИО']} день рождения {days_info} ({date_str})"
                    bot.send_message(CHAT_ID, message)
                    print(f"Отправлено: {message}")
                
    except Exception as e:
        print(f"Ошибка при отправке сообщений: {e}")

def schedule_daily_check():
    global stop_flag
    birthdays_df = load_birthdays('birthdays.xlsx')
    
    send_messages(birthdays_df)
    
    # Закрываем окно после отправки
    time.sleep(5)
    os._exit(0)

def signal_handler(sig, frame):
    global stop_flag
    print("\nПолучен сигнал остановки...")
    stop_flag = True
    print("Бот остановлен.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    print("Запуск бота...")
    print(f"Сегодня: {datetime.now().strftime('%d.%m.%Y')}")
    print(f"Используется chat_id: {CHAT_ID}")
    
    try:
        bot.send_message(CHAT_ID, "🤖 Бот запущен! Проверка связи...")
        print("Проверка связи: ОК")
    except Exception as e:
        print(f"Проверка связи: ОШИБКА - {e}")
        print("Убедитесь, что бот добавлен в чат и является администратором")
        time.sleep(5)
        sys.exit(1)
    
    holiday = check_holiday()
    if holiday:
        print(f"Сегодня праздник: {holiday}")
        
        holiday_image = get_holiday_image(holiday)
        if holiday_image:
            print(f"Найдена картинка праздника: {os.path.basename(holiday_image)}")
        else:
            print("Картинка для праздника не найдена")
    
    birthdays_df = load_birthdays('birthdays.xlsx')
    
    print("\nДни рождения в файле:")
    for _, row in birthdays_df.iterrows():
        print(f"{row['ФИО']}: {row['Дата рождения'].strftime('%d.%m.%Y')}")
    
    picture_folder = "pictureDR"
    if os.path.exists(picture_folder):
        images = [f for f in os.listdir(picture_folder) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        print(f"\nНайдено картинок для ДР: {len(images)}")
    else:
        print("\nПапка pictureDR не найдена")
    
    holiday_folder = "pictureHoliday"
    if os.path.exists(holiday_folder):
        holiday_images = [f for f in os.listdir(holiday_folder) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        print(f"Найдено картинок праздников: {len(holiday_images)}")
        for img in holiday_images:
            print(f"  - {img}")
    
    print("\nОтправка сообщений...")
    daily_check_thread = threading.Thread(target=schedule_daily_check, daemon=True)
    daily_check_thread.start()
    
    print("Окно закроется автоматически через 5 секунд...")
    time.sleep(10)
    os._exit(0)