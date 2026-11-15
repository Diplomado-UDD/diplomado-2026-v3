---
tipo: actividad
tags: [teaching, ai-agents, automation, tool-use, guardrails, hitl, anthropic]
fecha: 14-11-26
objetivo: Ejecutar el laboratorio de la clase 8 que compara una automatización con un componente agéntico frente a un agente con autonomía controlada.
---

# Clase 8: ¿automatización o agente?

El notebook es `clase_08-lab_agentes.ipynb`. Resuelve los mismos cinco tickets de atención de una tienda ficticia por dos caminos y compara el resultado. Cada misión termina con una pregunta para la puesta en común.

| Misión | Concepto |
|---|---|
| 1 | Regla de elegibilidad: dos o más SÍ entre ambigüedad, razonamiento contextual y excepciones frecuentes apuntan a un agente |
| 2 | Camino (a), automatización con un componente agéntico: Claude clasifica el ticket con salida estructurada y reglas en Python deciden |
| 3 | Camino (b), agente con autonomía controlada: loop de herramientas con lista permitida, límite de pasos, HITL (*human in the loop*), kill switch y bitácora |
| 4 | Comparación lado a lado: acciones, llamadas al modelo y bitácora de auditoría |
| 5 | Kill switch y aprobación del supervisor |

La conclusión esperada: la automatización resuelve los casos estándar con una llamada y reglas auditables; el agente atiende los casos ambiguos y escala lo que supera su autoridad.

## Ambiente

Esta carpeta tiene su propio ambiente virtual. Hace falta [uv](https://docs.astral.sh/uv/).

```bash
cd clase_08-agentes
uv sync
cp env.example .env   # luego pega tu ANTHROPIC_API_KEY
```

En Cursor o VS Code, el kernel es `clase_08-agentes/.venv/bin/python3`. Para abrir Jupyter en el navegador:

```bash
uv run --with jupyterlab jupyter lab clase_08-lab_agentes.ipynb
```

El notebook busca `ANTHROPIC_API_KEY` en un archivo `.env` de esta carpeta o de una carpeta superior. Sin clave, o con `USAR_CLAUDE = False`, usa un clasificador por palabras clave y un cliente simulado que sigue un guion fijo. Con clave, usa Claude Haiku 5.5 (`claude-haiku-5-5`); una pasada completa hace unas 30 llamadas.

Las pruebas corren sin red ni clave:

```bash
uv run pytest
```
