# Файл: setup_database.py

import sqlite3
import random
import string
import os

# 1. Функция для генерации случайного секретного кода
def generate_secret_code(length=8):
    # Генерируем случайную строку из букв и цифр
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# 2. Функция для создания базы данных и заполнения ее данными
def setup_db(num_codes=100):
    # Создаем соединение с файлом базы данных customers.db
    # Если файла нет, он будет создан
    conn = sqlite3.connect('customers.db')
    cursor = conn.cursor()

    # Создаем таблицу, если ее еще нет
    # TEXT - это просто текст, INTEGER - это целое число
    print("Создаем таблицу 'customers'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            qr_code_secret TEXT UNIQUE,
            customer_name TEXT,
            is_wallet_active INTEGER DEFAULT 0,
            order_history TEXT
        )
    """)
    conn.commit()

    # Проверяем, сколько кодов уже есть, чтобы не добавлять лишних
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]

    if count >= num_codes:
        print(f"В базе данных уже есть {count} записей. Новые не добавляем.")
        return

    # 3. Добавляем новые уникальные коды
    print(f"Добавляем {num_codes - count} уникальных записей...")
    codes = set()
    while len(codes) < num_codes - count:
        codes.add(generate_secret_code())

    data_to_insert = [(code, ) for code in codes]

    cursor.executemany("""
        INSERT INTO customers (qr_code_secret)
        VALUES (?)
    """, data_to_insert)

    conn.commit()
    conn.close()
    print("База данных успешно создана и заполнена!")

# Запускаем создание базы данных
if __name__ == '__main__':
    setup_db(num_codes=100)
    print("\nФайл 'customers.db' готов к работе!")