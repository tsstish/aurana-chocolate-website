import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import random
import os
import shutil 
from datetime import datetime

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
            
# =========================================================================
# ФУНКЦИЯ ФОРМАТИРОВАНИЯ ДАТЫ (РАБОТАЕТ НА СЕРВЕРЕ И ВОЗВРАЩАЕТ СТРОКУ)
# =========================================================================
def format_date_for_display(date_string):
    """Пытается парсить дату в разных форматах SQLite и возвращает готовую строку."""
    if not date_string:
        return "Дата неизвестна"
        
    # 1. Попытка с микросекундами
    try:
        dt_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
        return dt_obj.strftime('%d.%m.%Y %H:%M')
    except ValueError:
        pass
    # 2. Попытка без микросекунд
    try:
        dt_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return dt_obj.strftime('%d.%m.%Y %H:%M')
    except ValueError:
        pass
        
    return "Ошибка формата даты"


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

# МАРШРУТ: Личный кабинет (ИСПОЛЬЗУЕТ БЕЗОПАСНОЕ ФОРМАТИРОВАНИЕ ДАТЫ)
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
    ).