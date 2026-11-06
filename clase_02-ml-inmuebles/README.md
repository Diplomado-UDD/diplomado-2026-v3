---
tipo: actividad
tags: [machine-learning, scraping, real-estate, rust, objetivo/dataset-inmuebles-providencia]
fecha: 23-10-26
objetivo: Obtener un dataset de departamentos usados en venta en Providencia para un ejercicio de ML en Python.
---

# ml-inmuebles

El módulo `ingesta` (Rust) descarga los avisos de Portal Inmobiliario y escribe un CSV. El ejercicio de ML (Machine Learning, aprendizaje automático) usa ese CSV desde Python.

Fuente: `https://www.portalinmobiliario.com/venta/departamento/propiedades-usadas/providencia-metropolitana`. El módulo excluye los proyectos nuevos y los avisos cuya dirección no termina en "Providencia".

## Uso

```bash
cd ingesta
cargo run --release -- scrape  # escribe data/inmuebles_providencia.csv
cargo run --release -- geo     # agrega lat, lon, barrio y geo_nivel (~80 min)
cargo run --release -- filter  # escribe data/inmuebles_providencia_geo.csv, solo con coordenadas
cargo run --release -- etl     # scrape + geo + filter en secuencia
cargo run --release -- scrape otro.csv
cargo test
```

## Limpieza (Python)

El notebook `notebooks/limpieza.ipynb` lee `data/inmuebles_providencia_geo.csv` y escribe `data/inmuebles_providencia_limpio.csv`:

1. Convierte los precios en CLP a UF con el valor de la UF de hoy (mindicador.cl o findic.cl). La columna `uf_fecha` indica la fecha de ese valor.
2. Elimina filas sin precio o sin superficie.
3. Elimina outliers con la regla del IQR (rango intercuartílico) sobre el logaritmo del precio y de la superficie.

```bash
uv sync
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/limpieza.ipynb
```

```python
import pandas as pd
df = pd.read_csv("data/inmuebles_providencia_limpio.csv")
```

## Columnas

Columnas del CSV del ETL. El CSV limpio reemplaza `precio` y `moneda` por `precio_uf`, `precio_clp` y `uf_fecha`.

| Columna | Descripción |
|---|---|
| id | Identificador del aviso (MLC...) |
| titulo | Título del aviso |
| precio | Valor numérico |
| moneda | `CLF` (UF, Unidad de Fomento) o `CLP` (pesos chilenos) |
| dormitorios, banos | Número; un rango "1 a 2" queda como promedio (1,5) |
| superficie_texto | Texto original, por ejemplo "32 - 45 m² útiles" |
| superficie_m2 | Número; un rango queda como promedio: (32+45)/2 = 38,5 |
| direccion | Dirección publicada (calle, barrio o referencia, comuna) |
| url | Enlace canónico al aviso |
| lat, lon | Coordenadas según OpenStreetMap (Nominatim); vacías si no hay resultado dentro de Providencia |
| barrio | Barrio según OpenStreetMap |
| geo_nivel | Tipo de lugar encontrado en OSM: `building` (edificio), `residential`/`tertiary`/`primary` (calle), `railway` (estación de metro), `neighbourhood` (barrio), etc. |

El comando `geo` consulta cada dirección distinta una sola vez, a 1 consulta por segundo (política de uso de Nominatim). Si la dirección completa no da resultado, prueba con el primer tramo y la comuna. Si se interrumpe, se puede volver a ejecutar: solo consulta las filas sin coordenadas. No hay código postal útil: OpenStreetMap entrega `7500000`, el código genérico de la comuna.

## Estructura

| Archivo | Capa |
|---|---|
| `ingesta/src/main.rs` | Presentación: CLI (interfaz de línea de comandos) y paginación |
| `ingesta/src/parse.rs` | Lógica: extracción del JSON embebido, filtros y normalización |
| `ingesta/src/source.rs` | Datos: HTTP (portal y Nominatim) y lectura/escritura del CSV |
| `notebooks/limpieza.ipynb` | Conversión a UF y filtro de outliers |
| `modelo/` | Proyecto independiente: modelo de precio (ver `modelo/README.md`) |

## Limitaciones

El portal entrega como máximo unos 2.016 avisos por búsqueda (42 páginas de 48). Las páginas siguientes responden HTTP 404. Para obtener el total (~3.175) hay que dividir la búsqueda, por ejemplo por rango de precio.

La conversión usa la UF del día en que se ejecuta el notebook, no la del día de publicación del aviso.

Los CSV en `data/` no se versionan. Para generarlos, ejecute `etl`.
