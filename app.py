import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, g, send_file
import datetime
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import joblib
import sqlite3
from tensorflow.keras.models import load_model
from flask import send_file, request
import tempfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'
LOG_DB = 'logs/access.db'

MODEL_PATH = 'model/ai_ids_model.h5'
model = load_model(MODEL_PATH)
enc_ip = joblib.load('model/ip_encoder.pkl')
enc_method = joblib.load('model/method_encoder.pkl')
enc_path = joblib.load('model/path_encoder.pkl')

# Dummy user db
users = {"admin": "admin123", "user": "user123"}

# -- SQLite Logging Setup --
def get_db():
    if 'db' not in g:
        os.makedirs('logs', exist_ok=True)
        g.db = sqlite3.connect(LOG_DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Create table if not exists
with app.app_context():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    ip TEXT,
                    method TEXT,
                    path TEXT
                )''')
    db.commit()

# -- In-memory IP throttling tracker --
last_access = {}

# -- Log Request --
def log_request(path):
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'bot' in user_agent:
        return  # Bỏ qua bot

    ip = request.remote_addr
    now = datetime.datetime.now()

    # Giới hạn mỗi IP chỉ ghi log 1 lần mỗi 5 giây
    if ip in last_access and (now - last_access[ip]).total_seconds() < 5:
        return
    last_access[ip] = now

    method = request.method
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    db.execute('INSERT INTO logs (timestamp, ip, method, path) VALUES (?, ?, ?, ?)',
               (timestamp, ip, method, path))
    db.commit()

# -- Parse Log from SQLite --
def parse_log():
    db = get_db()
    rows = db.execute('SELECT timestamp, ip, method, path FROM logs').fetchall()
    data = [dict(row) for row in rows]
    return pd.DataFrame(data)

@app.route('/')
def home():
    log_request('/home')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    log_request('/login')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('success', page='login'))
        else:
            return "Login Failed! Try again."
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    log_request('/signup')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username not in users:
            users[username] = password
            return redirect(url_for('success', page='signup'))
        else:
            return "User already exists!"
    return render_template('signup.html')

@app.route('/logout')
def logout():
    log_request('/logout')
    session.pop('username', None)
    return redirect(url_for('success', page='logout'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    log_request('/search')
    results = []
    if request.method == 'POST':
        query = request.form.get('query')
        results = [f"Kết quả giả cho '{query}' - item {i}" for i in range(1, 6)]
        return render_template('search.html', results=results, query=query)
    return render_template('search.html', results=results)

@app.route('/admin')
def admin():
    log_request('/admin')
    username = session.get('username')
    if username != 'admin':
        return "Access Denied! Only admin allowed."

    df = parse_log()
    if df.empty:
        return render_template('admin.html', total_requests=0, chart_url='', log_table='<p>No data</p>')

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    total_requests = len(df)
    requests_by_method = df['method'].value_counts()

    ai_predictions = []
    for _, row in df.iterrows():
        try:
            ip = enc_ip.transform([row['ip']])[0]
            method = enc_method.transform([row['method']])[0]
            path = enc_path.transform([row['path']])[0]
            input_data = np.array([[ip, method, path]])
            prediction = model.predict(input_data)[0][0]
            label = '❌ Bất thường' if prediction > 0.5 else '✅ Bình thường'
        except Exception as e:
            print(f"Error in AI prediction for row {row.name}: {e}")
            label = '⚠ Không xác định'
        ai_predictions.append(label)

    df['AI_Phân_Tích'] = ai_predictions

    # Vẽ biểu đồ
    plt.figure(figsize=(5, 3))
    requests_by_method.plot(kind='bar', color='skyblue')
    plt.title('Requests by Method')
    plt.ylabel('Count')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    columns = ['timestamp', 'ip', 'method', 'path', 'AI_Phân_Tích']
    log_table_html = df.tail(10)[columns].to_html(classes='log-table', index=False)

    return render_template('admin.html',
                           total_requests=total_requests,
                           chart_url=chart_url,
                           log_table=log_table_html)

@app.route('/export/logs')
def export_logs():
    df = parse_log()
    if df.empty:
        return "Không có dữ liệu để xuất."

    filetype = request.args.get('filetype', 'csv').lower()
    # Tạo file tạm để lưu xuất
    if filetype == 'excel':
        tmpfile = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(tmpfile.name, index=False)
        tmpfile.close()
        return send_file(tmpfile.name, as_attachment=True, download_name='logs.xlsx')
    else:
        # mặc định csv
        tmpfile = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        df.to_csv(tmpfile.name, index=False)
        tmpfile.close()
        return send_file(tmpfile.name, as_attachment=True, download_name='logs.csv')

if __name__ == '__main__':
    app.run(debug=True)
