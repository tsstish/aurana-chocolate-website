import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response

app = Flask(__name__)
DATABASE = 'customers.db'

def get_db():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Добавляем маршрут для обработки главной страницы
@app.route('/')
def index():
    # 1. Получаем код клиента из куки (если есть)
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

    # Если код найден и имя сохранено, то is_registered будет True
    # name будет содержать имя или None
    
    # 3. Рендеринг шаблона с данными о клиенте
    return render_template('index.html', 
                           customer_code=customer_code,
                           name=name,
                           is_registered=is_registered)

# Маршрут для обработки регистрации имени
@app.route('/register', methods=['POST'])
def register():
    customer_code = request.cookies.get('customer_code')
    name = request.form.get('name')
    
    # 1. Проверка наличия кода и имени
    if not customer_code or not name:
        return redirect(url_for('index'))

    conn = get_db()
    
    # 2. Обновляем запись в базе данных: устанавливаем имя и флаг регистрации
    conn.execute(
        'UPDATE customers SET name = ?, registered = 1, registration_date = CURRENT_TIMESTAMP WHERE code = ?',
        (name, customer_code)
    )
    conn.commit()
    conn.close()
    
    # 3. Перенаправляем обратно на главную страницу (где уже будет видно имя и код)
    return redirect(url_for('index'))


# Маршрут для обработки сканирования QR-кода (установка куки)
@app.route('/qr/<customer_code>')
def qr_entry(customer_code):
    conn = get_db()
    
    # 1. Проверяем, существует ли такой код в базе
    exists = conn.execute('SELECT code FROM customers WHERE code = ?', (customer_code,)).fetchone()
    
    if exists:
        # 2. Если код существует, создаем ответ и устанавливаем куки
        resp = make_response(redirect(url_for('index')))
        # Куки действует 30 дней
        resp.set_cookie('customer_code', customer_code, max_age=30*24*60*60) 
        
        # Обновляем время первого посещения, если это первый раз
        conn.execute(
             'UPDATE customers SET first_visit = CURRENT_TIMESTAMP WHERE code = ? AND first_visit IS NULL', 
             (customer_code,)
        )
        conn.commit()
        conn.close()
        return resp
    else:
        conn.close()
        # 3. Если код недействителен, просто отправляем на главную
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Эта часть запускает Flask-приложение
    # При реальном развертывании на Vercel эта часть не используется, 
    # Vercel использует переменную 'app' напрямую.
    app.run(debug=True)