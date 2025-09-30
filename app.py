import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import random
import os
import shutil 
from datetime import datetime # ДОБАВЛЕНО: для работы с датами

app = Flask(__name__)
# Указываем имя файла, а не путь
DATABASE_FILE = 'customers.db'
# Определяем путь к базе данных на Vercel. Временные файлы хранятся в /tmp.
DATABASE = os.path.join('/tmp', DATABASE_FILE)

# =========================================================================
# НОВАЯ ФУНКЦИЯ: Обеспечивает, что файл customers.db существует в /tmp
# =========================================================================
def ensure_db_exists():
    if not os.path.exists(DATABASE):
        # Если файл не существует в /tmp, копируем его из корневой папки.
        if os.path.exists(DATABASE_FILE):
            shutil.copyfile(DATABASE_FILE, DATABASE)
            print(f"База данных скопирована в {DATABASE}")
        else:
            print("ВНИМАНИЕ: База данных не найдена. Создание новой.")
            conn = sqlite3.connect(DATABASE)
            conn.close()

def get_db():
    """Устанавливает соединение с базой данных в /tmp."""
    ensure_db_exists() 
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
# =========================================================================

def get_products():
    # Список товаров остается без изменений
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

def generate_unique_code(conn):
    # Логика генерации кода остается без изменений
    while True:
        number = random.randint(1000, 9999) 
        code = f"A{number:04d}"
        exists = conn.execute('SELECT code FROM customers WHERE code = ?', (code,)).fetchone()
        if not exists:
            return code
            
# =========================================================================
# НОВАЯ/ИЗМЕНЕННАЯ: Функция для безопасного парсинга дат SQLite
# =========================================================================
def parse_date_robustly(date_string):
    """Пытается парсить дату в разных форматах SQLite (с микросекундами и без)."""
    if not date_string:
        return None
    # 1. Сначала пытаемся парсить с микросекундами (%f)
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        pass
    # 2. Если не сработало, пробуем без микросекунд
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        pass
        
    return None # Если все попытки неудачны


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
            
            # Обновляем время последнего посещения
            conn.execute('UPDATE customers SET last_visit = CURRENT_TIMESTAMP WHERE code = ?', (customer_code,))
            conn.commit()

    conn.close()

    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered,
                           products=get_products())

# МАРШРУТ: Личный кабинет (ИСПОЛЬЗУЕТ НОВУЮ ФУНКЦИЮ ПАРСИНГА)
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    if not customer_code:
        return redirect(url_for('index'))
    
    conn = get_db()
    
    customer = conn.execute(
        'SELECT name, registration_date FROM customers WHERE code = ?', 
        (customer_code,)
    ).fetchone()

    order_rows = conn.execute(
        'SELECT order_details, order_date, status FROM orders WHERE customer_code = ? ORDER BY order_date DESC', 
        (customer_code,)
    ).fetchall()
    
    conn.close()
    
    orders = []
    for row in order_rows:
        try:
            items = json.loads(row['order_details'])
        except json.JSONDecodeError:
            items = [{"name": "Ошибка данных", "qty": 1, "price": 0}]

        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ: Надежное получение объекта даты
        order_date_obj = parse_date_robustly(row['order_date'])

        orders.append({
            'order_date': order_date_obj,
            'status': row['status'],
            'items': items
        })

    # Форматируем дату регистрации клиента
    reg_date = "Дата неизвестна"
    if customer and customer['registration_date']:
        # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ: Надежное получение объекта даты
        reg_date_obj = parse_date_robustly(customer['registration_date'])
        
        if reg_date_obj:
            reg_date = reg_date_obj.strftime('%d.%m.%Y')

    return render_template('profile.html',
                           code=customer_code,
                           registration_date=reg_date,
                           orders=orders)


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
    
    resp = make_response(redirect(url_for('order_success', code=customer_code)))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    
    return resp

@app.route('/order_success')
def order_success():
    code = request.args.get('code', 'AXXXXX')
    return render_template('success.html', code=code)


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
    app.run(debug=True)