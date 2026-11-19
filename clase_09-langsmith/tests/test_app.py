import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from agente import ClienteSimulado, Sistema, costo_usd, decidir_go, evaluar
from datos import CASOS


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["nombre"])
def test_casos_live(caso):
    s = Sistema(ClienteSimulado(), modo="LIVE")
    salida, _ = s.revisar(caso["sku"])
    assert salida.action == caso["esperado"]
    assert [p["tipo"] for p in s.traza][:2] == ["llm", "tool"]


def test_modos_idempotencia_y_hitl():
    for modo, accion, n in [("SIMULATE", "orden_simulada", 0), ("SAFE", "orden_borrador", 1), ("LIVE", "orden_enviada", 1)]:
        s = Sistema(ClienteSimulado(), modo=modo)
        assert s.revisar("SKU-900")[0].action == accion and len(s.ordenes) == n
    assert s.crear_orden_compra("SKU-900", 470, "reintento").startswith("Sin cambios") and len(s.ordenes) == 1
    s.revisar("SKU-902")
    assert s.ordenes["SKU-902-2200"]["estado"] == "borrador"
    assert s.ejecutar_herramienta("aprobar_orden", {"clave": "SKU-902-2200", "comprador": "agente"})[1] is True
    s.aprobar_orden("SKU-902-2200", "jefa de compras")
    assert s.ordenes["SKU-902-2200"]["estado"] == "enviada"


def test_cache_abarata_y_evaluacion_go():
    s = Sistema(ClienteSimulado(), modo="LIVE")
    filas = evaluar(s, CASOS)
    assert decidir_go(filas)[0] == "GO"
    assert s.uso["cache_read_input_tokens"] > s.uso["cache_creation_input_tokens"]
    assert costo_usd(s.uso) < costo_usd(s.uso, con_cache=False)


def test_evaluacion_guarda_detalle_por_caso():
    filas = evaluar(Sistema(ClienteSimulado(), modo="LIVE"), CASOS)
    for f in filas:
        assert f["salida"]["action"] == f["accion"]
        assert f["traza"][0]["tipo"] == "llm" and f["traza"][-1]["nombre"] == "entregar_respuesta"
