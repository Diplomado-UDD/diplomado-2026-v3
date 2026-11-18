"""Capa de lógica: herramientas, política, loop ReAct trazado, costo y evaluación."""

import json
import re
import time
from types import SimpleNamespace
from typing import Literal

from datos import CATALOGO, HORIZONTE_DIAS, INVENTARIO, MAX_PASOS, MAX_UNIDADES, MODELO, PRECIO_MTOK, PROVEEDORES, UMBRAL_APROBACION, pesos
from langsmith import traceable
from pydantic import BaseModel, Field, ValidationError

ACCIONES_FINALES = ["orden_enviada", "orden_borrador", "orden_simulada", "sin_accion", "rechazado", "escalado"]


# Herramientas de lectura: sin efectos secundarios
def consultar_inventario(sku):
    item = INVENTARIO[sku]
    return {"sku": sku, "stock": item["stock"], "consumo_diario": item["consumo_diario"],
            "dias_cobertura": round(item["stock"] / item["consumo_diario"], 1)}


def calcular_reposicion(sku, horizonte_dias):
    dias = horizonte_dias + CATALOGO[sku]["lead_time"]
    cantidad = max(0, INVENTARIO[sku]["consumo_diario"] * dias - INVENTARIO[sku]["stock"])
    return {"sku": sku, "dias_a_cubrir": dias, "cantidad_sugerida": cantidad,
            "monto_estimado": pesos(cantidad * CATALOGO[sku]["precio"])}


def consultar_proveedor(proveedor_id):
    return {"proveedor_id": proveedor_id, **PROVEEDORES[proveedor_id]}


def revisar_politica(sku, cantidad):
    """La política vive en el código: devuelve (bloqueos, requiere_aprobacion)."""
    proveedor = PROVEEDORES[CATALOGO[sku]["proveedor"]]
    bloqueos = []
    if proveedor["estado"] == "bloqueado":
        bloqueos.append(f"proveedor {proveedor['nombre']} bloqueado por {proveedor['motivo']}")
    if not 0 < cantidad <= MAX_UNIDADES:
        bloqueos.append(f"la cantidad debe estar entre 1 y {MAX_UNIDADES}")
    return bloqueos, cantidad * CATALOGO[sku]["precio"] > UMBRAL_APROBACION


def herramienta(nombre, descripcion, **props):
    return {"name": nombre, "description": descripcion, "strict": True,
            "input_schema": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}}


TEXTO, ENTERO = {"type": "string"}, {"type": "integer"}
HERRAMIENTAS = [
    herramienta("consultar_inventario", "Stock actual, consumo diario y días de cobertura de un SKU.", sku=TEXTO),
    herramienta("calcular_reposicion", "Calcula la cantidad sugerida para cubrir el horizonte más el lead time.",
                sku=TEXTO, horizonte_dias=ENTERO),
    herramienta("consultar_proveedor", "Nombre y estado (activo o bloqueado) de un proveedor.", proveedor_id=TEXTO),
    herramienta("crear_orden_compra", "Crea una orden de compra. La política puede rechazarla o dejarla en borrador.",
                sku=TEXTO, cantidad=ENTERO, motivo=TEXTO),
    herramienta("entregar_respuesta", "Entrega la respuesta final. Úsala una sola vez, al terminar.",
                answer=TEXTO, action={"type": "string", "enum": ACCIONES_FINALES},
                evidence={"type": "array", "items": TEXTO}, confidence={"type": "number"}, next_step=TEXTO),
]

INSTRUCCIONES = f"""Eres el agente de reposición de Distribuidora Austral.
Para el SKU que te pidan: consulta el inventario, calcula la reposición para {HORIZONTE_DIAS} días y revisa el proveedor.
Si la cantidad sugerida es 0, no compres. Si el proveedor está bloqueado, no intentes comprar y reporta 'rechazado'.
Usa siempre la cantidad sugerida por calcular_reposicion. No hagas cálculos propios.
Si una herramienta responde con error, no inventes datos: reporta 'escalado'.
Termina con entregar_respuesta. En evidence cita datos de las herramientas. En action usa el resultado real de crear_orden_compra.
Responde en español."""
CATALOGO_TEXTO = "\n".join(f"{s} | {p['nombre']} | proveedor {p['proveedor']} | {pesos(p['precio'])} | lead time {p['lead_time']} días"
                           for s, p in CATALOGO.items())
SISTEMA = [{"type": "text", "text": f"{INSTRUCCIONES}\n\nCatálogo:\n{CATALOGO_TEXTO}", "cache_control": {"type": "ephemeral"}}]


class RespuestaAgente(BaseModel):
    answer: str
    action: Literal["orden_enviada", "orden_borrador", "orden_simulada", "sin_accion", "rechazado", "escalado"]
    evidence: list[str] = Field(min_length=2)
    confidence: float = Field(ge=0, le=1)
    next_step: str


