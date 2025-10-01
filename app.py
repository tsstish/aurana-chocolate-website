import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import random
import os
from datetime import datetime
from threading import Lock
import traceback # Добавлен для отладки, если ошибка останется

app = Flask(__name__)
# Указываем имя файла, а не путь
DATABASE_FILE = 'customers.db'
# Определяем путь к базе данных на Vercel. Временные файлы хранятся в /tmp.
DATABASE = os.path.join('/tmp', DATABASE_FILE)
# Защита от одновременного доступа к БД
db_lock = Lock()


# =========================================================================
# ФУНКЦИИ БАЗЫ ДАННЫХ И ИНИЦИАЛИЗАЦИЯ
# =========================================================================
def init_db():
    # Эта функция гарантирует, что БД и таблицы существуют в /tmp
    with db_lock:
        conn = None
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # Создание таблицы клиентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    registered INTEGER DEFAULT 0,
                    registration_date TEXT,
                    first_visit TEXT,
                    last_visit TEXT
                )
            """)
            
            # Создание таблицы заказов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code TEXT,
                    order_details TEXT NOT NULL,
                    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'Новый',
                    FOREIGN KEY (customer_code) REFERENCES customers(code)
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"Ошибка при инициализации БД: {e}")
        finally:
            if conn:
                conn.close()

def get_db():
    """Устанавливает соединение с базой данных в /tmp и инициализирует ее, если необходимо."""
    init_db() # Гарантируем, что таблицы существуют
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

def generate_unique_code(conn):
    while True:
        number = random.randint(1000, 9999) 
        code = f"A{number:04d}"
        exists = conn.execute('SELECT code FROM customers WHERE code = ?', (code,)).fetchone()
        if not exists:
            return code
            
# ФУНКЦИЯ ФОРМАТИРОВАНИЯ ДАТЫ (С МАКСИМАЛЬНОЙ ЗАЩИТОЙ ОТ ПАДЕНИЯ)
def format_date_for_display(date_string):
    """Пытается парсить дату в разных форматах SQLite и возвращает готовую строку."""
    if not date_string:
        return "Дата неизвестна"
        
    # Пытаемся парсить в разных форматах
    formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    
    for fmt in formats:
        try:
            dt_obj = datetime.strptime(date_string, fmt)
            return dt_obj.strftime('%d.%m.%Y %H:%M')
        except ValueError:
            continue # Пробуем следующий формат
        
    return "Ошибка формата даты"


# =========================================================================
# МАРШРУТ: Личный кабинет (Основной источник 500-й ошибки)
# =========================================================================
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    if not customer_code:
        return redirect(url_for('index'))
    
    conn = get_db()
    
    # 1. Защита при получении данных клиента
    try:
        customer = conn.execute(
            'SELECT name, registration_date FROM customers WHERE code = ?', 
            (customer_code,)
        ).fetchone()
    except Exception:
        customer = None
        
    # 2. Получение данных заказов
    try:
        order_rows = conn.execute(
            'SELECT order_details, order_date, status FROM orders WHERE customer_code = ? ORDER BY order_date DESC', 
            (customer_code,)
        ).fetchall()
    except Exception:
        order_rows = []
        
    conn.close()
    
    orders = []
    for row in order_rows:
        try:
            # Десериализация JSON с защитой
            items = json.loads(row['order_details'])
        except (json.JSONDecodeError, TypeError):
            items = [{"name": "Ошибка данных заказа", "qty": 1, "price": 0}]

        orders.append({
            'order_date': format_date_for_display(row['order_date']),
            'status': row['status'],
            'items': items
        })

    # 3. Форматирование даты регистрации с защитой
    if customer and customer['registration_date']:
        reg_date = format_date_for_display(customer['registration_date'])
    else:
        reg_date = "Дата неизвестна"

    # Если customer не найден (хотя код есть), используем заглушку
    customer_name = customer['name'] if customer and customer['name'] else "Клиент"

    return render_template('profile.html',
                           code=customer_code,
                           customer_name=customer_name, # Можно использовать в шаблоне
                           registration_date=reg_date,
                           orders=orders)

# =========================================================================
# ОСТАЛЬНЫЕ МАРШРУТЫ (оставлены без изменений, как в предыдущем ответе)
# =========================================================================

@app.route('/')
def index():
    customer_code = request.cookies.get('customer_code')
    name = None
    is_registered = False

    conn = get_db()
    
    if customer_code:
        customer_data = conn.execute(
            'SELECT name, registered, last_visit FROM customers WHERE code = ?', 
            (customer_code,)
        ).fetchone()

        if customer_data:
            name = customer_data['name']
            is_registered = customer_data['registered']
            
            conn.execute('UPDATE customers SET last_visit = CURRENT_TIMESTAMP WHERE code = ?', (customer_code,))
            conn.commit()

    conn.close()

    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered,
                           products=get_products())


@app.route('/place_order', methods=['POST'])
def place_order():
    customer_code = request.cookies.get('customer_code')
    name = request.form.get('name')
    contact = request.form.get('contact')
    order_details_json = request.form.get('order_details_json') 
    
    if not name or not contact or not order_details_json:
        return redirect(url_for('index')) 

    conn = get_db()
    
    if not customer_code:
        customer_code = generate_unique_code(conn)
        
        conn.execute(
            'INSERT INTO customers (code, name, contact, registered, registration_date, first_visit) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
            (customer_code, name, contact)
        )
    else:
        conn.execute(
            'UPDATE customers SET name = ?, contact = ?, registered = 1, last_visit = CURRENT_TIMESTAMP WHERE code = ?',
            (name, contact, customer_code)
        )

    conn.execute(
        'INSERT INTO orders (customer_code, order_details, status) VALUES (?, ?, ?)',
        (customer_code, order_details_json, 'Новый')
    )
    conn.commit()
    conn.close()
    
    # ФИКС: Перенаправляем на страницу успеха (order_success), которая затем отправляет в ЛК
    resp = make_response(redirect(url_for('order_success', code=customer_code)))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    
    return resp

@app.route('/order_success')
def order_success():
    # Эта страница просто нужна как промежуточная точка для установки cookie
    code = request.args.get('code', 'AXXXXX')
    
    # Сразу перенаправляем в личный кабинет, чтобы исключить задержки
    return redirect(url_for('profile'))


@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    conn = get_db()
    
    exists = conn.execute('SELECT code FROM customers WHERE code = ?', (customer_code,)).fetchone()
    
    if exists:
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
        
        conn.execute(
             'UPDATE customers SET first_visit = COALESCE(first_visit, CURRENT_TIMESTAMP), last_visit = CURRENT_TIMESTAMP WHERE code = ?', 
             (customer_code,)
        )
        conn.commit()
        conn.close()
        return resp
    else:
        conn.close()
        return redirect(url_for('index'))

if __name__ == '__main__':
    init_db() 
    app.run(debug=True)