---
tipo: nota
tags: [cmf, jev, audit, classification]
fecha: 23-10-26
objetivo: Registrar el estado de la clasificación de reclamos CMF y los comandos que la validan.
---

La actividad clasifica reclamos de la CMF (Comisión para el Mercado Financiero) con Jev. El notebook ya escribió `reclamos_20201221_clasificados_jev.xlsx` con 100 filas, dos etiquetas válidas y confianza entre 0.10 y 1.0. No hay Docker ni base de datos. No hay repositorio git en esta carpeta.

## Estado

Notebook canónico: `clasificar_reclamos_jev.ipynb`. Kernel: `.venv` con Python 3.12.7. SDK: `typesafe-sdk` 0.7.5. Pandas: 3.1.0.

Exactitud de la muestra de 30 filas, semilla 42: 100%. Cinco reclamos sin etiqueta tienen confianza bajo 0.5 y quedan para revisión manual.

La etiqueta cruda `APIA -Reclamo Seguros ` trae un espacio final en las 662 filas. El notebook aplica `str.strip()` antes de armar las categorías.

## Comandos

```bash
uv sync
uv run --with jupyterlab jupyter lab clasificar_reclamos_jev.ipynb
uv run --with ruff ruff check clasificar_reclamos_jev.ipynb pyproject.toml
```

Chequeo de datos, sin llamar a la API:

```bash
uv run python -c "import pandas as pd; o=pd.read_excel('reclamos_20201221_clasificados_jev.xlsx'); assert len(o)==100 and o['MERCADO_JEV'].notna().all()"
```

## Pendiente

No hay tests. `pytest` no está en las dependencias y no recolecta módulos. Agregar un test de contrato de los Excel es una tarea aparte.

El notebook lee `JEV_API_KEY` desde `.env`. No imprimir esa clave.
