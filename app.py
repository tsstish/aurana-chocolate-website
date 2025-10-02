from flask import Flask, render_template, request, redirect, url_for, make_response
import random
from datetime import datetime
import json

app = Flask(__name__)

# --- Вспомогательные функции ---

def get_products():
    return [
        {"id": "A01", "name": "Плитка молочного шоколада с сублимированной клубникой", "price": 1500},
        {"id": "A02", "name": "Плитка молочного шоколада с мороженным пломбир - крем-брюле", "price": 1600},
        {"id": "A03", "name": "Плитка молочного шоколада с манго", "price": 1500},
    ]

def generate_new_code():
    """Просто генерирует новый код клиента."""
    return f"A{random.randint(1000, 9999):04d}"

# --- Маршруты ---

@app.route('/')
def index():
    customer_code = request.cookies.get('customer_code')
    
    # Имя и статус регистрации теперь просто заглушки
    name = "Клиент" if customer_code else None
    is_registered = bool(customer_code)

    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered,
                           products=get_products())

# МАРШРУТ: Личный кабинет (Защищен от ошибок куки)
@app.route('/profile')
def profile():
    customer_code = request.cookies.get('customer_code')
    
    # Защита: Если куки нет, генерируем код для отображения
    if not customer_code:
        customer_code = generate_new_code() 
    
    # Данные для шаблона - статические заглушки
    mock_orders = [
        {
            'order_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'status': 'Образец (данные не сохранены)',
            'items': [{"name": "Шоколад с клубникой", "qty": 1, "price": 1500}]
        },
    ]

    return render_template('profile.html',
                           code=customer_code,
                           customer_name="Ваш Клиент",
                           registration_date="Нет данных о регистрации",
                           orders=mock_orders)


# QR-вход (Устанавливает куки и перенаправляет на главную)
@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    resp = make_response(redirect(url_for('index')))
    # Устанавливаем куки на 30 дней
    resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
    return resp


if __name__ == '__main__':
    app.run(debug=True)