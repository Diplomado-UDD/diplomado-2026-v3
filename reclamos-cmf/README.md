---
tipo: actividad
tags: [cmf, complaints, classification, jev, objetivo/clasificar-reclamos-cmf]
fecha: 23-10-26
objetivo: Clasificar reclamos ciudadanos a la CMF con Jev según las categorías de analistas.
---

# Reclamos CMF

Actividad del diplomado. El notebook `clasificar_reclamos_jev.ipynb` clasifica 100 reclamos sin categoría con Jev (modelo de TypeSafe AI). Las categorías provienen de 999 reclamos etiquetados por analistas de la CMF (Comisión para el Mercado Financiero).

## Datos

| Archivo | Filas | Columnas |
|---|---|---|
| `reclamos_20201221_con_clas.xlsx` | 999 | `CASO_ID`, `MERCADO_ANALISTA`, `DESCRIPCION_CIUDADANO`, `PETICION_CIUDADANO` |
| `reclamos_20201221_sin_clas.xlsx` | 100 | `CASO_ID`, `DESCRIPCION_CIUDADANO`, `PETICION_CIUDADANO` |

## Uso

```bash
uv sync
uv run --with jupyterlab jupyter lab clasificar_reclamos_jev.ipynb
```

El notebook lee `JEV_API_KEY` desde `.env` en esta carpeta.

El notebook valida la exactitud con 30 reclamos etiquetados. Luego clasifica los 100 reclamos y escribe `reclamos_20201221_clasificados_jev.xlsx` con `MERCADO_JEV` y `CONFIANZA_JEV`.
