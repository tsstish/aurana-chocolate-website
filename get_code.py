# Файл: get_code.py
import sqlite3

conn = sqlite3.connect('customers.db')
cursor = conn.cursor()

# Запрашиваем самый первый секретный код
cursor.execute("SELECT qr_code_secret FROM customers LIMIT 1;")

secret_code = cursor.fetchone()[0]

conn.close()

print("\nВаш секретный код для тестирования:\n")
print("====================================")
print(secret_code)
print("====================================\n")