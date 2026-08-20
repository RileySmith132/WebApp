from flask import Flask, render_template, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

@app.route('/')
def root():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=["POST"])
def signup():
    name = request.form['name']
    email = request.form['email']
    pwd = request.form['pwd2']
    hashed_pwd = generate_password_hash(pwd)

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO users (user_name, user_email, user_pwd) VALUES (?, ?, ?)',
        (name, email, hashed_pwd)
    )

    conn.commit()
    conn.close()

    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
    app.run()

