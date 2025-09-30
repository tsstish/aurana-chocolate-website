import sqlite3

DATABASE = 'customers.db'

def setup_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Создаем или модифицируем таблицу customers
    # TEXT для имен, INTEGER для флагов, TIMESTAMP для дат
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            registered INTEGER DEFAULT 0,
            first_visit TIMESTAMP,
            last_visit TIMESTAMP,
            registration_date TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных 'customers.db' обновлена с полями name, registered, dates.")

if __name__ == '__main__':
    setup_database()