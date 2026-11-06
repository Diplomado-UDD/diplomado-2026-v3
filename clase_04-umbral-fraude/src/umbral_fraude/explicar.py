"""Capa de lógica: explicación de un falso positivo con SHAP y con LIME."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from lime.lime_tabular import LimeTabularExplainer

from umbral_fraude.umbral import Lab


def cliente_bloqueado(lab: Lab, umbral: float) -> int:
    """Índice (en test) del cliente bueno bloqueado con mayor probabilidad de fraude."""
    falsos_positivos = np.where((lab.prob >= umbral) & (lab.y_real == 0))[0]
    if not len(falsos_positivos):
        raise ValueError(f"Con umbral {umbral:.2f} no hay clientes buenos bloqueados.")
    return int(falsos_positivos[np.argmax(lab.prob[falsos_positivos])])


def explicar_shap(lab: Lab, i: int) -> shap.Explanation:
    explicador = shap.TreeExplainer(lab.modelo, data=lab.X_train.sample(100, random_state=0),
                                    model_output="probability")
    return explicador(lab.X_test.iloc[[i]])[0]


@dataclass(frozen=True)
class Lime:
    prob_modelo: float
    prob_recta: float
    fidelidad: float                   # R² ponderado de la recta local
    reglas: list[tuple[str, float]]    # (regla, peso); peso > 0 empuja a fraude


def explicar_lime(lab: Lab, i: int) -> Lime:
    columnas = list(lab.X_train.columns)

    def probabilidad_fraude(matriz):
        # LIME entrega una matriz sin nombres; el modelo espera la tabla con columnas.
        return lab.modelo.predict_proba(pd.DataFrame(matriz, columns=columnas))

    explicador = LimeTabularExplainer(
        lab.X_train.to_numpy(),
        feature_names=columnas,
        class_names=["legítima", "fraude"],
        categorical_features=[columnas.index(c) for c in ("compra_internacional", "comercio_nuevo")],
        discretize_continuous=True,
        sample_around_instance=True,
        feature_selection="none",
        random_state=0,
    )
    e = explicador.explain_instance(lab.X_test.iloc[i].to_numpy(), probabilidad_fraude,
                                    num_features=len(columnas), num_samples=4_000)
    return Lime(
        prob_modelo=float(e.predict_proba[1]),
        prob_recta=float(np.asarray(e.local_pred).reshape(-1)[0]),
        fidelidad=float(e.score),
        reglas=e.as_list(label=1),
    )


def variable_de(regla: str, columnas) -> str:
    """Nombre de la variable dentro de una regla LIME (el más largo, si hay varios)."""
    coincidencias = [c for c in columnas if c in regla]
    return max(coincidencias, key=len) if coincidencias else regla


def signo(aporte_shap: float, peso_lime: float, casi_nulo: float = 0.01) -> str:
    if abs(aporte_shap) < casi_nulo and abs(peso_lime) < casi_nulo:
        return "ambas casi nulas"
    return "sí" if aporte_shap * peso_lime > 0 else "no"


def comparar_signos(exp_shap: shap.Explanation, lime: Lime) -> pd.DataFrame:
    aportes = pd.Series(exp_shap.values, index=list(exp_shap.feature_names))
    filas = []
    for regla, peso in lime.reglas:
        variable = variable_de(regla, aportes.index)
        aporte = float(aportes[variable])
        filas.append({"Variable": variable, "Regla LIME": regla, "Peso LIME": peso,
                      "Aporte SHAP": aporte, "Mismo signo": signo(aporte, peso)})
    return pd.DataFrame(filas)
