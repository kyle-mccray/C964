from flask import Flask, session, redirect, url_for, request, render_template
import plotly
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
import db_connection


app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = "supersecretkey123"
db = db_connection.Con()
login_manager = LoginManager()

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if user_exists():
            return redirect(url_for('homepage'))
        else:
            print("wrong username or password")
    return render_template('login.html')


def user_exists():
    input_username = request.form['username']
    input_password = request.form['password']
    db.cur.execute(
        """
    select * from accounts where username = %s and password = %s;
    """, [input_username, input_password])
    result = db.cur.fetchone()
    if result is not None:
        print("User logged in")
        session['username'] = input_username
        return True
    else:
        return False


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/data')
def data():
    z = []
    for x in range(0, 3):
        bar = create_plots()
        z.append(bar)

    return render_template("data.html", plot=z)


def create_plots():
    N = 40
    x = np.linspace(0, 1, N)
    y = np.random.randn(N)
    df = pd.DataFrame({'x': x, 'y': y})  # creating a sample dataframe
    data = [
        go.Bar(
            x=df['x'],  # assign x as the dataframe column 'x'
            y=df['y']
        )
    ]
    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


@app.route('/homepage')
def homepage():
    return render_template('homepage.html')
