from flask import Flask, render_template

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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
    app.run()

