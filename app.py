import sqlite3 # Оставляем импорт, но не используем его
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import random
import os
from datetime import datetime
import csv # Используем CSV для сохранения данных
from threading import Lock

app = Flask(__name__)

# Путь для временного хранения данных заказа в Vercel
ORDERS_FILE = os.path.join('/tmp', 'orders.csv')
CUSTOMERS_FILE = os.path.join('/tmp', 'customers.json')
file_lock = Lock()

# =========================================================================
# ФУНКЦИИ УПРАВЛЕНИЯ ДАННЫМИ (ЗАГЛУШКИ)
# =========================================================================

def ensure_files_exist():
    """Создает пустые файлы заказов и клиентов, если они не существуют."""
    with file_lock:
        if not os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['customer_code', 'order_details', 'status', 'order_date'])
        
        if not os.path.exists(CUSTOMERS_FILE):
            with open(CUSTOMERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)

def load_customers():
    """Загружает данные клиентов из JSON-файла."""
    ensure_files_exist()
    with file_lock:
        with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

def save_customers(data):
    """Сохраняет данные клиентов в JSON-файл."""
    with file_lock:
        with open(CUSTOMERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

def load_orders(customer_code=None):
    """Загружает заказы из CSV-файла."""
    ensure_files_exist()
    orders = []
    with file_lock:
        with open(ORDERS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not customer_code or row['customer_code'] == customer_code:
                    orders.append(row)
    # Сортировка по дате (имитация БД)
    orders.sort(key=lambda x: x['order_date'], reverse=True)
    return orders

def generate_unique_code(customers):
    while True:
        number = random.randint(1000, 9999) 
        code = f"A{number:04d}"
        if code not in customers:
            return code

# =========================================================================
# ОСТАЛЬНЫЕ ФУНКЦИИ И МАРШРУТЫ
# =========================================================================

def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]
            
def format_date_for_display(date_string):
    if not date_string:
        return "Дата неизвестна"
    try:
        dt_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S.%f')
        return dt_obj.strftime('%d.%m.%Y %H:%M')
    except ValueError:
        return date_string # Если не можем распарсить, возвращаем как есть

# МАРШРУТ: Главная страница
@app.route('/')
def index():
    customer_code = request.cookies.get('customer_code')
    customers = load_customers()
    name = None
    is_registered = False

    if customer_code and customer_code in customers:
        customer_data = customers[customer_code]
        name = customer_data.get('name')
        is_registered = True
        
        # Обновляем время последнего посещения
        customers[customer_code]['last_visit'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        save_customers(customers)
        
    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered,
                           products=get_products())


# МАРШРУТ: Личный кабинет (Теперь использует файлы-заглушки)
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    if not customer_code:
        return redirect(url_for('index'))
    
    customers = load_customers()
    
    customer = customers.get(customer_code)
    
    if not customer:
        return redirect(url_for('index'))

    # Загружаем заказы по коду клиента
    order_rows = load_orders(customer_code)
    
    orders = []
    for row in order_rows:
        try:
            items = json.loads(row['order_details'])
        except (json.JSONDecodeError, TypeError):
            items = [{"name": "Ошибка данных заказа", "qty": 1, "price": 0}]

        orders.append({
            'order_date': format_date_for_display(row['order_date']),
            'status': row['status'],
            'items': items
        })

    reg_date = format_date_for_display(customer.get('registration_date'))

    return render_template('profile.html',
                           code=customer_code,
                           customer_name=customer.get('name', 'Клиент'),
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

    customers = load_customers()
    
    try:
        # 1. Обработка клиента
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        if not customer_code or customer_code not in customers:
            customer_code = generate_unique_code(customers)
            customers[customer_code] = {
                'code': customer_code,
                'name': name,
                'contact': contact,
                'registered': 1,
                'registration_date': now_str,
                'first_visit': now_str,
                'last_visit': now_str
            }
        else:
            customers[customer_code].update({
                'name': name,
                'contact': contact,
                'registered': 1,
                'last_visit': now_str
            })
        
        save_customers(customers)

        # 2. Сохранение заказа в CSV
        order_data = {
            'customer_code': customer_code,
            'order_details': order_details_json,
            'status': 'Новый',
            'order_date': now_str
        }
        
        with file_lock:
            with open(ORDERS_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(list(order_data.values()))
        
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА сохранения заказа в файл: {e}")
        return redirect(url_for('index')) 
    
    # 3. Перенаправляем на страницу успеха
    resp = make_response(redirect(url_for('order_success', code=customer_code)))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60, httponly=True) 
    
    return resp

@app.route('/order_success')
def order_success():
    code = request.args.get('code', 'AXXXXX')
    return render_template('success.html', code=code)


@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    customers = load_customers()
    
    if customer_code in customers:
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        customers[customer_code]['last_visit'] = now_str
        customers[customer_code]['first_visit'] = customers[customer_code].get('first_visit', now_str)
        save_customers(customers)
        
        return resp
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    ensure_files_exist() 
    app.run(debug=True)