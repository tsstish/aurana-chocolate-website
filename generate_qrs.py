# Файл: generate_qrs.py

import sqlite3
import qrcode
import os

# !!! ВАЖНО: Замените "http://mysite.com" на реальный адрес, 
# который будет у твоего сайта (мы его настроим позже, 
# но для печати уже нужна заглушка).
BASE_URL = "http://auranachocolate.com/" 

# Папка для сохранения QR-кодов
OUTPUT_DIR = "qrcodes_for_print" 
os.makedirs(OUTPUT_DIR, exist_ok=True) # Создаем папку, если ее нет

def get_db_connection():
    conn = sqlite3.connect('customers.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_qr_images():
    print("--- Начинаем генерацию QR-кодов для печати ---")
    conn = get_db_connection()
    # Получаем все секретные коды из базы
    codes = conn.execute('SELECT qr_code_secret FROM customers').fetchall()
    conn.close()

    count = 0
    for row in codes:
        secret_code = row['qr_code_secret']
        # 1. Формируем полную ссылку
        full_url = BASE_URL + secret_code
        
        # 2. Создаем QR-код
        img = qrcode.make(full_url)
        
        # 3. Сохраняем как файл
        file_path = os.path.join(OUTPUT_DIR, f"aurana_qr_{secret_code}.png")
        img.save(file_path)
        count += 1
    
    print(f"Готово! Создано {count} файлов QR-кодов.")
    print(f"Они находятся в папке: {OUTPUT_DIR}")

if __name__ == '__main__':
    generate_qr_images()