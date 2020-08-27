from flask import Flask, session, redirect, url_for, request, render_template
from markupsafe import escape

app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'\xb4\xf7\xba\x0ed\x97TJ0\xf4\xe6m\xc5m\x9f\xc5'

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("Username: " + request.form['username'])
        print("Password: " + request.form['password'])
        return redirect(url_for('homepage'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/data')
def data():
    return render_template("data.html")


@app.route('/homepage')
def homepage():
    return render_template('homepage.html')