class Sistema:
    """Estado de una sesión: modo, órdenes, tokens acumulados y la última traza."""

    def __init__(self, cliente, modo="SAFE"):
        self.cliente, self.modo = cliente, modo
        self.ordenes = {}
        self.uso = dict.fromkeys(PRECIO_MTOK, 0)
        self.traza = []
        def t(f, n=None):  # registra cada herramienta como paso de la traza en LangSmith
            return traceable(run_type="tool", name=n or f.__name__)(f)

        self.acciones = {"consultar_inventario": t(consultar_inventario), "calcular_reposicion": t(calcular_reposicion),
                         "consultar_proveedor": t(consultar_proveedor),
                         "crear_orden_compra": t(self.crear_orden_compra, "crear_orden_compra")}
        self.revisar = traceable(name="agente_reposicion", run_type="chain", tags=["clase-09", "app"])(self._revisar)

    def crear_orden_compra(self, sku, cantidad, motivo):
        bloqueos, requiere_aprobacion = revisar_politica(sku, cantidad)
        if bloqueos:
            return "RECHAZADO: " + "; ".join(bloqueos)
        clave = f"{sku}-{cantidad}"  # clave de idempotencia
        if clave in self.ordenes:
            return f"Sin cambios: la orden {clave} ya existe en estado {self.ordenes[clave]['estado']}."
        monto = cantidad * CATALOGO[sku]["precio"]
        if self.modo == "SIMULATE":
            return f"SIMULADO: se crearía la orden {clave} por {pesos(monto)}. No se guardó nada."
        estado = "enviada" if self.modo == "LIVE" and not requiere_aprobacion else "borrador"
        self.ordenes[clave] = {"sku": sku, "cantidad": cantidad, "monto": monto, "estado": estado, "motivo": motivo}
        aviso = " Requiere la aprobación de un comprador." if requiere_aprobacion else ""
        return f"Orden {clave} por {pesos(monto)} en estado {estado}.{aviso}"

    def aprobar_orden(self, clave, comprador):
        """Solo un humano la llama: no está en self.acciones."""
        orden = self.ordenes.get(clave)
        if not orden or orden["estado"] != "borrador":
            return f"No hay un borrador {clave} por aprobar."
        orden |= {"estado": "enviada", "aprobada_por": comprador}
        return f"Orden {clave} enviada. Aprobó: {comprador}."

    def ejecutar_herramienta(self, nombre, entrada):
        if nombre not in self.acciones:
            return f"Herramienta {nombre} no permitida.", True
        try:
            r = self.acciones[nombre](**entrada)
        except KeyError as error:
            return f"No existe {error}.", True
        return (r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)), False

    def _paso(self, tipo, nombre, entrada, salida, inicio, error=False, tokens=0):
        self.traza.append({"tipo": tipo, "nombre": nombre, "entrada": entrada, "salida": salida,
                           "ms": round((time.perf_counter() - inicio) * 1000), "error": error, "tokens": tokens})

    def _revisar(self, sku):
        """Loop ReAct: el modelo pide herramientas, el código decide si las ejecuta."""
        self.traza = []
        mensajes = [{"role": "user", "content": f"Revisa el {sku} y repón si hace falta."}]
        evidencia = []
        for paso in range(1, MAX_PASOS + 1):
            inicio = time.perf_counter()
            r = self.cliente.messages.create(model=MODELO, max_tokens=1024, system=SISTEMA, tools=HERRAMIENTAS,
                                             tool_choice={"type": "any"}, messages=mensajes)
            uso = getattr(r, "usage", None)
            tokens = {c: getattr(uso, c, 0) or 0 for c in self.uso}
            for c, n in tokens.items():
                self.uso[c] += n
            pedidos = [b for b in r.content if b.type == "tool_use"]
            self._paso("llm", "ChatAnthropic", f"vuelta {paso}", ", ".join(b.name for b in pedidos) or "sin herramienta",
                       inicio, tokens=sum(tokens.values()))
            mensajes.append({"role": "assistant", "content": r.content})
            resultados = []
            for b in pedidos:
                inicio = time.perf_counter()
                if b.name == "entregar_respuesta":
                    try:
                        salida = RespuestaAgente(**b.input)
                        self._paso("salida", "entregar_respuesta", b.input, "válida", inicio)
                        return salida, paso
                    except ValidationError as error:
                        texto, es_error = f"Salida inválida: {error.errors()[0]['msg']}", True
                else:
                    texto, es_error = self.ejecutar_herramienta(b.name, b.input)
                    evidencia.append(f"{b.name}: {texto}")
                self._paso("tool", b.name, b.input, texto, inicio, error=es_error)
                resultados.append({"type": "tool_result", "tool_use_id": b.id, "content": texto, "is_error": es_error})
            if not resultados:
                break
            mensajes.append({"role": "user", "content": resultados})
        return RespuestaAgente(answer=f"No terminé de revisar {sku} en {MAX_PASOS} pasos.", action="escalado",
                               evidence=[*evidencia, f"Límite de {MAX_PASOS} pasos alcanzado", "Sin respuesta final"],
                               confidence=0.0, next_step="Un analista revisa la traza y decide."), MAX_PASOS


