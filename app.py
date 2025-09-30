# Файл: app.py
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import qrcode
from io import BytesIO
import base64

# Создаем наше приложение Flask
app = Flask(__name__)
# Указываем, где лежат шаблоны страниц (index.html)
app.template_folder = 'templates'

# 1. Функция для подключения к базе данных
def get_db_connection():
    # Подключаемся к файлу customers.db
    conn = sqlite3.connect('customers.db')
    # Это позволяет обращаться к столбцам по их именам (например, customer['customer_name'])
    conn.row_factory = sqlite3.Row
    return conn

# 2. Функция для создания QR-кода в виде картинки (для клубной карты)
def generate_qr_code(data):
    # Создаем QR-код с данными
    img = qrcode.make(data)
    
    # Сохраняем QR-код во временную область памяти
    buffered = BytesIO()
    # Указываем формат PNG, который поддерживает PIL/Pillow
    img.save(buffered, format="PNG")
    
    # Преобразуем картинку в текст (Base64), чтобы показать на сайте без сохранения файла
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

# 3. Главная страница (маршрут)
# Обрабатывает: / (общий вход) и /секретный_код (персонализированный вход)
@app.route('/')
@app.route('/<secret_code>')
def index(secret_code=None):
    customer_info = None
    qr_img = None
    page_title = "Элитный шоколад ручной работы" # SEO-заголовок по умолчанию
    
    # --- Логика персонализации ---
    if secret_code:
        conn = get_db_connection()
        # Ищем клиента по уникальному секретному коду
        customer = conn.execute(
            'SELECT * FROM customers WHERE qr_code_secret = ?', (secret_code,)
        ).fetchone()
        conn.close()
        
        if customer:
            # Клиент найден! Заполняем информацию для страницы
            customer_info = dict(customer)
            # Меняем заголовок на персонализированный
            page_title = f"С возвращением, {customer_info['customer_name'] or 'дорогой гость'}!"
            
        else:
            # Код не найден, перенаправляем на обычную главную страницу
            return redirect(url_for('index'))
            
        # Генерируем QR-код для клубной карты (даже если имя не введено)
        # Это тестовая заглушка, реальный сервис для Wallet настраивается отдельно
        wallet_link = f"https://wallet.example.com/add?id={secret_code}" 
        qr_img = generate_qr_code(wallet_link)
    
    # Отправляем информацию нашему HTML-шаблону index.html
    return render_template('index.html', 
                           customer=customer_info,
                           qr_img=qr_img,
                           page_title=page_title)

# Добавляем маршрут для первого входа (обновление имени)
@app.route('/register/<secret_code>', methods=['POST'])
def register_customer(secret_code):
    new_name = request.form.get('customer_name')
    if new_name and secret_code:
        conn = get_db_connection()
        # Обновляем имя клиента в базе данных по секретному коду
        conn.execute(
            'UPDATE customers SET customer_name = ? WHERE qr_code_secret = ?', 
            (new_name, secret_code)
        )
        conn.commit()
        conn.close()
    
    # Перенаправляем клиента обратно на его персонализированную страницу
    return redirect(url_for('index', secret_code=secret_code))

# Для локального тестирования (удалить при публикации на Vercel!)
if __name__ == '__main__':
    app.run(debug=True)