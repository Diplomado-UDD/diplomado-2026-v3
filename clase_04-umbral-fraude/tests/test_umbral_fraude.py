import numpy as np
import pandas as pd

from umbral_fraude import datos, expediente, explicar, umbral


def test_datos_reproducibles():
    d = datos.generar()
    assert len(d) == 20_000 and d[datos.ETIQUETA].sum() == 379
    pd.testing.assert_frame_equal(d, datos.generar())


def test_evaluar_matriz_y_costo():
    prob = np.array([0.9, 0.6, 0.4, 0.1])
    y = np.array([1, 0, 1, 0])
    r = umbral.evaluar(prob, y, 0.5, costo_fraude=100, costo_falsa_alarma=10)
    assert (r["vp"], r["fp"], r["fn"], r["vn"]) == (1, 1, 1, 1)
    assert r["precision"] == r["recall"] == r["exactitud"] == 0.5
    assert r["costo"] == 110


def test_criterios_del_notebook():
    lab = umbral.preparar()
    exacta, barata = umbral.comparar(lab.prob, lab.y_real, 300_000, 15_000)
    assert (exacta["umbral"], barata["umbral"]) == (0.63, 0.04)
    assert exacta["costo"] - barata["costo"] == 18_990_000


def test_signo_y_variable():
    assert explicar.signo(0.2, 0.1) == "sí"
    assert explicar.signo(0.2, -0.1) == "no"
    assert explicar.signo(0.001, -0.005) == "ambas casi nulas"
    assert explicar.variable_de("monto_clp > 53000.00", ["monto_clp"]) == "monto_clp"


def test_cierre_exige_decision_y_revision():
    assert expediente.puede_cerrar("levantar", hechos_revisados=False)
    assert expediente.puede_cerrar("mantener", hechos_revisados=True)
    assert not expediente.puede_cerrar("mantener", hechos_revisados=False)
    assert not expediente.puede_cerrar("quizás", hechos_revisados=True)
    assert expediente.pesos(1234567) == "$1.234.567"
