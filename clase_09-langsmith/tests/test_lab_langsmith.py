import json
import re
from types import SimpleNamespace
from typing import Literal

import pytest
from langsmith import traceable
from nb import load
from pydantic import BaseModel, Field, ValidationError

NB = "clase_09-lab_langsmith.ipynb"
DATA = load(
    NB, "PROVEEDORES", "FAMILIAS", "CATALOGO", "INVENTARIO", "pesos", "HORIZONTE_DIAS"
)


def lab(modo="SAFE"):
    """Load the agent pieces with fresh state."""
    ns = load(
        NB,
        "consultar_inventario",
        "calcular_reposicion",
        "consultar_proveedor",
        "MAX_UNIDADES",
        "UMBRAL_APROBACION",
        "ORDENES",
        "revisar_politica",
        "crear_orden_compra",
        "herramienta",
        "TEXTO",
        "ENTERO",
        "ACCIONES_FINALES",
        "HERRAMIENTAS",
        "RespuestaAgente",
        "ACCIONES",
        "ejecutar_herramienta",
        "SISTEMA",
        "MAX_PASOS",
        "USO",
        "sumar_uso",
        "resumir_y_escalar",
        "agente_reposicion",
        "GUION",
        "accion_desde",
        "ClienteSimulado",
        "CASOS",
        "cumple_politica",
        "UMBRAL_ACIERTO",
        "decidir_go",
        json=json,
        re=re,
        SimpleNamespace=SimpleNamespace,
        Literal=Literal,
        BaseModel=BaseModel,
        Field=Field,
        ValidationError=ValidationError,
        traceable=traceable,
        MODELO="test",
        INSTRUCCIONES="test",
        CATALOGO_TEXTO="test",
        MODO=modo,
        **DATA,
    )
    return ns


def test_reposicion_la_calcula_el_codigo():
    r = lab()["calcular_reposicion"]("SKU-900", 14)
    assert r["cantidad_sugerida"] == 30 * (14 + 3) - 40
    assert lab()["calcular_reposicion"]("SKU-903", 14)["cantidad_sugerida"] == 0


def test_politica_bloquea_proveedor_y_pide_aprobacion():
    ns = lab()
    assert ns["revisar_politica"]("SKU-901", 220)[0]
    assert ns["revisar_politica"]("SKU-902", 2_200) == ([], True)
    assert ns["crear_orden_compra"]("SKU-901", 220, "x").startswith("RECHAZADO")


@pytest.mark.parametrize(
    ("modo", "estado"), [("SIMULATE", None), ("SAFE", "borrador"), ("LIVE", "enviada")]
)
def test_modos(modo, estado):
    ns = lab(modo)
    ns["crear_orden_compra"]("SKU-900", 470, "x")
    assert [o["estado"] for o in ns["ORDENES"].values()] == ([estado] if estado else [])


def test_live_sobre_umbral_queda_en_borrador():
    ns = lab("LIVE")
    ns["crear_orden_compra"]("SKU-902", 2_200, "x")
    assert ns["ORDENES"]["SKU-902-2200"]["estado"] == "borrador"


def test_idempotencia():
    ns = lab("LIVE")
    ns["crear_orden_compra"]("SKU-900", 470, "x")
    assert ns["crear_orden_compra"]("SKU-900", 470, "x").startswith("Sin cambios")
    assert len(ns["ORDENES"]) == 1


def test_herramienta_no_permitida_y_sku_inexistente():
    ns = lab()
    assert ns["ejecutar_herramienta"]("borrar_base", {})[1]
    assert ns["ejecutar_herramienta"]("consultar_inventario", {"sku": "SKU-X"})[1]


def test_sku_inexistente_escala():
    ns = lab()
    salida, _ = ns["agente_reposicion"]("SKU-999", ns["ClienteSimulado"]())
    assert salida.action == "escalado"


def test_solo_un_humano_aprueba_montos_altos():
    ns = lab("LIVE")
    ns["crear_orden_compra"]("SKU-902", 2_200, "x")
    assert ns["ejecutar_herramienta"]("aprobar_orden", {})[1]
    ns["ORDENES"]["SKU-902-2200"]["estado"] = "enviada"
    assert not ns["cumple_politica"]()
    ns["ORDENES"]["SKU-902-2200"]["aprobada_por"] = "comprador"
    assert ns["cumple_politica"]()


def test_salida_estandar_exige_evidencia():
    with pytest.raises(ValidationError):
        lab()["RespuestaAgente"](
            answer="x",
            action="sin_accion",
            evidence=["uno"],
            confidence=0.5,
            next_step="y",
        )


def test_evaluacion_simulada_da_go():
    ns = lab("LIVE")
    filas = []
    for caso in ns["CASOS"]:
        salida, _ = ns["agente_reposicion"](caso["sku"], ns["ClienteSimulado"]())
        filas.append(
            {
                "acierto": salida.action == caso["esperado"],
                "politica": ns["cumple_politica"](),
                "evidencia": len(salida.evidence) >= 2,
            }
        )
    assert ns["decidir_go"](filas) == ("GO", 1.0)


def test_salida_invalida_vuelve_al_modelo_y_limite_escala():
    ns = lab()
    mala = SimpleNamespace(
        type="tool_use",
        id="x",
        name="entregar_respuesta",
        input={
            "answer": "x",
            "action": "sin_accion",
            "evidence": [],
            "confidence": 2,
            "next_step": "y",
        },
    )
    terco = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **_: SimpleNamespace(stop_reason="tool_use", content=[mala])
        )
    )
    salida, pasos = ns["agente_reposicion"]("SKU-900", terco)
    assert salida.action == "escalado" and pasos == ns["MAX_PASOS"]
