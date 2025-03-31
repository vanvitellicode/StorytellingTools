from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, GridSearchCV, RepeatedKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

from sklearn.svm import SVR

import numpy as np


class Positioning:
    def __init__(self, model_type='knn', optimize=False, **kwargs):
        self.optimize = optimize
        self.model_type = model_type

        # Seleziona i modelli di base per x e y
        if model_type == 'knn':
            self.model_x = KNeighborsRegressor(n_neighbors=kwargs.get('n_neighbors', 5))
            self.model_y = KNeighborsRegressor(n_neighbors=kwargs.get('n_neighbors', 5))
        elif model_type == 'svr':
            self.model_x = SVR(**kwargs)
            self.model_y = SVR(**kwargs)
        elif model_type == 'rf':
            self.model_x = RandomForestRegressor(**kwargs)
            self.model_y = RandomForestRegressor(random_state=kwargs.get(' random_state', 42))
        else:
            raise ValueError(f"Modello {model_type} non supportato.")

###############################################################################################################################
    def optimize_model(self, X_train, y_train):
        """
        Ottimizza i modelli base usando GridSearchCV.
        """
        param_grid = {}

        k_fold_method = RepeatedKFold(n_splits=6,
                                      n_repeats=3,
                                      random_state=8)
        if self.model_type == 'knn':

            leaf_size = list(range(1, 50))
            param_grid = {
                'n_neighbors': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30, 35],
                'weights': ['uniform', 'distance'],
                'p': [1, 2, 5]  # Parametro per la distanza: manhattan (p=1), euclidean (p=2)
            }
        elif self.model_type == 'svr':
            param_grid = {
                'C': [0.1, 1, 10, 100, 1000],
                'gamma': [1, 0.1, 0.01, 0.001, 0.0001],
                'kernel': ['rbf']
            }
        elif self.model_type == 'rf':
            param_grid = {
                'n_estimators': [10, 20, 50, 100, 150, 200],
                'max_depth': [None, 10, 20, 30, 40, 50, 100, 120, 200],
            }

        # Ottimizzazione per il modello x
        grid_search_x = GridSearchCV(self.model_x, param_grid, cv=k_fold_method, scoring='r2')
        grid_search_x.fit(X_train, y_train[:, 0])
        print(f"Best parameters for x model: {grid_search_x.best_params_}")
        self.model_x = grid_search_x.best_estimator_

        # Ottimizzazione per il modello y
        grid_search_y = GridSearchCV(self.model_y, param_grid, cv=k_fold_method, scoring='r2')
        grid_search_y.fit(X_train, y_train[:, 1])
        print(f"Best parameters for y model: {grid_search_y.best_params_}")
        self.model_y = grid_search_y.best_estimator_

    def predict(self, observed_rss_values):
        observed_rss_values = np.array(observed_rss_values)

        # Predizioni per x e y usando modelli separati
        x_predictions = self.model_x.predict(observed_rss_values)
        y_predictions = self.model_y.predict(observed_rss_values)

        # Combina le predizioni
        combined_predictions = np.column_stack((x_predictions, y_predictions))  # coordinata x,y

        return combined_predictions

###############################################################################################################################
    def train(self, rps, scaler=None):
        X_train = []
        y_train = []

        for rp in rps:
            X_train.append(rp.readings)  # rssi
            y_train.append(rp.coordinates)  # x e y

        X_train = np.array(X_train)
        y_train = np.array(y_train)

        # Verifica la forma di y_train
        if y_train.ndim == 1:
            y_train = np.column_stack((y_train, y_train))  # Solo se hai una sola dimensione

        # Suddivisione in train/test
        X_train_split, X_test_split, y_train_split, y_test_split = train_test_split(
            X_train, y_train, test_size=0.1, random_state=42)

        if self.optimize:
            self.optimize_model(X_train_split, y_train_split)

        # Addestra i modelli
        self.model_x.fit(X_train_split, y_train_split[:, 0])  # x
        self.model_y.fit(X_train_split, y_train_split[:, 1])  # y
        ###############################################################################################################################
        # Valutazione
        print("Performance su test:")
        evaluate_model(self.model_x, X_train_split, y_train_split[:, 0], X_test_split, y_test_split[:, 0])
        evaluate_model(self.model_y, X_train_split, y_train_split[:, 1], X_test_split, y_test_split[:, 1])


def evaluate_model(model, X_train, y_train, X_test, y_test):
    """
    Valuta le performance del modello sui dati di training e test.
    """
    y_pred_train = model.predict(X_train)
    mse_train = mean_squared_error(y_train, y_pred_train)
    r2_train = r2_score(y_train, y_pred_train)

    print(f"Performance sul training set:\n"
          f"MSE: {mse_train}, R²: {r2_train}\n")

    y_pred_test = model.predict(X_test)
    mse_test = mean_squared_error(y_test, y_pred_test)
    r2_test = r2_score(y_test, y_pred_test)

    print(f"Performance sul test set:\n"
          f"MSE: {mse_test}, R²: {r2_test}\n")
