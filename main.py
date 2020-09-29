import os
from _plotly_utils.utils import PlotlyJSONEncoder
from flask import Flask, redirect, url_for, request, render_template, flash, abort
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
from flask_login import LoginManager, login_required, current_user, logout_user, UserMixin, login_user
from werkzeug.security import check_password_hash
from joblib import load
from flask_sqlalchemy import SQLAlchemy
import ml_main

app = Flask(__name__, template_folder='templates')

if __name__ == "__main__":
    app.run()

app.secret_key = "hzxcv,mndskljhxcvqwe13"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# DATABASE_URL = os.environ['DATABASE_URL']
local = 'postgresql+psycopg2://server:admin@localhost:5432/flask'
app.config['SQLALCHEMY_DATABASE_URI'] = local

db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = 'accounts'
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(200))

    def get_id(self):
        return self.username

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login?next=' + request.path)


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None




@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']
        user = User.query.filter_by(username=input_username).first()
        if user:
            if check_password_hash(user.password, input_password):
                print("Logging in")
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))

            flash("Wrong Username or Password")
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    print("User logged out")
    logout_user()
    return redirect(url_for('login'))


@app.route('/data')
@login_required
def data():
    result = db.engine.execute("select * from bike_data;")
    col = ['Date', 'Rented Bike Count', 'Hour', 'Temperature(C)', 'Humidity(%)',
           'Wind speed (m/s)', 'Visibility (10m)', 'Dew point temperature(C)',
           'Solar Radiation (MJ/m2)', 'Rainfall(mm)', 'Snowfall (cm)', 'Seasons',
           'Holiday', 'Functioning Day']

    db_data = pd.DataFrame(data=result, columns=col)
    plots = create_plots(df=db_data)
    return render_template('data.html', plot=plots)


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


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
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

        except FileNotFoundError:
            print("An error has occurred")
            print("Retraining Model this might take a bit")
            ml_main.main()

    return render_template('home.html')
