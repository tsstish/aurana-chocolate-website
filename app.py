import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import random # Для генерации уникальных кодов

app = Flask(__name__)
DATABASE = 'customers.db'

def get_db():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Функция для получения списка всех продуктов (для передачи в шаблон)
def get_products():
    # Важно: ID и цены должны совпадать с теми, что используются в JS
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

# ИСПРАВЛЕННАЯ: Функция для генерации уникального кода
def generate_unique_code(conn):
    """Генерирует уникальный 4-значный код клиента, начиная с 'A'."""
    while True:
        # Генерация 4-значного числа
        number = random.randint(1000, 9999) 
        code = f"A{number:04d}"
        
        # Проверка уникальности
        exists = conn.execute('SELECT code FROM customers WHERE code = ?', (code,)).fetchone()
        if not exists:
            return code


# Добавляем маршрут для обработки главной страницы
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

# ИСПРАВЛЕННЫЙ: Маршрут для обработки оформления заказа
@app.route('/place_order', methods=['POST'])
def place_order():
    customer_code = request.cookies.get('customer_code')
    name = request.form.get('name')
    contact = request.form.get('contact')
    order_details_json = request.form.get('order_details_json') 
    
    if not name or not contact or not order_details_json:
        # В случае ошибки возвращаем обратно на главную
        return redirect(url_for('index')) 

    conn = get_db()
    
    # 1. Если код клиента не существует (новый клиент)
    if not customer_code:
        # Генерируем новый уникальный код
        customer_code = generate_unique_code(conn)
        
        # Добавляем нового клиента (используя контакт!)
        conn.execute(
            'INSERT INTO customers (code, name, contact, registered, registration_date, first_visit, last_visit) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
            (customer_code, name, contact)
        )
    else:
        # 2. Если код клиента существует
        # Обновляем имя и контакт (если они изменились)
        conn.execute(
            'UPDATE customers SET name = ?, contact = ?, registered = 1, last_visit = CURRENT_TIMESTAMP WHERE code = ?',
            (name, contact, customer_code)
        )

    # 3. Сохраняем информацию о заказе
    conn.execute(
        'INSERT INTO orders (customer_code, order_details, status) VALUES (?, ?, ?)',
        (customer_code, order_details_json, 'Новый')
    )
    conn.commit()
    conn.close()
    
    # 4. Создаем ответ и устанавливаем куки
    resp = make_response(redirect(url_for('order_success', code=customer_code)))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    
    return resp

# Маршрут для страницы успешного заказа
@app.route('/order_success')
def order_success():
    code = request.args.get('code', 'AXXXXX')
    return render_template('success.html', code=code)


# Маршрут для обработки сканирования QR-кода (установка куки)
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