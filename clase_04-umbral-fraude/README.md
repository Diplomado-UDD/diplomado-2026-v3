---
tipo: actividad
tags: [machine-learning, fraud-detection, threshold, cost-sensitive, shap, lime, eu-ai-act]
fecha: 03-11-26
objetivo: Elegir el umbral de bloqueo de un modelo de fraude según el costo de los errores, explicar un falso positivo con SHAP y LIME, y cerrar la decisión con un expediente.
---

# umbral-fraude

El laboratorio en notebook es `clase_04-lab_umbral_fraude.ipynb`, en esta misma carpeta. El proyecto Python repite esos pasos como subcomandos, sin notebook. Los gráficos quedan en `salidas/`. El texto didáctico de cada paso está en [GUIA.md](GUIA.md).

## Uso

```bash
uv sync
uv run fraude todo                                    # pasos 2 a 9 en orden
uv run fraude datos                                   # Paso 2
uv run fraude entrenar                                # Paso 3
uv run fraude exactitud                               # Paso 4
uv run fraude panel --umbral 0.20                     # Paso 5
uv run fraude panel --umbral 0.10 --costo-falsa-alarma 60000
uv run fraude comparar --costo-falsa-alarma 60000     # Paso 6
uv run fraude shap                                    # Paso 7
uv run fraude lime                                    # Paso 8
uv run fraude expediente --decision mantener          # Paso 9
uv run fraude expediente --decision mantener --sin-revision   # expediente abierto
uv run pytest
```

Opciones comunes: `--costo-fraude` (CLP por fraude no detectado, 300.000 por defecto) y `--costo-falsa-alarma` (CLP por cliente bueno bloqueado, 15.000 por defecto). Los pasos 7 a 9 usan el umbral de menor costo con esos costos. `fraude <paso> -h` muestra todas las opciones.

## Resultados (semilla 42, costos por defecto)

| | Mayor exactitud | Menor costo |
|---|---|---|
| Umbral | 0,63 | 0,04 |
| Recall | 11,1 % | 61,4 % |
| Fraudes que se escaparon | 168 | 73 |
| Clientes buenos bloqueados | 14 | 648 |
| Costo total | $50.610.000 | $31.620.000 |

LIME sobre el falso positivo más sospechoso: probabilidad del modelo 97 %, de la recta local 21 %, R² ponderado 0,30. Bajo la barra de 0,70, el expediente exige decisión humana.

## Estructura

| Archivo | Capa |
|---|---|
| `src/umbral_fraude/cli.py` | Presentación: subcomandos por paso, impresión y gráficos |
| `src/umbral_fraude/umbral.py` | Lógica: modelo, matriz de confusión, costo por umbral |
| `src/umbral_fraude/explicar.py` | Lógica: SHAP, LIME y comparación de signos |
| `src/umbral_fraude/expediente.py` | Lógica: expediente y texto para el cliente |
| `src/umbral_fraude/datos.py` | Datos: set sintético y partición train/test |
| `tests/test_umbral_fraude.py` | Tests, incluye los umbrales del notebook |
| `GUIA.md` | Texto didáctico y preguntas para la puesta en común |
