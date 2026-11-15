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
| 1 | Herramientas trazables con `@traceable` y política de compras en código: proveedor bloqueado, cantidad máxima y umbral de aprobación HITL (*human in the loop*) |
| 2 | Loop ReAct (*Reason + Act*) con `wrap_anthropic`, salida estándar validada con Pydantic y lectura de la traza |
| 3 | Modos SIMULATE, SAFE y LIVE, más idempotencia de las órdenes |
| 4 | Uso de tokens y *prompt caching* del catálogo |
| 5 | Evaluación con cuatro casos, métricas y decisión *go/no-go* |

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

Una pasada completa con clave hace unas 30 llamadas al modelo. Las trazas quedan en **Tracing**, proyecto `clase-09-agentes`; las de la misión 5 llevan la etiqueta `eval`.

Las pruebas corren sin red ni claves:

```bash
uv run pytest
```
