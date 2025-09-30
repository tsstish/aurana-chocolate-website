import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response
import json # Новый импорт для работы с данными заказа

app = Flask(__name__)
DATABASE = 'customers.db'

def get_db():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Функция для получения списка всех продуктов (для передачи в шаблон)
def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

# Добавляем маршрут для обработки главной страницы
@app.route('/')
def index():
    # 1. Получаем код клиента из куки
    customer_code = request.cookies.get('customer_code')
    
    # Инициализация переменных для передачи в шаблон
    name = None
    is_registered = False

    conn = get_db()
    
    if customer_code:
        # 2. Если код есть, пытаемся найти клиента и его имя
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

    # 3. Рендеринг шаблона с данными о клиенте и списке товаров
    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered,
                           products=get_products())

# Маршрут для обработки оформления заказа (включая регистрацию)
@app.route('/place_order', methods=['POST'])
def place_order():
    customer_code = request.cookies.get('customer_code')
    name = request.form.get('name')
    contact = request.form.get('contact') # Новый поле для контакта (телефон/email)
    
    # Сбор информации о заказе (список ID выбранных товаров)
    order_items = [prod for prod, qty in request.form.items() if prod.startswith('product_') and qty == '1']
    
    # Проверка обязательных полей
    if not name or not contact or not order_items:
        # В реальном приложении здесь будет сообщение об ошибке
        return "Ошибка: Укажите имя, контакт и выберите хотя бы один товар.", 400

    conn = get_db()
    
    # 1. Если код клиента не существует (новый клиент с Гугла)
    if not customer_code:
        # Генерируем новый код (предполагаем, что setup_database.py уже создал таблицу)
        cursor = conn.execute('SELECT code FROM customers ORDER BY id DESC LIMIT 1').fetchone()
        last_id = int(cursor[0][1:]) if cursor else 0
        new_id = last_id + 1
        customer_code = f"A{new_id:04d}" 
        
        # Добавляем нового анонимного клиента
        conn.execute(
            'INSERT INTO customers (code, name, contact, registered, registration_date, first_visit) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
            (customer_code, name, contact)
        )
    else:
        # 2. Если код клиента существует (QR или повторный заказ)
        # Обновляем имя и контакт (если они изменились) и ставим флаг регистрации
        conn.execute(
            'UPDATE customers SET name = ?, contact = ?, registered = 1, registration_date = COALESCE(registration_date, CURRENT_TIMESTAMP) WHERE code = ?',
            (name, contact, customer_code)
        )

    # 3. Сохраняем информацию о заказе в отдельную таблицу (предполагаем, что она создана)
    order_details = json.dumps(order_items) # Сохраняем список товаров как JSON
    conn.execute(
        'INSERT INTO orders (customer_code, order_details, status) VALUES (?, ?, ?)',
        (customer_code, order_details, 'Новый')
    )
    conn.commit()
    conn.close()
    
    # 4. Создаем ответ и устанавливаем куки для нового клиента
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
             'UPDATE customers SET first_visit = CURRENT_TIMESTAMP WHERE code = ? AND first_visit IS NULL', 
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