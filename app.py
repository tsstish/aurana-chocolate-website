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
    return f"A{random.randint(1000, 9999):04d}"

# --- Маршруты ---

@app.route('/')
def index():
    # Куки больше не используем. Код генерируем для отображения в форме.
    customer_code = generate_new_code()
    
    return render_template('index.html', 
                           customer_code=customer_code,
                           products=get_products())

# МАРШРУТ: Личный кабинет (БЕЗОПАСНАЯ ВЕРСИЯ)
@app.route('/profile')
def profile():
    # НЕ ПЕРЕДАЕМ НИ ОДНОЙ ПЕРЕМЕННОЙ
    return render_template('profile.html')


# QR-вход (Просто перенаправляет)
@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)