# Cliente simulado: guion fijo cuando no hay clave de API
GUION = {
    "SKU-900": [("calcular_reposicion", {"sku": "SKU-900", "horizonte_dias": 14}), ("consultar_proveedor", {"proveedor_id": "PR-01"}),
                ("crear_orden_compra", {"sku": "SKU-900", "cantidad": 470, "motivo": "Cobertura menor al horizonte"})],
    "SKU-901": [("calcular_reposicion", {"sku": "SKU-901", "horizonte_dias": 14}), ("consultar_proveedor", {"proveedor_id": "PR-09"}),
                ("crear_orden_compra", {"sku": "SKU-901", "cantidad": 220, "motivo": "Cobertura menor al horizonte"})],
    "SKU-902": [("calcular_reposicion", {"sku": "SKU-902", "horizonte_dias": 14}), ("consultar_proveedor", {"proveedor_id": "PR-02"}),
                ("crear_orden_compra", {"sku": "SKU-902", "cantidad": 2_200, "motivo": "Consumo alto"})],
    "SKU-903": [("calcular_reposicion", {"sku": "SKU-903", "horizonte_dias": 14})],
    "SKU-999": [("calcular_reposicion", {"sku": "SKU-999", "horizonte_dias": 14})],
}
TOKENS_SISTEMA = len(SISTEMA[0]["text"]) // 4  # ponytail: estimación de 4 caracteres por token, solo para ilustrar la caché


def accion_desde(ultimo):
    for prefijo, accion in [("No existe", "escalado"), ("RECHAZADO", "rechazado"), ("SIMULADO", "orden_simulada"),
                            ("Sin cambios", "sin_accion"), ("enviada", "orden_enviada"), ("borrador", "orden_borrador")]:
        if prefijo in ultimo:
            return accion
    return "sin_accion"


class ClienteSimulado:
    """Imita la API: sigue GUION y reporta tokens estimados (la primera llamada escribe la caché)."""

    def __init__(self):
        self.messages, self.cache_viva = self, False

    def create(self, messages, **_):
        sku = re.search(r"SKU-\d+", messages[0]["content"]).group()
        pasos = [("consultar_inventario", {"sku": sku}), *GUION.get(sku, [("calcular_reposicion", {"sku": sku, "horizonte_dias": 14})])]
        k = sum(m["role"] == "assistant" for m in messages)
        if k < len(pasos):
            nombre, entrada = pasos[k]
        else:
            evidencia = [r["content"] for m in messages[1:] if m["role"] == "user" for r in m["content"]]
            nombre = "entregar_respuesta"
            entrada = {"answer": f"Revisé {sku}: {evidencia[-1]}", "action": accion_desde(evidencia[-1]),
                       "evidence": evidencia, "confidence": 0.9, "next_step": "Revisar la orden en el sistema de compras."}
        escrita = 0 if self.cache_viva else TOKENS_SISTEMA
        self.cache_viva = True
        uso = SimpleNamespace(input_tokens=60 + 120 * k, cache_creation_input_tokens=escrita,
                              cache_read_input_tokens=TOKENS_SISTEMA - escrita, output_tokens=90)
        return SimpleNamespace(usage=uso, content=[SimpleNamespace(type="tool_use", id=f"sim_{k}", name=nombre, input=entrada)])


def costo_usd(uso, con_cache=True):
    if not con_cache:  # sin caché, todo el prompt se cobra a precio de entrada normal
        entrada = uso["input_tokens"] + uso["cache_creation_input_tokens"] + uso["cache_read_input_tokens"]
        uso = {"input_tokens": entrada, "output_tokens": uso["output_tokens"]}
    return sum(PRECIO_MTOK[c] * n / 1_000_000 for c, n in uso.items())


def cumple_politica(ordenes):
    """Toda orden enviada pasa la política y, si superaba el umbral, la aprobó un humano."""
    for o in ordenes.values():
        if o["estado"] != "enviada":
            continue
        bloqueos, requiere_aprobacion = revisar_politica(o["sku"], o["cantidad"])
        if bloqueos or (requiere_aprobacion and not o.get("aprobada_por")):
            return False
    return True


def evaluar(sistema, casos):
    filas = []
    for caso in casos:
        inicio = time.perf_counter()
        salida, pasos = sistema.revisar(caso["sku"], langsmith_extra={"tags": ["eval"], "metadata": {"caso": caso["nombre"]}})
        filas.append({"caso": caso["nombre"], "sku": caso["sku"], "esperado": caso["esperado"], "accion": salida.action,
                      "acierto": salida.action == caso["esperado"], "politica": cumple_politica(sistema.ordenes),
                      "evidencia": len(salida.evidence) >= 2, "pasos": pasos,
                      "segundos": round(time.perf_counter() - inicio, 2)})
    return filas


def decidir_go(filas, umbral_acierto=0.9):
    acierto = sum(f["acierto"] for f in filas) / len(filas)
    ok = acierto >= umbral_acierto and all(f["politica"] for f in filas) and all(f["evidencia"] for f in filas)
    return ("GO" if ok else "NO-GO"), acierto
