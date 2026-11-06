"""Lógica: partición, validación cruzada anidada y métricas."""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import (
    GroupKFold,
    GroupShuffleSplit,
    RandomizedSearchCV,
    cross_validate,
)

from .models import CATALOG, build

SCORING = {
    "mae": "neg_mean_absolute_error",
    "rmse": "neg_root_mean_squared_error",
    "mape": "neg_mean_absolute_percentage_error",
    "r2": "r2",
}


def split(X, y, groups, test_size=0.2, seed=42):
    """Holdout por grupos: un edificio queda entero en train o en test."""
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    tr, te = next(gss.split(X, y, groups))
    return X.iloc[tr], X.iloc[te], y.iloc[tr], y.iloc[te], groups.iloc[tr]


def tuned(name: str, n_iter=20, inner=3, seed=42):
    """Modelo con búsqueda aleatoria de hiperparámetros (lazo interno)."""
    model, params = build(name, seed)
    if not params:
        return model
    return RandomizedSearchCV(
        model,
        params,
        n_iter=n_iter,
        cv=GroupKFold(inner, shuffle=True, random_state=seed),
        scoring="neg_mean_absolute_error",
        random_state=seed,
        n_jobs=-1,
    )


def nested_cv(X, y, groups, names=None, n_iter=20, outer=5, inner=3, seed=42) -> pd.DataFrame:
    """Validación cruzada anidada: el lazo externo estima el error del modelo ya ajustado."""
    cv = GroupKFold(outer, shuffle=True, random_state=seed)
    rows = []
    for name in names or CATALOG:
        m = tuned(name, n_iter, inner, seed)
        search = isinstance(m, RandomizedSearchCV)
        r = cross_validate(
            m,
            X,
            y,
            groups=groups,
            cv=cv,
            scoring=SCORING,
            params={"groups": groups} if search else None,  # grupos para el lazo interno
        )
        for fold in range(outer):
            rows.append(
                {"modelo": name, "pliegue": fold, "fit_s": r["fit_time"][fold]}
                | {m: (1 if m == "r2" else -1) * r[f"test_{m}"][fold] for m in SCORING}
            )
    return pd.DataFrame(rows)


def summary(cv: pd.DataFrame) -> pd.DataFrame:
    """Media y desviación por modelo, ordenado por MAE."""
    agg = cv.drop(columns="pliegue").groupby("modelo").agg(["mean", "std"])
    return agg.sort_values(("mae", "mean"))


def fit_final(name, X, y, groups, n_iter=20, inner=3, seed=42):
    """Ajusta el modelo ganador con todo el train y devuelve el mejor estimador."""
    m = tuned(name, n_iter, inner, seed)
    m.fit(X, y, groups=groups) if isinstance(m, RandomizedSearchCV) else m.fit(X, y)
    return getattr(m, "best_estimator_", m)


def metrics(y_true, y_pred) -> dict:
    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }


def predict_one(model, dormitorios, banos, superficie_m2, lat, lon) -> float:
    if superficie_m2 <= 0 or dormitorios < 0 or banos < 0:
        raise ValueError("superficie debe ser > 0; dormitorios y baños, >= 0")
    X = pd.DataFrame(
        [[dormitorios, banos, superficie_m2, lat, lon]], columns=model.feature_names_in_
    )
    return float(np.asarray(model.predict(X))[0])
