from flask import Flask, render_template, request, redirect, url_for, make_response
import random
from datetime import datetime

app = Flask(__name__)

# --- Вспомогательные функции ---

def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

def generate_new_code():
    """Генерирует код, но он не будет использоваться для сохранения истории."""
    return f"A{random.randint(1000, 9999):04d}"

# --- Маршруты ---

@app.route('/')
def index():
    customer_code = request.cookies.get('customer_code')
    
    # Всегда генерируем код, если его нет (для отображения в форме)
    if not customer_code:
        customer_code = generate_new_code()
    
    return render_template('index.html', 
                           customer_code=customer_code,
                           products=get_products())

# МАРШРУТ: Оформление заказа (Просто устанавливает куки и перенаправляет)
@app.route('/place_order', methods=['POST'])
def place_order():
    # Мы могли бы здесь отправить данные в Formspree, но пока просто перенаправим
    
    customer_code = request.cookies.get('customer_code')
    is_new_customer = False

    if not customer_code:
        customer_code = generate_new_code()
        is_new_customer = True

    # Перенаправление на страницу успеха
    resp = make_response(redirect(url_for('order_success', code=customer_code)))
    
    if is_new_customer:
        # Устанавливаем куки
        resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    
    return resp


@app.route('/order_success')
def order_success():
    code = request.args.get('code', 'AXXXXX')
    return render_template('success.html', code=code)


# МАРШРУТ: Личный кабинет (Полностью статичная заглушка)
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    if not customer_code:
        customer_code = "Не зарегистрирован" # Для отображения

    # Статические данные для отображения
    mock_orders = [
        {
            'order_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'status': 'Пример (нет данных)',
            'items': [{"name": "Шоколад с клубникой", "qty": 1, "price": 1500}]
        },
    ]

    return render_template('profile.html',
                           code=customer_code,
                           customer_name="Ваш Клиент",
                           registration_date="Нет данных", 
                           orders=mock_orders)


# QR-вход (Устанавливает куки)
@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    return resp


if __name__ == '__main__':
    app.run(debug=True)