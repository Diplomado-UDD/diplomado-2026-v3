"""Capa de datos: Distribuidora Austral (datos ficticios, iguales al notebook)."""

MODELO = "claude-haiku-5-5"
HORIZONTE_DIAS = 14
MAX_UNIDADES = 5_000
UMBRAL_APROBACION = 2_000_000  # sobre este monto, un comprador humano aprueba (HITL)
MAX_PASOS = 8
MODOS = ["SIMULATE", "SAFE", "LIVE"]

PROVEEDORES = {
    "PR-01": {"nombre": "Agrícola Sur", "estado": "activo", "motivo": ""},
    "PR-02": {"nombre": "Lácteos del Lago", "estado": "activo", "motivo": ""},
    "PR-03": {"nombre": "Comercial Fiordos", "estado": "activo", "motivo": ""},
    "PR-09": {"nombre": "Importadora Pacífico", "estado": "bloqueado", "motivo": "tres entregas incompletas en 2026"},
}

FAMILIAS = ["Aceite", "Arroz", "Harina", "Azúcar", "Fideos", "Avena", "Lentejas", "Sal", "Detergente", "Papel higiénico"]

CATALOGO = {
    f"SKU-{i:03d}": {"nombre": f"{FAMILIAS[i % 10]} formato {i // 10 + 1}", "proveedor": f"PR-0{i % 3 + 1}",
                     "precio": 800 + 45 * i, "lead_time": 2 + i % 4}
    for i in range(100)
} | {
    "SKU-900": {"nombre": "Aceite maravilla 1 L", "proveedor": "PR-01", "precio": 2_500, "lead_time": 3},
    "SKU-901": {"nombre": "Café en grano 1 kg", "proveedor": "PR-09", "precio": 9_000, "lead_time": 10},
    "SKU-902": {"nombre": "Leche entera 1 L", "proveedor": "PR-02", "precio": 1_100, "lead_time": 2},
    "SKU-903": {"nombre": "Arroz grado 1, 1 kg", "proveedor": "PR-03", "precio": 1_300, "lead_time": 4},
}

INVENTARIO = {sku: {"stock": 300 + (i * 37) % 500, "consumo_diario": 5 + (i * 13) % 40} for i, sku in enumerate(CATALOGO)} | {
    "SKU-900": {"stock": 40, "consumo_diario": 30},
    "SKU-901": {"stock": 20, "consumo_diario": 10},
    "SKU-902": {"stock": 200, "consumo_diario": 150},
    "SKU-903": {"stock": 3_000, "consumo_diario": 20},
}

CASOS = [
    {"nombre": "camino feliz", "sku": "SKU-900", "esperado": "orden_enviada"},
    {"nombre": "proveedor bloqueado", "sku": "SKU-901", "esperado": "rechazado"},
    {"nombre": "monto sobre el umbral", "sku": "SKU-902", "esperado": "orden_borrador"},
    {"nombre": "stock suficiente", "sku": "SKU-903", "esperado": "sin_accion"},
    {"nombre": "SKU inexistente", "sku": "SKU-999", "esperado": "escalado"},
]

# USD por millón de tokens, Claude Haiku 5.5, precios de lista a noviembre de 2026 (mismos del notebook)
PRECIO_MTOK = {"input_tokens": 0.10, "cache_creation_input_tokens": 0.125,
               "cache_read_input_tokens": 0.01, "output_tokens": 0.50}


def pesos(monto):
    return f"${monto:,}".replace(",", ".")
