from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

LOG_FILE = 'logs/access.log'

# Dummy user db
users = {"admin": "admin123", "user": "user123"}

def log_request(path):
    ip = request.remote_addr
    method = request.method
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{time} {ip} {method} {path}\n"
    os.makedirs('logs', exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line)

@app.route('/')
def home():
    log_request('/')
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
        # Demo kết quả tìm kiếm giả
        results = [f"Kết quả giả cho '{query}' - item {i}" for i in range(1, 6)]
        return render_template('search.html', results=results, query=query)
    return render_template('search.html', results=results)

@app.route('/admin')
def admin():
    log_request('/admin')
    username = session.get('username')
    if username != 'admin':
        return "Access Denied! Only admin allowed."
    return render_template('admin.html')

@app.route('/success/<page>')
def success(page):
    log_request(f'/success/{page}')
    return render_template('success.html', page=page)

if __name__ == '__main__':
    app.run(debug=True)
