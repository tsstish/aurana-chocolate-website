import sqlite3

DATABASE = 'customers.db'

def setup_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 1. Модифицируем таблицу customers, чтобы добавить contact
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            contact TEXT,  -- ПОЛЕ CONTACT ДОЛЖНО БЫТЬ ТУТ
            registered INTEGER DEFAULT 0,
            first_visit TIMESTAMP,
            last_visit TIMESTAMP,
            registration_date TIMESTAMP
        )
    ''')
    
    # 2. Создаем новую таблицу для хранения заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_code TEXT NOT NULL,
            order_details TEXT NOT NULL,  -- ТАБЛИЦА ORDERS ДОЛЖНА БЫТЬ ТУТ
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Новый',
            FOREIGN KEY(customer_code) REFERENCES customers(code)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных 'customers.db' обновлена: добавлено поле 'contact' и создана таблица 'orders'.")

if __name__ == '__main__':
    setup_database()