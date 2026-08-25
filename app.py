from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

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

@app.route('/logon', methods=["POST"])
def logon():
    email = request.form['email']
    pwd = request.form['pwd']

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_pwd, user_id FROM users WHERE user_email = ?', (email,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_password, user_id = result[0], result[1]
        if check_password_hash(stored_password, pwd):
            session['user_id'] = user_id
            session['user_email'] = email
            return redirect('/')
        
        else:
            error = "Incorrect Password!"

    else:
        error = 'User Does Not Exist!'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/list-job')
def list_job():
    if 'user_email' not in session:
        return redirect('/login')

    return render_template('list-job.html')

@app.route('/jobs')
def jobs():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = '''
        SELECT jobs.*, users.user_name, users.user_email 
        FROM jobs 
        JOIN users ON jobs.user_id = users.user_id 
        WHERE jobs.completed = "no"
    '''

    jobs = cursor.execute(query).fetchall()

    conn.close()

    return render_template('jobs.html', jobs=jobs)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
    app.run()

