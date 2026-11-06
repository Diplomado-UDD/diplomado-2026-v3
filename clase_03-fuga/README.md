---
tipo: nota
tags: [teaching, churn, machine-learning, genai, objetivo/laboratorio-clase-03]
fecha: 23-10-26
objetivo: Describir los archivos y la ejecución del laboratorio de fuga de clientes de la Clase 3.
---

# Clase 3: laboratorio de fuga de clientes

Laboratorio del Módulo II que compara no hacer nada, reglas, ML (*Machine Learning*, aprendizaje automático) y ML con GenAI (IA generativa) para reducir la fuga de clientes al menor costo.

| Archivo | Contenido |
|---|---|
| `clase_03_laboratorio.ipynb` | Notebook del alumno, ejecutado, con historia, analogías, diagramas incrustados y autoevaluaciones |
| `data.csv` | Dataset sintético de 500 clientes |
| `pyproject.toml`, `uv.lock` | Dependencias del ambiente virtual (uv) |
| `img/` | Fuente de los diagramas (ya incrustados en el notebook) |
| `diagramas.py` | Genera `img/` y lo incrusta en el notebook (`uv run python diagramas.py`) |

## Estructura del notebook

El notebook cuenta una historia: Paula, gerenta de clientes de una tienda ficticia, debe decidir qué hacer con el presupuesto de cupones. Javier (cliente C0321) aparece en cada bloque y muestra la lección en un caso concreto. La clase cierra con el memo de Paula al gerente general y un glosario.

Cada bloque abre con un mapa “Ustedes están aquí” (`mapa_bloque_1.png` a `mapa_bloque_5.png`), un resumen “En 30 segundos” y “El conflicto”. Cierra con “Lo que Paula aprendió”, una autoevaluación con respuesta oculta, un “Punto de control” y el anuncio del próximo bloque. Los detalles técnicos opcionales van en secciones plegables “Para profundizar”.

| Bloque | Pregunta | Analogía | Diagrama |
|---|---|---|---|
| 1 Diagnóstico | ¿Cuánto nos cuesta la fuga? | Balde con agujero | `train_test.png`, `matriz_costos.png` |
| 2 Reglas | SI pasa X, ENTONCES cupón | Alarma de humo | `regla.png` |
| 3 ML | ¿Qué probabilidad de fuga tiene cada cliente? | Médico que aprende de fichas; paraguas | `pipeline_ml.png`, `paraguas.png`, `validacion_cruzada.png` |
| 4 GenAI | ¿Qué decirle a cada uno? | ML elige a quién; GenAI escribe la carta | `privacidad.png` |
| 5 Decisión | ¿Qué conviene según el tamaño? | Auto propio o Uber | `auto_uber.png` |

`mapa_clase.png` resume los cinco bloques en la apertura.

## Ejecución

```bash
uv sync                                         # crea .venv desde pyproject.toml y uv.lock
uv run jupyter notebook clase_03_laboratorio.ipynb
```

En Cursor o VS Code, elegir el kernel `.venv/bin/python`. En Colab basta con subir el notebook y `data.csv`: los diagramas van incrustados.

El LLM (*Large Language Model*, modelo de lenguaje) real es opcional. Requiere `ANTHROPIC_API_KEY` en un archivo `.env` en esta carpeta o en una superior (recomendado, para que no viaje al compartir la carpeta), y `ANTHROPIC_WORKSPACE_ID` si la llave no está asociada a un *workspace*. Sin clave, el notebook usa una versión simulada. El archivo `.env` nunca se comparte ni se sube a un repositorio.
