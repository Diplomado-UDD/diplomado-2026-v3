import numpy as np
import pandas as pd
import pytest

from modelo import conformal, evaluate, features
from modelo.data import FEATURES


def synthetic(n=200, seed=0):
    rng = np.random.default_rng(seed)
    X = pd.DataFrame(rng.random((n, len(FEATURES))), columns=FEATURES)
    X.iloc[0, 0] = np.nan  # la imputación debe cubrir datos faltantes
    y = pd.Series(np.exp(3 + 2 * X["superficie_m2"].fillna(0.5)))
    g = pd.Series(np.arange(n) % 40).astype(str)
    return X, y, g


def test_split_no_mezcla_grupos():
    X, y, g = synthetic()
    _, Xte, *_, gtr = evaluate.split(X, y, g)
    assert not set(gtr) & set(g.loc[Xte.index])


def test_zona_es_determinista():
    X, _, _ = synthetic()
    assert np.array_equal(features.zonas(X, k=4), features.zonas(X, k=4))
    assert set(features.zonas(X, k=4)).issubset(range(4))


def test_comparar_ubicacion():
    X, y, g = synthetic()
    tabla = features.comparar(X, y, g, folds=2, iterations=15, n_jobs=1)
    assert tabla.variante.tolist() == [v[0] for v in features.VARIANTES]
    assert tabla.loc[tabla.variante == "base", "delta_mae"].item() == 0
    assert tabla.mae.notna().all()


def test_nested_cv_y_prediccion():
    X, y, g = synthetic()
    cv = evaluate.nested_cv(X, y, g, ["dummy", "ridge"], n_iter=2, outer=2, inner=2)
    res = evaluate.summary(cv)
    assert res.index[0] == "ridge"  # supera a la línea base
    m = evaluate.fit_final("ridge", X, y, g, n_iter=2, inner=2)
    assert evaluate.predict_one(m, 1, 1, 0.5, 0.5, 0.5) > 0
    with pytest.raises(ValueError):
        evaluate.predict_one(m, 1, 1, -5, 0.5, 0.5)  # superficie imposible


def test_calibracion_no_mezcla_grupos():
    X, y, g = synthetic()
    Xtr, Xte, ytr, _yte, _gtr = evaluate.split(X, y, g)
    _Xfit, Xcal, _yfit, _ycal, gfit = conformal.split_calibration(Xtr, ytr, g.loc[Xtr.index])
    gcal = set(g.loc[Xcal.index])
    assert not set(gfit) & gcal
    assert not set(gfit) & set(g.loc[Xte.index])
    assert not gcal & set(g.loc[Xte.index])


def test_cuantil_es_el_orden_k():
    s = np.array([0.1, 0.4, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9])
    # n=9, alpha=0.1, k=techo(10*0.9)=9, el máximo
    assert conformal.quantile(s, alpha=0.1) == 0.9
    # n=3, alpha=0.5, k=techo(4*0.5)=2
    assert conformal.quantile(np.array([0.3, 0.1, 0.2]), alpha=0.5) == 0.2
    with pytest.raises(ValueError):
        conformal.quantile(np.array([0.1]), alpha=0.1)


def test_intervalo_es_multiplicativo():
    y = np.array([100.0, 200.0, 400.0])
    pred = np.array([110.0, 180.0, 500.0])
    assert np.allclose(conformal.scores(y, pred), np.abs(np.log(y) - np.log(pred)))
    q = np.log(1.1)
    lo, hi = conformal.interval(pred, q)
    assert np.allclose(lo, pred / 1.1)
    assert np.allclose(hi, pred * 1.1)
    assert conformal.margin(q) == pytest.approx(0.1)
    with pytest.raises(ValueError):
        conformal.scores([0.0], [1.0])


def test_cobertura_y_tramos():
    y = np.array([10, 10, 10, 20, 20, 20, 40, 40, 40], dtype=float)
    pred = y.copy()
    pred[-1] = 80
    cov = conformal.coverage(y, pred, q=0.0)
    assert cov["n"] == 9
    assert cov["cobertura"] == pytest.approx(8 / 9)
    tabla = conformal.coverage_by_band(y, pred, q=0.0, n_bands=3)
    assert tabla.n.sum() == 9
    assert set(tabla.columns) == {"tramo", "n", "cobertura", "ancho_medio_uf"}


class _PrecioFijo:
    feature_names_in_ = np.array(FEATURES)

    def predict(self, X):
        return np.full(len(X), 100.0)


def test_predecir_intervalo():
    punto, lo, hi = conformal.predict_interval(
        _PrecioFijo(), np.log(1.1), dormitorios=1, banos=1, superficie_m2=50, lat=0.2, lon=0.3
    )
    assert punto == 100
    assert lo == pytest.approx(100 / 1.1)
    assert hi == pytest.approx(110)
    with pytest.raises(ValueError):
        conformal.predict_interval(
            _PrecioFijo(), np.log(1.1), dormitorios=1, banos=1, superficie_m2=-1, lat=0, lon=0
        )
