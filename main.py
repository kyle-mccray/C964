from _plotly_utils.utils import PlotlyJSONEncoder
from flask import Flask, session, redirect, url_for, request, render_template, flash
import plotly
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
import db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from joblib import load
import ml_main


app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = "supersecretkey123"
db = db_connection.Connection()


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if user_exists() == True:
            return redirect(url_for('homepage'))
        else:
            flash("Wrong Username or Password")
            print("wrong username or password")
    return render_template('login.html')


def user_exists():
    input_username = request.form['username']
    input_password = request.form['password']
    db.cur.execute(
        """
    select username, password from accounts where username = %s;
    """, [input_username, ]
    )
    result = db.cur.fetchone()
    if result is not None:
        if check_password_hash(result['password'], input_password) == True:
            print("User logged in")
            session['username'] = input_username
            return True
    return False


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/data')
def data():
    db.cur.execute(
        """
    select * from bike_data;
    """
    )
    result = db.cur.fetchall()

    col = ['Date', 'Rented Bike Count', 'Hour', 'Temperature(C)', 'Humidity(%)',
           'Wind speed (m/s)', 'Visibility (10m)', 'Dew point temperature(C)',
           'Solar Radiation (MJ/m2)', 'Rainfall(mm)', 'Snowfall (cm)', 'Seasons',
           'Holiday', 'Functioning Day']

    db_data = pd.DataFrame(data=result, columns=col)

    plots = create_plots(df=db_data)

    return render_template("data.html", plot=plots)


def create_plots(df):
    plots = []
    data = [
        go.Scatter(
            x=df['Date'],
            y=df['Rented Bike Count']
        )
    ]
    plots.append(json.dumps(data, cls=PlotlyJSONEncoder))

    data_2 = [
        go.Bar(
            x=df['Date'],
            y=df['Rented Bike Count']
        )
    ]

    plots.append(json.dumps(data_2, cls=PlotlyJSONEncoder))

    data_3 = [
        go.Histogram(
            x=df['Date'],
            y=df['Rented Bike Count']
        )
    ]

    plots.append(json.dumps(data_3, cls=PlotlyJSONEncoder))

    return plots


@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        hour = request.form['hourSelect']
        month = request.form['monthSelect']
        humidity = request.form['humidityID']
        temp = request.form['tempID']
        snow = request.form['snowID']
        rain = request.form['rainID']
        df = pd.DataFrame(None, columns=['hr_cos', 'hr_sin', 'month_cos', 'month_sin',
                                         'seasons_cos', 'seasons_sin', 'Temperature(C)', 'Humidity(%)',
                                         'Rainfall(mm)', 'Snowfall (cm)', 'Functioning Day'])

        if month in [12, 1, 2]:
            season = 0
        elif month in [3, 4, 5]:
            season = 1
        elif month in [6, 7, 8]:
            season = 2
        else:
            season = 3

        df = df.append({'seasons_cos': np.cos(season * (2 * np.pi / 4)),
                        'seasons_sin': np.sin(season * (2 * np.pi / 4)),
                        'hr_cos': np.cos(int(hour) * (2 * np.pi / 24)),
                        'hr_sin': np.sin(int(hour) * (2 * np.pi / 24)),
                        'month_cos': np.cos((int(month) - 1) * (2 * np.pi / 12)),
                        'month_sin': np.sin((int(month) - 1) * (2 * np.pi / 12)),
                        'Temperature(C)': temp,
                        'Humidity(%)': humidity,
                        'Rainfall(mm)': rain,
                        'Snowfall (cm)': snow,
                        'Functioning Day': 1
                        }, ignore_index=True)

        filename = 'final_model.joblib'
        try:
            pipe = load(open(filename, 'rb'))
            print(pipe.predict(df))

        except Exception:
            print("An error has occurred")
            print("Retraining Model this might take a bit")
            ml_main.main()


    return render_template('homepage.html')
