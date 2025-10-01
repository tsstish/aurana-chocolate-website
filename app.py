from flask import Flask, render_template, request, redirect, url_for, make_response
import random
from datetime import datetime
import json

app = Flask(__name__)

# Максимально упрощенные функции (нет БД, нет файлов)

def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

def generate_new_code():
    """Просто генерирует новый код без проверки на уникальность (для Vercel)."""
    return f"A{random.randint(1000, 9999):04d}"

# =========================================================================
# МАРШРУТЫ
# =========================================================================

@app.route('/')
def index():
    customer_code = request.cookies.get('customer_code')
    
    # Имя и статус регистрации теперь просто заглушки, т.к. данные не хранятся
    name = "Клиент" if customer_code else None
    is_registered = bool(customer_code)

    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered,
                           products=get_products())

# МАРШРУТ: Оформление заказа (Просто устанавливает куки и перенаправляет)
@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form.get('name', 'Клиент')
    order_details_json = request.form.get('order_details_json') 
    
    # Здесь была бы отправка данных во внешний API (CRM, Google Sheets и т.д.)
    # Сейчас мы просто генерируем код и перенаправляем.
    
    customer_code = request.cookies.get('customer_code')
    if not customer_code:
        customer_code = generate_new_code()
    
    # Логика: если заказ был, мы считаем его успешным
    if order_details_json and json.loads(order_details_json):
        # **ВНИМАНИЕ**: Здесь нет сохранения данных, только генерация кода и перенаправление.
        print(f"Заказ от {name} (код: {customer_code}). Детали: {order_details_json}. Данные НЕ СОХРАНЕНЫ.")
        
        resp = make_response(redirect(url_for('order_success', code=customer_code)))
        # Устанавливаем куки
        resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60, httponly=True) 
        
        return resp

    # Если заказ пустой или данные не пришли
    return redirect(url_for('index'))


# МАРШРУТ: Личный кабинет (Заглушка без истории)
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    if not customer_code:
        return redirect(url_for('index'))

    # Данные для шаблона - статические заглушки
    mock_orders = [
        {
            'order_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'status': 'Новый (не сохранен)',
            'items': [{"name": "Образец: Шоколад с клубникой", "qty": 1, "price": 1500}]
        },
    ]

    return render_template('profile.html',
                           code=customer_code,
                           customer_name="Клиент",
                           registration_date="сегодня",
                           orders=mock_orders)


@app.route('/order_success')
def order_success():
    code = request.args.get('code', 'AXXXXX')
    return render_template('success.html', code=code)


# QR-вход теперь просто устанавливает куки без проверки
@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    return resp


if __name__ == '__main__':
    app.run(debug=True)