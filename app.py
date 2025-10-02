from flask import Flask, render_template, request, redirect, url_for, make_response
import random
from datetime import datetime
import json
import os

app = Flask(__name__)

# --- Константы и Файловая система ---

ORDER_FILE = 'orders.json'

def load_orders():
    """Загружает заказы из JSON-файла."""
    if not os.path.exists(ORDER_FILE) or os.path.getsize(ORDER_FILE) == 0:
        return []
    try:
        with open(ORDER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Если файл пуст или некорректен
        return []

def save_orders(orders):
    """Сохраняет заказы в JSON-файл."""
    with open(ORDER_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

def generate_new_code():
    """Генерирует новый код клиента."""
    return f"A{random.randint(1000, 9999):04d}"

# --- Маршруты ---

@app.route('/')
def index():
    customer_code = request.cookies.get('customer_code')
    
    # Имя будет 'Клиент' только для отображения в форме
    name = "Клиент" if customer_code else None
    
    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           products=get_products())

# МАРШРУТ: Оформление заказа (Сохранение данных в orders.json)
@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form.get('name', 'Клиент')
    contact = request.form.get('contact', 'Не указан')
    order_details_json = request.form.get('order_details_json') 
    
    customer_code = request.cookies.get('customer_code')
    is_new_customer = False

    if not customer_code:
        customer_code = generate_new_code()
        is_new_customer = True
    
    # Логика: если данные заказа пришли и не пусты
    if order_details_json:
        try:
            order_details = json.loads(order_details_json)
        except json.JSONDecodeError:
            order_details = []

        if order_details:
            new_order = {
                'code': customer_code,
                'name': name,
                'contact': contact,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'items': order_details,
                'status': 'Новый'
            }
            
            # Сохранение заказа
            all_orders = load_orders()
            all_orders.append(new_order)
            save_orders(all_orders)

            # Формирование ответа
            resp = make_response(redirect(url_for('order_success', code=customer_code)))
            
            # Устанавливаем куки, если клиент новый или куки не было
            if is_new_customer:
                resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60, httponly=True) 
            
            return resp

    # Если заказ пустой или данные не пришли, возвращаем на главную
    return redirect(url_for('index'))


@app.route('/order_success')
def order_success():
    code = request.args.get('code', 'AXXXXX')
    return render_template('success.html', code=code)


# МАРШРУТ: Личный кабинет (Отображение истории из orders.json)
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    if not customer_code:
        # Если нет куки, отправляем на главную
        return redirect(url_for('index'))

    # Фильтруем заказы для текущего клиента
    all_orders = load_orders()
    client_orders = [
        {
            'order_date': datetime.strptime(o['date'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M'),
            'status': o['status'],
            'items': o['items']
        }
        for o in all_orders if o.get('code') == customer_code
    ]
    
    # Предполагаем имя из первого заказа, если оно есть
    customer_name = next((o['name'] for o in all_orders if o.get('code') == customer_code), "Клиент")
    
    return render_template('profile.html',
                           code=customer_code,
                           customer_name=customer_name,
                           registration_date="N/A", # Нет данных о регистрации в этой простой версии
                           orders=client_orders)


# QR-вход (Устанавливает куки и перенаправляет)
@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    return resp


if __name__ == '__main__':
    # Создаем пустой файл, если его нет
    if not os.path.exists(ORDER_FILE):
        save_orders([])
    app.run(debug=True)