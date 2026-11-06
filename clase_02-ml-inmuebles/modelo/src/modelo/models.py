"""Lógica: catálogo de regresores y espacios de búsqueda de hiperparámetros."""

import numpy as np
from catboost import CatBoostRegressor
from scipy.stats import loguniform, randint, uniform
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

# Cada modelo usa 1 hilo: el paralelismo lo da la búsqueda de hiperparámetros.
CATALOG = {
    "dummy": (lambda s: DummyRegressor(strategy="median"), {}),
    "ridge": (lambda s: Ridge(), {"alpha": loguniform(1e-3, 1e3)}),
    "knn": (
        lambda s: KNeighborsRegressor(),
        {"n_neighbors": randint(3, 40), "weights": ["uniform", "distance"]},
    ),
    "random_forest": (
        lambda s: RandomForestRegressor(random_state=s, n_jobs=1),
        {
            "n_estimators": randint(200, 600),
            "max_depth": [None, 8, 16],
            "min_samples_leaf": randint(1, 10),
            "max_features": [0.5, 0.8, 1.0],
        },
    ),
    "hist_gb": (
        lambda s: HistGradientBoostingRegressor(random_state=s),
        {
            "learning_rate": loguniform(0.01, 0.3),
            "max_leaf_nodes": randint(8, 64),
            "min_samples_leaf": randint(5, 50),
            "l2_regularization": loguniform(1e-3, 10),
        },
    ),
    "xgboost": (
        lambda s: XGBRegressor(random_state=s, n_jobs=1, tree_method="hist"),
        {
            "n_estimators": randint(200, 800),
            "learning_rate": loguniform(0.01, 0.3),
            "max_depth": randint(2, 8),
            "subsample": uniform(0.6, 0.4),
            "colsample_bytree": uniform(0.6, 0.4),
            "min_child_weight": randint(1, 10),
        },
    ),
    "catboost": (
        lambda s: CatBoostRegressor(
            random_seed=s, verbose=0, thread_count=1, allow_writing_files=False
        ),
        {
            "iterations": randint(300, 1000),
            "learning_rate": loguniform(0.01, 0.3),
            "depth": randint(4, 8),
            "l2_leaf_reg": loguniform(1, 10),
        },
    ),
}


def build(name: str, seed: int = 42) -> tuple[TransformedTargetRegressor, dict]:
    """Pipeline (imputación, escala, modelo) que aprende log(precio) y predice precio.

    El logaritmo corrige la cola larga del precio: el error pasa a ser relativo.
    """
    make, params = CATALOG[name]
    pipe = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", make(seed)),
        ]
    )
    model = TransformedTargetRegressor(pipe, func=np.log, inverse_func=np.exp)
    return model, {f"regressor__model__{k}": v for k, v in params.items()}
