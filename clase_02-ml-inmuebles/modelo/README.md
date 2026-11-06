---
tipo: actividad
tags: [machine-learning, regression, cross-validation, conformal-prediction, catboost, xgboost, objetivo/modelo-precio-providencia]
fecha: 23-10-26
objetivo: Predecir el precio en UF de departamentos usados en Providencia con dormitorios, baños, superficie útil, latitud y longitud.
---

# modelo

Proyecto Python independiente (uv) que entrena y compara 7 regresores. Entrada: `../data/inmuebles_providencia_limpio.csv`, salida del notebook `../notebooks/limpieza.ipynb`.

## Uso

```bash
uv sync
uv run modelo train                              # CV anidada, ~1 min
uv run modelo train --models catboost xgboost --n-iter 50
uv run modelo conformal                           # CatBoost + intervalo al 90 %
uv run modelo predict 2 2 80 -33.4263 -70.6110   # dorm, baños, m², lat, lon -> UF [mín, máx]
uv run pytest
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/modelado.ipynb
```

El notebook `notebooks/modelado.ipynb` muestra el mismo flujo paso a paso, con gráficos.

## Método

1. Objetivo: `log(precio_uf)`. El modelo predice en UF con la transformación inversa.
2. Grupos: avisos con las mismas coordenadas (mismo edificio o calle) quedan siempre en el mismo pliegue. Así el modelo no memoriza el precio de un edificio.
3. Holdout: 20 % de los grupos queda como test y se usa una sola vez, al final.
4. Validación cruzada anidada sobre el train: `GroupKFold` externo de 5 pliegues mide el error; `RandomizedSearchCV` interno (`GroupKFold` de 3, 20 iteraciones) ajusta hiperparámetros.
5. Ubicación: el mismo CatBoost, con hiperparámetros fijos, se prueba sin latitud, sin longitud y con una zona de 6 grupos (KMeans, k-medias). Quitar la latitud sube el MAE. La zona no lo baja, porque el árbol ya corta el mapa con las coordenadas. Latitud y longitud se mantienen.
6. El modelo con menor MAE (error absoluto medio) se reentrena con todo el train y se evalúa en test.
7. Intervalo conformal sobre CatBoost. Del train, un 20 % de los grupos solo calibra. El resto ajusta el CatBoost. El puntaje es el residuo absoluto en logaritmo. El intervalo es multiplicativo y apunta a cubrir el 90 % de los precios de publicación. El test mide esa cobertura una sola vez. Este CatBoost no es el del punto 6: no vio la calibración.

Modelos: `dummy` (mediana, línea base), `ridge`, `knn`, `random_forest`, `hist_gb`, `xgboost`, `catboost`. Todos usan imputación por mediana y escalado.

## Resultados (23-10-26)

| Modelo | MAE CV (UF) | MAPE CV | R² CV |
|---|---|---|---|
| catboost | 1.204 ± 34 | 14,6 % | 0,67 |
| random_forest | 1.229 ± 69 | 15,0 % | 0,66 |
| xgboost | 1.250 ± 39 | 15,2 % | 0,65 |
| knn | 1.261 ± 95 | 15,7 % | 0,64 |
| hist_gb | 1.263 ± 55 | 15,4 % | 0,64 |
| ridge | 1.344 ± 44 | 16,4 % | 0,59 |
| dummy | 2.361 ± 175 | 31,7 % | -0,04 |

Test (catboost): MAE 1.353 UF, MAPE (error porcentual absoluto medio) 14,9 %, R² 0,60.

Intervalo conformal (27-10-26, semilla 42, alfa 0,10): margen ±31,9 % del precio predicho. En el test, cobertura 81,6 % y ancho medio 4.426 UF. El MAE de este CatBoost, ajustado sin los grupos de calibración, es 1.347 UF. El tramo medio de precio predicho queda en 71,8 % de cobertura. Las semillas 0, 1 y 7 dieron 89,4 %, 93,8 % y 87,4 %. El cuantil no se corrige con el test.

## Estructura

| Archivo | Capa |
|---|---|
| `src/modelo/cli.py` | Presentación: CLI `train`, `conformal` y `predict` |
| `src/modelo/models.py` | Lógica: catálogo de modelos y espacios de búsqueda |
| `src/modelo/features.py` | Lógica: ablación de latitud y zona geográfica |
| `src/modelo/evaluate.py` | Lógica: partición, CV anidada y métricas |
| `src/modelo/conformal.py` | Lógica: intervalo conformal del CatBoost |
| `src/modelo/data.py` | Datos: carga del CSV y artefactos |
| `notebooks/modelado.ipynb` | Flujo didáctico |
| `tests/test_modelo.py` | Tests con datos sintéticos |
| `artifacts/` | `modelo.joblib` y `conformal.joblib` (no versionados), `cv_resultados.csv`, `metricas_test.json`, `conformal.json` |
