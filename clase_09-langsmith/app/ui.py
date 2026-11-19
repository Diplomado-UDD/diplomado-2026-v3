"""Capa de presentación: `uv run streamlit run app/ui.py`."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
if not os.environ.get("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_TRACING"] = "false"  # sin clave de LangSmith no hay a dónde enviar trazas

import anthropic
import streamlit as st
from agente import ClienteSimulado, Sistema, costo_usd, decidir_go, evaluar, revisar_politica
from datos import CASOS, CATALOGO, INVENTARIO, MODOS, PROVEEDORES, UMBRAL_APROBACION, pesos
from langsmith.utils import tracing_is_enabled
from langsmith.wrappers import wrap_anthropic

st.set_page_config(page_title="Agente de reposición", layout="wide")
hay_clave = bool(os.environ.get("ANTHROPIC_API_KEY"))

with st.sidebar:
    st.header("Configuración")
    usar_claude = st.toggle("Usar Claude Haiku 5.5", value=hay_clave, disabled=not hay_clave,
                            help="Sin ANTHROPIC_API_KEY, la app usa un cliente simulado con guion fijo.")
    modo = st.radio("Modo de operación", MODOS, index=1, horizontal=True)
    st.caption(f"Trazas en LangSmith: {'activas, proyecto ' + os.environ.get('LANGSMITH_PROJECT', 'default') if tracing_is_enabled() else 'apagadas'}")
    if st.button("Reiniciar sesión") or st.session_state.get("claude") != usar_claude:
        cliente = wrap_anthropic(anthropic.Anthropic()) if usar_claude else ClienteSimulado()
        st.session_state.update(sistema=Sistema(cliente), claude=usar_claude, ultima=None, filas=None, revisiones=0)

s: Sistema = st.session_state.sistema
s.modo = modo
SKUS = ["SKU-900", "SKU-901", "SKU-902", "SKU-903", "SKU-999", *list(CATALOGO)[:100]]



def mostrar_traza(sku, traza):
    st.code(f"chain  agente_reposicion({sku})", language=None)
    for paso in traza:
        extra = f"{paso['tokens']:,} tokens" if paso["tokens"] else ""
        with st.expander(f"{'ERROR ' if paso['error'] else ''}{paso['tipo']} {paso['nombre']}  {paso['ms']} ms  {extra}"):
            st.write("Entrada:", paso["entrada"])
            (st.error if paso["error"] else st.write)(f"Salida: {paso['salida']}")


st.title("Agente de reposición con trazas")
st.caption("Distribuidora Austral (datos ficticios). Misiones de la clase 9 en una interfaz.")
t1, t2, t3, t4, t5 = st.tabs(["1 Política", "2 Agente y traza", "3 Órdenes y HITL", "4 Tokens y costo", "5 Evaluación"])

with t1:
    st.subheader("La política como compuerta")
    st.write("Toda orden pasa por `revisar_politica` antes de existir. El código impone la regla, no el prompt.")
    c1, c2 = st.columns(2)
    sku = c1.selectbox("SKU", [k for k in SKUS if k in CATALOGO], key="pol_sku")
    cantidad = c2.number_input("Cantidad", min_value=0, max_value=10_000, value=470, step=10)
    p = CATALOGO[sku]
    prov = PROVEEDORES[p["proveedor"]]
    st.write(f"{p['nombre']} | {pesos(p['precio'])} por unidad | proveedor {prov['nombre']} ({prov['estado']})")
    bloqueos, aprobacion = revisar_politica(sku, cantidad)
    monto = cantidad * p["precio"]
    if bloqueos:
        st.error("BLOQUEADO: " + "; ".join(bloqueos))
    elif aprobacion:
        st.warning(f"Requiere aprobación humana: {pesos(monto)} supera el umbral de {pesos(UMBRAL_APROBACION)}.")
    else:
        st.success(f"Permitido: {pesos(monto)}.")

with t2:
    st.subheader("Loop ReAct y su traza")
    st.write("El modelo pide una herramienta; `ejecutar_herramienta` decide si la ejecuta. La respuesta final se valida con Pydantic.")
    sku = st.selectbox("SKU a revisar (SKU-999 no existe)", SKUS, key="ag_sku")
    if st.button("Ejecutar agente", type="primary"):
        with st.spinner("El agente trabaja..."):
            try:
                salida, pasos = s.revisar(sku)
            except anthropic.APIError as error:
                st.error(f"La API falló ({type(error).__name__}). Cambio a modo simulado.")
                s.cliente = ClienteSimulado()
                salida, pasos = s.revisar(sku)
        st.session_state.ultima = (sku, salida, pasos, list(s.traza))
        st.session_state.revisiones += 1
    if st.session_state.ultima:
        sku, salida, pasos, traza = st.session_state.ultima
        izq, der = st.columns(2)
        with izq:
            st.markdown(f"**Salida estándar** ({pasos} vueltas, modo {s.modo})")
            st.json(salida.model_dump())
        with der:
            st.markdown("**Árbol de la traza**")
            mostrar_traza(sku, traza)
            if tracing_is_enabled():
                st.caption("La misma traza está en smith.langchain.com, Tracing, con la etiqueta `app`.")

with t3:
    st.subheader("Modos, idempotencia y aprobación humana")
    st.write("SIMULATE no guarda nada. SAFE deja borradores. LIVE envía si la política lo permite y el monto no supera el umbral.")
    if s.ordenes:
        st.dataframe([{"clave": k, **o} for k, o in s.ordenes.items()], width="stretch")
    else:
        st.info("No hay órdenes. Ejecuta el agente en modo SAFE o LIVE.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Idempotencia**")
        if s.ordenes and st.button("Reintentar la última orden"):
            o = list(s.ordenes.values())[-1]
            st.write(s.crear_orden_compra(o["sku"], o["cantidad"], "Reintento tras un corte de red"))
    with c2:
        st.markdown("**HITL** (*human in the loop*)")
        borradores = [k for k, o in s.ordenes.items() if o["estado"] == "borrador"]
        if borradores:
            clave = st.selectbox("Borrador", borradores)
            if st.button("El agente intenta aprobar"):
                st.error(s.ejecutar_herramienta("aprobar_orden", {"clave": clave, "comprador": "agente"})[0])
            comprador = st.text_input("Comprador", "jefa de compras")
            if st.button("Aprobar como humano"):
                st.success(s.aprobar_orden(clave, comprador))
                st.rerun()
        else:
            st.caption("Sin borradores por aprobar.")

with t4:
    st.subheader("Tokens, caché y costo")
    st.write("El catálogo va en el prompt de sistema con `cache_control`. La primera llamada escribe la caché; las siguientes la leen a menor costo.")
    if not usar_claude:
        st.caption("Modo simulado: tokens estimados, solo para ilustrar.")
    st.dataframe([{"campo": c, "tokens": n} for c, n in s.uso.items()], hide_index=True)
    n = st.session_state.revisiones or 1
    for etiqueta, con_cache in [("con caché", True), ("sin caché", False)]:
        por_revision = costo_usd(s.uso, con_cache) / n
        st.metric(f"Costo {etiqueta}", f"USD {por_revision:.5f} por revisión",
                  f"USD {por_revision * len(CATALOGO) * 30:,.2f} al mes ({len(CATALOGO)} SKU al día)", delta_color="off")

with t5:
    st.subheader("Evaluación y decisión go/no-go")
    st.write("Cinco casos con resultado conocido, en modo LIVE. La política exige 100 %; el acierto, el umbral.")
    umbral = st.slider("Umbral de acierto", 0.5, 1.0, 0.9, 0.05)
    if st.button("Correr evaluación", type="primary"):
        s.modo, s.ordenes = "LIVE", {}
        with st.spinner("Evaluando cinco casos..."):
            st.session_state.filas = evaluar(s, CASOS)
        st.session_state.revisiones += len(CASOS)
    if st.session_state.filas:
        filas = st.session_state.filas
        st.dataframe([{k: v for k, v in f.items() if k not in ("salida", "traza")} for f in filas], width="stretch")
        decision, acierto = decidir_go(filas, umbral)
        (st.success if decision == "GO" else st.error)(f"Acierto {acierto:.0%}. Decisión: {decision}")
        st.markdown("**Detalle por caso**")
        i = st.radio("Caso", range(len(filas)), horizontal=True,
                     format_func=lambda i: f"{i + 1}. {filas[i]['caso']} ({'acierto' if filas[i]['acierto'] else 'falla'})")
        f = filas[i]
        c = st.columns(4)
        c[0].metric("Esperado", f["esperado"])
        c[1].metric("Obtenido", f["accion"])
        c[2].metric("Política", "cumple" if f["politica"] else "falla")
        c[3].metric("Pasos", f["pasos"], f"{f['segundos']} s", delta_color="off")
        izq, der = st.columns(2)
        with izq:
            st.markdown("**Salida estándar**")
            st.json(f["salida"])
        with der:
            st.markdown("**Árbol de la traza**")
            mostrar_traza(f["sku"], f["traza"])

st.divider()
st.caption(f"Inventario: {len(INVENTARIO)} SKU. Un agente sin trazas no se puede auditar; sin evaluación, no se promueve a LIVE.")
