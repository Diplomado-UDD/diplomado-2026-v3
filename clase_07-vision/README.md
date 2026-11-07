---
tipo: actividad
tags: [teaching, computer-vision, yolo, vlm, ocr]
fecha: 07-11-26
objetivo: Ejecutar el laboratorio de la clase 7 sobre píxeles, convolución, detección de objetos y lectura de facturas con un VLM.
---

# Clase 7: cómo ve una máquina

El notebook es `clase_07-lab_vision.ipynb`. Tiene cinco misiones. Cada misión termina con una pregunta para la puesta en común.

| Misión | Concepto |
|---|---|
| 1 | Una foto como tabla de números: píxeles y canales RGB (rojo, verde, azul) |
| 2 | Convolución con numpy, la base de una CNN (red neuronal convolucional) |
| 3 | Detección de objetos con YOLO26n y el umbral de confianza |
| 4 | Lectura de una factura ficticia con Claude Haiku 5.5 y validación con reglas |
| 5 | El "último kilómetro": de la detección a la alerta |

VLM significa modelo de visión y lenguaje.

## Ambiente

Esta carpeta tiene su propio ambiente virtual. Hace falta [uv](https://docs.astral.sh/uv/).

```bash
cd clase_07-vision
uv sync
```

En Cursor o VS Code, el kernel es `clase_07-vision/.venv/bin/python3`. Para abrir Jupyter en el navegador:

```bash
uv run --with jupyterlab jupyter lab clase_07-lab_vision.ipynb
```

La misión 3 descarga una vez el modelo `yolo26n.pt` (unos 5 MB). La misión 4 busca `ANTHROPIC_API_KEY` en un archivo `.env` de esta carpeta o de una carpeta superior. Sin clave, o con `USAR_CLAUDE = False`, usa una respuesta simulada que trae un error a propósito.
