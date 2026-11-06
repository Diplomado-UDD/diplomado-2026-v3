---
tipo: recurso
tags: [teaching, diplomado, actividades]
fecha: 06-11-26
objetivo: Indicar a los alumnos qué actividad corresponde a cada carpeta y cómo ejecutarla.
---

# Actividades del diplomado

Material de trabajo del Diplomado en Inteligencia Artificial para la Transformación Empresarial. Cada carpeta es una actividad. El detalle de datos y comandos está en el `README.md` de esa carpeta.

| Carpeta o archivo | Actividad |
|---|---|
| `guia-colab.pdf` | Cómo abrir un notebook en Google Colab |
| `clase_02-ml-inmuebles/` | Dataset de departamentos en Providencia y ejercicio de aprendizaje automático |
| `clase_03-fuga/` | Laboratorio de fuga de clientes: reglas, aprendizaje automático e IA generativa |
| `clase_04-umbral-fraude/` | Laboratorio del umbral de fraude. El notebook y el proyecto Python están en esa carpeta |
| `clase_05-prompting/` | Laboratorio de prompting con Claude (Anthropic) |
| `reclamos-cmf/` | Clasificación de reclamos de la CMF |
| `consigna-auditoria/` | Consigna y archivo de transacciones para el caso de auditoría |

## Ambiente

Hace falta [uv](https://docs.astral.sh/uv/). En esta carpeta:

```bash
uv sync
```

Eso crea `.venv` con Python 3.13 o superior. En Cursor o VS Code, el kernel del notebook es `.venv/bin/python3`.

Las carpetas `clase_02-ml-inmuebles`, `clase_03-fuga`, `clase_04-umbral-fraude` y `reclamos-cmf` tienen su propio `pyproject.toml`. Entra a la carpeta y ejecuta `uv sync` ahí antes de correr esa actividad.

## Claves

Algunas actividades llaman a una API. Crea un archivo `.env` en esta carpeta, o en la carpeta de la actividad, con estas variables:

```text
ANTHROPIC_API_KEY=
ANTHROPIC_WORKSPACE_ID=
JEV_API_KEY=
```

El archivo `.env` no se comparte. Sin `ANTHROPIC_API_KEY`, el laboratorio de la clase 3 usa una respuesta simulada. La clase 5 necesita esa clave. La actividad de reclamos necesita `JEV_API_KEY`.
