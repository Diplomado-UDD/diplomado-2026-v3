"""Lógica: intervalo conformal multiplicativo sobre el mismo regresor.

El modelo puntual no cambia. Un bloque de grupos que ese modelo no ajusta
fija el cuantil q del residuo absoluto en logaritmo.
"""

import math

import numpy as np
import pandas as pd

from .evaluate import predict_one, split


def split_calibration(X, y, groups, cal_size=0.2, seed=42):
    """Reserva grupos del train para calibrar. El modelo no los ajusta.

    El segundo bloque es la calibración (fracción cal_size), igual que el
    test en split. Un edificio queda entero en ajuste o en calibración.
    """
    if not 0 < cal_size < 1:
        raise ValueError("cal_size debe estar entre 0 y 1")
    return split(X, y, groups, test_size=cal_size, seed=seed)


def scores(y_true, y_pred) -> np.ndarray:
    """Residuo absoluto en logaritmo: |log(y) - log(predicho)|."""
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    if y.size == 0 or p.size == 0 or y.shape != p.shape:
        raise ValueError("precio y predicción deben tener el mismo largo")
    if not np.isfinite(y).all() or not np.isfinite(p).all() or np.any(y <= 0) or np.any(p <= 0):
        raise ValueError("precio y predicción deben ser finitos y > 0")
    return np.abs(np.log(y) - np.log(p))


def quantile(s, alpha: float = 0.1) -> float:
    """Cuantil de orden k = techo((n + 1) · (1 - alpha)).

    k es la posición en la muestra ordenada, de 1 a n. Si k supera a n,
    la calibración no alcanza para ese alpha.
    """
    if not 0 < alpha < 1:
        raise ValueError("alpha debe estar entre 0 y 1")
    ordered = np.sort(np.asarray(s, dtype=float))
    n = int(ordered.size)
    if n == 0 or not np.isfinite(ordered).all():
        raise ValueError("los puntajes de calibración deben ser finitos")
    k = math.ceil((n + 1) * (1 - alpha))
    if k > n:
        raise ValueError(f"calibración insuficiente: n={n} no alcanza para alpha={alpha}")
    return float(ordered[k - 1])


def calibrate(model, X_cal, y_cal, alpha: float = 0.1) -> float:
    """Calcula q con avisos que el modelo no ajustó."""
    return quantile(scores(y_cal, model.predict(X_cal)), alpha)


def margin(q: float) -> float:
    """Holgura relativa exp(q) - 1. Un valor 0,15 equivale a ±15 %."""
    if not np.isfinite(q) or q < 0:
        raise ValueError("q debe ser finito y >= 0")
    return float(np.exp(q) - 1)


def interval(y_pred, q: float) -> tuple[np.ndarray, np.ndarray]:
    """Intervalo [predicho · exp(-q), predicho · exp(q)]."""
    if not np.isfinite(q) or q < 0:
        raise ValueError("q debe ser finito y >= 0")
    p = np.asarray(y_pred, dtype=float)
    return p * np.exp(-q), p * np.exp(q)


def coverage(y_true, y_pred, q: float) -> dict:
    """Fracción de precios dentro del intervalo y ancho medio en UF."""
    y = np.asarray(y_true, dtype=float)
    if y.size == 0:
        raise ValueError("no hay precios para evaluar")
    lo, hi = interval(y_pred, q)
    dentro = (y >= lo) & (y <= hi)
    return {
        "cobertura": float(np.mean(dentro)),
        "ancho_medio_uf": float(np.mean(hi - lo)),
        "n": int(y.size),
    }


def coverage_by_band(y_true, y_pred, q: float, n_bands: int = 3) -> pd.DataFrame:
    """Cobertura por tramos del precio predicho."""
    if n_bands < 2:
        raise ValueError("n_bands debe ser >= 2")
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    lo, hi = interval(p, q)
    try:
        tramo = pd.qcut(p, n_bands, duplicates="drop")
    except ValueError:
        tramo = pd.Series(["unico"] * len(p))
    df = pd.DataFrame({"tramo": tramo, "dentro": (y >= lo) & (y <= hi), "ancho": hi - lo})
    return (
        df.groupby("tramo", observed=True)
        .agg(n=("dentro", "size"), cobertura=("dentro", "mean"), ancho_medio_uf=("ancho", "mean"))
        .reset_index()
    )


def predict_interval(model, q, dormitorios, banos, superficie_m2, lat, lon):
    """Devuelve precio puntual, límite inferior y límite superior, en UF."""
    punto = predict_one(model, dormitorios, banos, superficie_m2, lat, lon)
    lo, hi = interval([punto], q)
    return punto, float(lo[0]), float(hi[0])
