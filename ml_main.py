from sklearn.neural_network import MLPRegressor
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import explained_variance_score
from sklearn.metrics import max_error
from sklearn.metrics import r2_score
from sklearn.metrics import median_absolute_error
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from joblib import dump, load
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA


def main():
    df = pd.read_csv("SeoulBikeData.csv")
    print(df.columns)
    df.insert(0, 'hr_cos', '-1')
    df.insert(1, 'hr_sin', '-1')
    df.insert(3, 'month_cos', '-1')
    df.insert(4, 'month_sin', '-1')
    df.insert(5, 'seasons_sin', '-1')
    df.insert(6, 'seasons_cos', '-1')
    df.insert(7, 'days_sin', '-1')
    df.insert(8, 'days_cos', '-1')

    df[['Day', 'Month', 'Year']] = df['Date'].str.split('/', expand=True)

    df['hr_cos'] = np.cos(df['Hour'] * (2 * np.pi / 24))
    df['hr_sin'] = np.sin(df['Hour'] * (2 * np.pi / 24))
    df['Month'] = df['Month'].astype(int)

    df['month_cos'] = np.cos((df['Month'] - 1) * (2 * np.pi / 12))
    df['month_sin'] = np.sin((df['Month'] - 1) * (2 * np.pi / 12))

    df['Functioning Day'] = df['Functioning Day'].replace({'Yes': 1, 'No': 0})
    df['Holiday'] = df['Holiday'].replace({'Holiday': 1, 'No Holiday': 0})
    df['Seasons'] = df['Seasons'].replace({'Winter': 0, 'Spring': 1, 'Summer': 2, 'Autumn': 3})

    df['seasons_cos'] = np.cos((df['Seasons']) * (2 * np.pi / 4))
    df['seasons_sin'] = np.sin((df['Seasons']) * (2 * np.pi / 4))

    df['Day'] = df['Day'].astype(int)
    df['days_cos'] = np.cos((df['Day']) * (2 * np.pi / 30))
    df['days_sin'] = np.sin((df['Day']) * (2 * np.pi / 30))

    categories = ['hr_cos', 'hr_sin', 'month_cos', 'month_sin',
                  'seasons_cos', 'seasons_sin', 'Temperature(C)', 'Humidity(%)',
                  'Rainfall(mm)', 'Snowfall (cm)', 'Functioning Day']

    RANDOM_STATE = 2020

    target = ['Rented Bike Count']
    pd.set_option('display.max_columns', None)
    X = df[categories]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=RANDOM_STATE)

    filename = 'final_model.joblib'

    try:
        pipe = load(open(filename, 'rb'))

    except Exception:
        print("An error has occurred")
        pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components='mle', random_state=RANDOM_STATE)),
                         ('mlp', MLPRegressor(hidden_layer_sizes=(100, 100, 100, 100, 100, 100, 100),
                                              verbose=True, shuffle=True,
                                              random_state=RANDOM_STATE,
                                              solver='adam', activation='relu',
                                              max_iter=20000, early_stopping=True))])

        pipe.fit(X_train, y_train.values.ravel())

        dump(pipe, open(filename, 'wb'))

    print(" ")
    print('Accuracy testing : {:.3f}'.format(pipe.score(X_test, y_test)))

    expected_y = y_test
    predicted_y = pipe.predict(X_test)

    print(explained_variance_score(expected_y, predicted_y))
    print(max_error(expected_y, predicted_y))
    print(r2_score(expected_y, predicted_y))
    print(median_absolute_error(expected_y, predicted_y))
    print(mean_absolute_error(expected_y, predicted_y))
    print(mean_squared_error(expected_y, predicted_y))




main()
