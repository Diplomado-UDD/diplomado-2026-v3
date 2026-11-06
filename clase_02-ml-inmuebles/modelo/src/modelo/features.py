"""Lógica: compara formas de usar la ubicación. No modifica el modelo final."""

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans
from sklearn.compose import TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import make_scorer, mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import FEATURES

# (nombre, columnas que ve el modelo, k de la zona; 0 = sin zona)
VARIANTES = (
    ("base", FEATURES, 0),
    ("sin_lat", ["dormitorios", "banos", "superficie_m2", "lon"], 0),
    ("sin_lon", ["dormitorios", "banos", "superficie_m2", "lat"], 0),
    ("sin_coordenadas", ["dormitorios", "banos", "superficie_m2"], 0),
    ("zona", FEATURES, 6),
    ("solo_zona", ["dormitorios", "banos", "superficie_m2"], 6),
)


class _Matriz(BaseEstimator, TransformerMixin):
    """Columnas del modelo y, si k > 0, la zona en variables indicadoras.

    La zona se ajusta solo con las filas de entrenamiento que recibe.
    """

    def __init__(self, columnas, k=0):
        self.columnas = columnas
        self.k = k

    def fit(self, X, y=None):
        X = _frame(X)
        self.feature_names_in_ = np.asarray(FEATURES, dtype=object)
        if self.k:
            xy = X[["lat", "lon"]].to_numpy(dtype=float)
            self.scaler_ = StandardScaler().fit(xy)
            self.km_ = KMeans(n_clusters=self.k, n_init=10, random_state=42)
            self.km_.fit(self.scaler_.transform(xy))
        return self

    def transform(self, X):
        X = _frame(X)
        base = X[list(self.columnas)].to_numpy(dtype=float)
        if not self.k:
            return base
        etiquetas = self.km_.predict(
            self.scaler_.transform(X[["lat", "lon"]].to_numpy(dtype=float))
        )
        return np.column_stack([base, np.eye(self.k)[etiquetas]])


def _frame(X) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        return X
    return pd.DataFrame(X, columns=FEATURES)


def zonas(X: pd.DataFrame, k: int = 6) -> np.ndarray:
    """Etiqueta de KMeans sobre latitud y longitud escaladas."""
    xy = StandardScaler().fit_transform(X[["lat", "lon"]].to_numpy(dtype=float))
    return KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(xy)


def _estimador(columnas, k, iterations, seed):
    pipe = Pipeline(
        [
            ("matriz", _Matriz(columnas=columnas, k=k)),
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "model",
                CatBoostRegressor(
                    iterations=iterations,
                    learning_rate=0.06,
                    depth=6,
                    loss_function="RMSE",
                    random_seed=seed,
                    verbose=0,
                    thread_count=1,
                    allow_writing_files=False,
                ),
            ),
        ]
    )
    return TransformedTargetRegressor(pipe, func=np.log, inverse_func=np.exp)


def comparar(X, y, groups, folds=5, iterations=400, seed=42, n_jobs=-1) -> pd.DataFrame:
    """MAE de un CatBoost fijo según cómo entra la ubicación.

    Los hiperparámetros no se ajustan: la tabla compara variantes, no estima
    el error del modelo final. La zona se reajusta en cada pliegue.
    """
    cv = GroupKFold(folds, shuffle=True, random_state=seed)
    scoring = {
        "mae": make_scorer(mean_absolute_error, greater_is_better=False),
        "mape": make_scorer(mean_absolute_percentage_error, greater_is_better=False),
    }
    filas = []
    for nombre, columnas, k in VARIANTES:
        r = cross_validate(
            _estimador(columnas, k, iterations, seed),
            X,
            y,
            groups=groups,
            cv=cv,
            scoring=scoring,
            n_jobs=n_jobs,
        )
        mae = -r["test_mae"]
        filas.append(
            {
                "variante": nombre,
                "mae": mae.mean(),
                "mae_std": mae.std(ddof=1),
                "mape": (-r["test_mape"]).mean(),
            }
        )
    tabla = pd.DataFrame(filas)
    base = tabla.loc[tabla.variante == "base", "mae"].item()
    tabla["delta_mae"] = tabla["mae"] - base
    return tabla
