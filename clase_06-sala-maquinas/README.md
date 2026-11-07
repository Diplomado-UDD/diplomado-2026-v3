---
tipo: actividad
tags: [teaching, llm, tokens, embeddings, rag]
fecha: 07-11-26
objetivo: Ejecutar el laboratorio de la clase 6 sobre tokens, costos, ventana de contexto, embeddings y búsqueda semántica.
---

# Clase 6: la sala de máquinas de un LLM

El notebook es `clase_06-lab_sala_maquinas.ipynb`. Tiene siete misiones. Cada misión termina con una pregunta para la puesta en común.

| Misión | Concepto |
|---|---|
| 1 | Tokenizador `o200k_base` y costo del idioma |
| 2 | Calculadora de costo con precios de Claude (noviembre de 2026) |
| 3 | Ventana de contexto: páginas que caben en 1 millón de tokens |
| 4 | Embeddings, similitud coseno y analogías |
| 5 | Mapa de palabras con PCA (análisis de componentes principales) |
| 6 | Buscador por palabras frente a buscador semántico |
| 7 | Auto-atención: el vector de "banco" según la frase |

## Ambiente

Esta carpeta tiene su propio ambiente virtual. Hace falta [uv](https://docs.astral.sh/uv/).

```bash
cd clase_06-sala-maquinas
uv sync
```

En Cursor o VS Code, el kernel es `clase_06-sala-maquinas/.venv/bin/python3`. Para abrir Jupyter en el navegador:

```bash
uv run --with jupyterlab jupyter lab clase_06-lab_sala_maquinas.ipynb
```

El notebook no necesita clave de API. La primera ejecución descarga el modelo `paraphrase-multilingual-MiniLM-L12-v2` (unos 470 MB).
