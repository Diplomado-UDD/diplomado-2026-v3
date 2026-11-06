"""Capa de lógica: modelo, matriz de confusión, costo por umbral y comparación de criterios."""

from dataclasses import dataclass
from functools import cache

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from umbral_fraude import datos as capa_datos

UMBRALES = np.round(np.arange(0.01, 1.00, 0.01), 2)
COSTO_FRAUDE = 300_000
COSTO_FALSA_ALARMA = 15_000


@dataclass(frozen=True)
class Lab:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    modelo: GradientBoostingClassifier
    prob: np.ndarray    # probabilidad de fraude de cada transacción de test
    y_real: np.ndarray


@cache
def preparar() -> Lab:
    """Genera datos, entrena y puntúa el test. Determinista: semillas fijas."""
    X_train, X_test, y_train, y_test = capa_datos.dividir(capa_datos.generar())
    modelo = GradientBoostingClassifier(random_state=0).fit(X_train, y_train)
    prob = modelo.predict_proba(X_test)[:, 1]
    return Lab(X_train, X_test, y_train, modelo, prob, y_test.to_numpy())


def evaluar(prob, y_real, umbral: float, costo_fraude: float, costo_falsa_alarma: float) -> dict:
    bloquear = prob >= umbral
    vp = int((bloquear & (y_real == 1)).sum())    # fraudes atrapados
    fn = int((~bloquear & (y_real == 1)).sum())   # fraudes que se escaparon
    fp = int((bloquear & (y_real == 0)).sum())    # clientes buenos bloqueados
    vn = int((~bloquear & (y_real == 0)).sum())   # clientes buenos sin molestia
    return {
        "vp": vp, "fn": fn, "fp": fp, "vn": vn,
        "precision": vp / (vp + fp) if (vp + fp) else 0.0,
        "recall": vp / (vp + fn) if (vp + fn) else 0.0,
        "exactitud": (vp + vn) / len(y_real),
        "costo": fn * costo_fraude + fp * costo_falsa_alarma,
    }


def tabla(prob, y_real, costo_fraude: float, costo_falsa_alarma: float) -> pd.DataFrame:
    """Una fila por umbral candidato (0.01 a 0.99)."""
    return pd.DataFrame([{"umbral": u, **evaluar(prob, y_real, u, costo_fraude, costo_falsa_alarma)}
                         for u in UMBRALES])


def comparar(prob, y_real, costo_fraude: float, costo_falsa_alarma: float):
    """Devuelve (fila de mayor exactitud, fila de menor costo)."""
    t = tabla(prob, y_real, costo_fraude, costo_falsa_alarma)
    return t.loc[t["exactitud"].idxmax()], t.loc[t["costo"].idxmin()]
