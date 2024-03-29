import os
from math import ceil

import sqlalchemy
from _plotly_utils.utils import PlotlyJSONEncoder
from flask import Flask, redirect, url_for, request, render_template, flash, jsonify
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json
from flask_login import LoginManager, login_required, logout_user, UserMixin, login_user
from psycopg2 import sql
from sqlalchemy import text, bindparam, literal_column, column, select
from werkzeug.security import check_password_hash
from joblib import load
from flask_sqlalchemy import SQLAlchemy
import ml_main

app = Flask(__name__, template_folder='templates')

if __name__ == "__main__":
    app.run()

app.secret_key = '\xaeH\x041\xa3\x99.\xa3<uC\xfa`\x00\r\x9d>f-\xef\x1f\xed\xc9\x93'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
DATABASE_URL = os.environ['DATABASE_URL']
#local = 'postgresql+psycopg2://server:admin@localhost:5432/flask'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


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
                login_user(user)
                app.logger.info(" %s logged in", user.username)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
            flash("Wrong Username or Password")  # user was found password was wrong
        flash("Wrong Username or Password")  # user was not found
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    app.logger.info("User Logged Out", )
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
    return render_template('data.html', plots=plots)


def create_plots(df):
    df[['Day', 'Month', 'Year']] = df['Date'].str.split('/', expand=True)
    result = db.engine.execute(
        "select split_part(date_recorded, '/', 1) as day, split_part(date_recorded, '/', 2) as month,"
        "split_part(date_recorded, '/', 3) as year, avg(temperature) as t, sum(rented_bikes) as "
        "count from bike_data group by 1,2,3 order by 3, 2, 1;")
    date = []
    count = []
    temp = []
    for x in result:
        date.append(str(x['day']) + "/" + str(x['month']) + "/" + str(x['year']))
        count.append(x['count'])
        temp.append(ceil(x['t']))
    scatter_df = pd.DataFrame()
    scatter_df['Date'] = date
    scatter_df['Bike Count'] = count
    scatter_df['temp'] = temp
    plots = []
    data = [
        go.Scatter(x=scatter_df['Date'],
                   y=scatter_df['Bike Count'],
                   mode="markers",
                   marker=dict(color='#838df9')

                   )

    ]
    plots.append(json.dumps(data, cls=PlotlyJSONEncoder))

    data_2 = [
        go.Bar(
            y=scatter_df['temp'],
            x=scatter_df['Bike Count'],
            orientation='h',
            marker=dict(color='#ec7a69')

        )
    ]

    plots.append(json.dumps(data_2, cls=PlotlyJSONEncoder))

    data_3 = [
        go.Histogram(
            y=df['Rented Bike Count'],
            marker=dict(color='#636efa')

        )
    ]

    plots.append(json.dumps(data_3, cls=PlotlyJSONEncoder))

    data_4 = [
        go.Histogram2d(
            x=df['Humidity(%)'],
            y=df['Temperature(C)'],
            z=df['Rented Bike Count'],
            histfunc="avg"

        )
    ]

    plots.append(json.dumps(data_4, cls=PlotlyJSONEncoder))

    return plots


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    return render_template('home.html')


@app.route('/process', methods=['POST'])
@login_required
def process():
    hour = request.form['hour']
    month = request.form['month']
    day = request.form['day']
    humidity = request.form['humidity']
    temp = request.form['temp']
    snow = request.form['snow']
    rain = request.form['rain']
    df = pd.DataFrame(None, columns=['hr_cos', 'hr_sin', 'month_cos', 'month_sin', 'days_cos', 'days_sin',
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
                    'days_cos': np.cos(int(day) * (2 * np.pi / 31)),
                    'days_sin': np.sin(int(day) * (2 * np.pi / 31)),
                    'Temperature(C)': temp,
                    'Humidity(%)': humidity,
                    'Rainfall(mm)': rain,
                    'Snowfall (cm)': snow,
                    'Functioning Day': 1
                    }, ignore_index=True)

    filename = 'model.joblib'
    try:
        pipe = load(open(filename, 'rb'))
        result = pipe.predict(df)
        int_result = int(result)
        str_result = str(ceil(int_result))
        app.logger.info("Bikes Needed: {}".format(result))
        resp = {'result': str_result}
        return jsonify(resp)

    except FileNotFoundError:
        app.logger.error("Model could not be found retraining model")
        resp = {'error': "An Error Has Occurred Retraining Model This Might Take a Bit"}
        ml_main.main()
        return jsonify(resp)


@app.route('/fetch', methods=['GET'])
@login_required
def fetch():
    r = request.args
    offset = r.get(key='offset')
    limit = r.get(key='limit')
    sort = r.get(key='sort')
    order = r.get(key='order')
    row_count = db.engine.execute('select count(*) from bike_data;').fetchone()
    key = sort + "_" + order
    queries = {
        "date_recorded_asc": "select * from bike_data order by date_recorded asc",
        "date_recorded_desc": "select * from bike_data order by date_recorded desc",
        "rented_bikes_asc": "select * from bike_data order by rented_bikes asc",
        "rented_bikes_desc": "select * from bike_data order by rented_bikes desc",
        "hour_recored_asc": "select * from bike_data order by hour_recored asc",
        "hour_recored_desc": "select * from bike_data order by hour_recored desc",
        "temperature_asc": "select * from bike_data order by temperature asc",
        "temperature_desc": "select * from bike_data order by temperature desc",
        "humidity_asc": "select * from bike_data order by humidity asc",
        "humidity_desc": "select * from bike_data order by humidity desc",
        "wind_speed_asc": "select * from bike_data order by wind_speed asc",
        "wind_speed_desc": "select * from bike_data order by wind_speed desc",
        "visibility_asc": "select * from bike_data order by visibility asc",
        "visibility_desc": "select * from bike_data order by visibility desc",
        "dewpoint_asc": "select * from bike_data order by dewpoint asc",
        "dewpoint_desc": "select * from bike_data order by dewpoint desc",
        "solar_radiation_asc": "select * from bike_data order by solar_radiation asc",
        "solar_radiation_desc": "select * from bike_data order by solar_radiation desc",
        "rainfall_asc": "select * from bike_data order by rainfall asc",
        "rainfall_desc": "select * from bike_data order by rainfall desc",
        "snowfall_asc": "select * from bike_data order by snowfall asc",
        "snowfall_desc": "select * from bike_data order by snowfall desc",
        "seasons_asc": "select * from bike_data order by seasons asc",
        "seasons_desc": "select * from bike_data order by seasons desc",
        "holiday_asc": "select * from bike_data order by holiday asc",
        "holiday_desc": "select * from bike_data order by holiday desc",
        "functioning_day_asc": "select * from bike_data order by functioning_day asc",
        "functioning_day_desc": "select * from bike_data order by functioning_day desc",
    }
    if order and sort:
        statement = queries[key]
        statement = text(statement + " offset :x rows fetch next :y rows only")
        raw_result = db.engine.execute(statement, x=int(offset), y=int(limit)).fetchall()
        # statement = text("""select * from bike_data offset :x rows fetch next :y rows only""")
        # raw_result = db.engine.execute(statement, x=offset, y=limit).fetchall()
        result = {'total': int(*row_count), 'rows': [dict(row) for row in raw_result]}
        return jsonify(result)

    statement = text("""select * from bike_data offset :x rows fetch next :y rows only""")
    raw_result = db.engine.execute(statement, x=offset, y=limit).fetchall()
    result = {'total': int(*row_count), 'rows': [dict(row) for row in raw_result]}
    return jsonify(result)
