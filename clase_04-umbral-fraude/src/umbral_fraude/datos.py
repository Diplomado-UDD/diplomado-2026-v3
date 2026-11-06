"""Capa de datos: set sintético de transacciones y partición train/test."""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

SEMILLA = 42
N = 20_000
ETIQUETA = "es_fraude"


def generar(n: int = N, semilla: int = SEMILLA) -> pd.DataFrame:
    """Genera transacciones sintéticas. La misma semilla da siempre los mismos datos."""
    rng = np.random.default_rng(semilla)
    datos = pd.DataFrame({
        "monto_clp": np.round(rng.lognormal(mean=10.2, sigma=1.0, size=n), -2),
        "hora_del_dia": rng.integers(0, 24, n),
        "distancia_km": np.round(rng.exponential(8, n), 1),
        "intentos_fallidos_24h": rng.poisson(0.15, n),
        "antiguedad_cliente_meses": rng.integers(1, 241, n),
        "compra_internacional": rng.binomial(1, 0.08, n),
        "comercio_nuevo": rng.binomial(1, 0.30, n),
    })
    riesgo = (-7.2
              + 1.6 * np.log1p(datos["monto_clp"] / 50_000)
              + 2.0 * (datos["hora_del_dia"] <= 5)
              + 0.06 * np.minimum(datos["distancia_km"], 60)
              + 1.6 * datos["intentos_fallidos_24h"]
              - 0.012 * datos["antiguedad_cliente_meses"]
              + 2.4 * datos["compra_internacional"]
              + 1.4 * datos["comercio_nuevo"]
              + rng.normal(0, 0.5, n))
    datos[ETIQUETA] = rng.binomial(1, 1 / (1 + np.exp(-riesgo)))
    return datos


def dividir(datos: pd.DataFrame):
    """Mitad para entrenar, mitad para evaluar, con la misma tasa de fraude en ambas."""
    X = datos.drop(columns=ETIQUETA)
    y = datos[ETIQUETA]
    return train_test_split(X, y, test_size=0.5, random_state=0, stratify=y)
