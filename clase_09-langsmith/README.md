---
tipo: actividad
tags: [teaching, ai-agents, langsmith, observability, tracing, evals, anthropic]
fecha: 14-11-26
objetivo: Ejecutar el laboratorio de la clase 9, que construye un agente de reposición de inventario con trazas en LangSmith y lo evalúa antes de pasarlo a producción.
---

# Clase 9: un agente con trazas en LangSmith

El notebook es `clase_09-lab_langsmith.ipynb`. Un agente revisa el inventario de una distribuidora ficticia y crea órdenes de compra bajo una política. Cada llamada al modelo y cada herramienta quedan registradas como una traza en LangSmith. Cada misión termina con una pregunta para la puesta en común.

| Misión | Concepto |
|---|---|
| 1 | Herramientas trazables con `@traceable` y política de compras en código: proveedor bloqueado, cantidad máxima y umbral de aprobación HITL (*human in the loop*). Prueba de la política con casos fijos |
| 2 | Loop ReAct (*Reason + Act*) con `wrap_anthropic`, salida estándar validada con Pydantic, lectura de la traza desde código y escalamiento ante un SKU (*stock keeping unit*) inexistente |
| 3 | Modos SIMULATE, SAFE y LIVE, idempotencia de las órdenes y aprobación humana de montos altos |
| 4 | Uso de tokens, *prompt caching* del catálogo y costo en USD (dólares estadounidenses) por revisión y por mes |
| 5 | Evaluación con cinco casos, métricas, decisión *go/no-go* y experimento sobre un dataset de LangSmith |

## Ambiente

Esta carpeta tiene su propio ambiente virtual. Hace falta [uv](https://docs.astral.sh/uv/).

```bash
cd clase_09-langsmith
uv sync
cp env.example .env   # luego pega tus claves de Claude y LangSmith
```

En Cursor o VS Code, el kernel es `clase_09-langsmith/.venv/bin/python3`. Para abrir Jupyter en el navegador:

```bash
uv run --with jupyterlab jupyter lab clase_09-lab_langsmith.ipynb
```

El notebook busca el archivo `.env` en esta carpeta o en una carpeta superior. Las variables son:

| Variable | Uso |
|---|---|
| `ANTHROPIC_API_KEY` | Llama a Claude Haiku 5.5 (`claude-haiku-5-5`). Sin ella, el notebook usa un cliente simulado con un guion fijo |
| `LANGSMITH_TRACING` | `true` activa el envío de trazas |
| `LANGSMITH_API_KEY` | Clave de [smith.langchain.com](https://smith.langchain.com). Sin ella, las trazas se apagan y el agente funciona igual |
| `LANGSMITH_PROJECT` | Proyecto donde aparecen las trazas; el ejemplo usa `clase-09-agentes` |
| `LANGSMITH_ENDPOINT` | Solo para cuentas en la región de la Unión Europea |
| `LANGSMITH_WORKSPACE_ID` | Solo para claves con acceso a varios workspaces |

Una pasada completa con clave hace unas 35 llamadas al modelo; con LangSmith activo, el experimento de la misión 5 agrega unas 15 más. Las trazas quedan en **Tracing**, proyecto `clase-09-agentes`; las de la misión 5 llevan la etiqueta `eval`. El dataset `clase-09-reposicion` y sus experimentos (prefijo `clase-09`) quedan en **Datasets & Experiments**.

## Diagramas

Los diagramas del notebook están en `img/` y van incrustados en las celdas. Para regenerarlos e incrustarlos de nuevo:

```bash
uv run python diagramas.py
```

Las pruebas corren sin red ni claves:

```bash
uv run pytest
```
