"""Genera los diagramas del laboratorio en img/ y los incrusta en el notebook. Uso: uv run python diagramas.py"""

import base64
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

C = {
    "verde": "#2C5F2D",
    "azul": "#065A82",
    "rojo": "#B85042",
    "gris": "#5C6670",
    "claro": "#EEF2F6",
    "verde_claro": "#E8F1E8",
    "rojo_claro": "#F7EAE7",
    "azul_claro": "#E6EFF5",
}
OUT = Path(__file__).parent / "img"
NB = Path(__file__).parent / "clase_09-lab_langsmith.ipynb"
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 10,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "text.parse_math": False,  # los "$" son pesos, no LaTeX
    }
)


def lienzo(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set(xlim=(0, w), ylim=(0, h))
    ax.axis("off")
    return fig, ax


def caja(ax, x, y, w, h, texto, color=C["azul"], relleno=None, size=10, bold=False):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            fc=relleno or "white",
            ec=color,
            lw=1.8,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        texto,
        ha="center",
        va="center",
        fontsize=size,
        color="#1A1A1A",
        weight="bold" if bold else "normal",
    )


def flecha(ax, a, b, texto="", color=C["gris"], curva=0.0, dy=0.12):
    ax.add_patch(
        FancyArrowPatch(
            a,
            b,
            arrowstyle="-|>",
            mutation_scale=14,
            color=color,
            lw=1.5,
            connectionstyle=f"arc3,rad={curva}",
        )
    )
    if texto:
        ax.text(
            (a[0] + b[0]) / 2,
            (a[1] + b[1]) / 2 + dy,
            texto,
            ha="center",
            fontsize=9,
            color=color,
            bbox={"fc": "white", "ec": "none", "pad": 1},
        )


def nota(ax, x, y, texto, color=C["gris"], size=9, **kw):
    ax.text(x, y, texto, ha="center", color=color, fontsize=size, **kw)


def guardar(fig, nombre):
    fig.savefig(OUT / nombre, facecolor="white")
    plt.close(fig)


def mapa_clase(activo=None):
    """Sin `activo`: mapa general. Con `activo` (1 a 5): resalta esa misión."""
    fig, ax = lienzo(10, 2.2)
    pasos = [
        ("1 Herramientas", "Contratos y\npolítica en código"),
        ("2 Agente", "Loop ReAct\ny su traza"),
        ("3 Modos", "Tres modos e\nidempotencia"),
        ("4 Costo", "Tokens\ny caché"),
        ("5 Evaluación", "Casos, métricas\ny go/no-go"),
    ]
    for i, (t, d) in enumerate(pasos):
        x = 0.1 + i * 2
        texto = f"{t}\n\n{d}"
        if activo is None:
            caja(ax, x, 0.35, 1.6, 1.3, texto, size=9)
        elif i + 1 == activo:
            caja(ax, x, 0.35, 1.6, 1.3, texto, C["rojo"], C["rojo_claro"], 9)
            nota(ax, x + 0.8, 1.85, "Ustedes están aquí", C["rojo"], 10, weight="bold")
        else:
            col = C["gris"] if i + 1 > activo else C["verde"]
            caja(ax, x, 0.35, 1.6, 1.3, texto, col, size=9)
        if i:
            flecha(ax, (x - 0.38, 1.0), (x - 0.02, 1.0))
    if activo is None:
        nota(
            ax,
            5,
            2.0,
            "Un agente de reposición de Distribuidora Austral, observable de punta a punta",
            size=10,
        )
    guardar(fig, f"mapa_mision_{activo}.png" if activo else "mapa_clase.png")


def politica():
    fig, ax = lienzo(10, 3.65)
    caja(
        ax,
        0.1,
        1.3,
        2.0,
        0.9,
        "El agente pide\ncrear_orden_compra",
        C["azul"],
        C["azul_claro"],
        9,
    )
    caja(
        ax,
        2.9,
        1.3,
        2.2,
        0.9,
        "revisar_politica\n(código Python)",
        C["rojo"],
        C["rojo_claro"],
        9,
        True,
    )
    flecha(ax, (2.1, 1.75), (2.9, 1.75))
    salidas = [
        (
            "bloqueo",
            "RECHAZADO\nproveedor bloqueado o\ncantidad fuera de rango",
            C["rojo"],
            C["rojo_claro"],
            2.3,
        ),
        (
            "monto alto",
            "Borrador\nun comprador aprueba\n(HITL)",
            C["azul"],
            C["azul_claro"],
            1.25,
        ),
        (
            "todo en regla",
            "Orden creada\nsegún el modo\n(misión 3)",
            C["verde"],
            C["verde_claro"],
            0.2,
        ),
    ]
    for t, d, col, rel, y in salidas:
        caja(ax, 6.9, y, 3.0, 0.85, d, col, rel, 8.5)
        flecha(ax, (5.1, 1.75), (6.9, y + 0.42), t, col, dy=0.06)
    nota(
        ax,
        5,
        3.5,
        "El prompt explica la política; el código la impone",
        size=10,
        weight="bold",
    )
    guardar(fig, "politica.png")


def loop_react():
    fig, ax = lienzo(10, 4.2)
    caja(ax, 0.1, 1.7, 1.5, 0.9, "SKU a\nrevisar", C["gris"])
    caja(
        ax,
        2.3,
        1.7,
        2.0,
        0.9,
        "Claude razona\ny elige herramienta",
        C["azul"],
        C["azul_claro"],
        9,
    )
    caja(
        ax,
        5.0,
        1.7,
        2.1,
        0.9,
        "ejecutar_herramienta\n(lista permitida)",
        C["rojo"],
        C["rojo_claro"],
        9,
    )
    caja(
        ax,
        7.8,
        1.7,
        2.1,
        0.9,
        "Herramienta\n@traceable",
        C["verde"],
        C["verde_claro"],
        9,
    )
    flecha(ax, (1.6, 2.15), (2.3, 2.15))
    flecha(ax, (4.3, 2.15), (5.0, 2.15), "tool_use")
    flecha(ax, (7.1, 2.15), (7.8, 2.15))
    flecha(
        ax,
        (8.85, 1.7),
        (3.3, 1.7),
        "tool_result: observa y repite",
        C["verde"],
        curva=-0.35,
        dy=-1.15,
    )
    caja(
        ax,
        0.1,
        3.2,
        3.0,
        0.85,
        "entregar_respuesta\nanswer, action, evidence,\nconfidence, next_step",
        C["azul"],
        size=8.5,
    )
    flecha(ax, (3.0, 2.6), (2.4, 3.2), color=C["azul"])
    caja(
        ax,
        4.0,
        3.2,
        2.4,
        0.85,
        "Pydantic valida\nla salida",
        C["rojo"],
        C["rojo_claro"],
        9,
    )
    flecha(ax, (3.1, 3.62), (4.0, 3.62))
    caja(
        ax,
        7.3,
        3.2,
        2.6,
        0.85,
        "Si no cumple, el error\nvuelve al modelo",
        C["gris"],
        C["claro"],
        8.5,
    )
    flecha(ax, (6.4, 3.62), (7.3, 3.62))
    nota(
        ax,
        5,
        0.05,
        "Máximo 8 vueltas; al llegar al límite, el agente escala a un analista",
        C["gris"],
        9,
    )
    guardar(fig, "loop_react.png")


def arbol_traza():
    fig, ax = lienzo(10, 4.0)
    filas = [
        (
            0,
            "chain",
            "agente_reposicion",
            "raíz: entrada SKU-900, salida estándar",
            C["azul"],
        ),
        (1, "llm", "ChatAnthropic", "vuelta 1: tokens, latencia, costo", C["gris"]),
        (
            1,
            "tool",
            "consultar_inventario",
            "entrada y salida de la herramienta",
            C["verde"],
        ),
        (1, "llm", "ChatAnthropic", "vuelta 2", C["gris"]),
        (
            1,
            "tool",
            "calcular_reposicion",
            "la cantidad la calcula el código",
            C["verde"],
        ),
        (1, "llm", "ChatAnthropic", "...", C["gris"]),
        (1, "tool", "crear_orden_compra", "resultado de la política", C["verde"]),
        (1, "llm", "ChatAnthropic", "última vuelta: entregar_respuesta", C["gris"]),
    ]
    for i, (nivel, tipo, nombre, desc, col) in enumerate(filas):
        y = 3.4 - i * 0.45
        x = 0.3 + nivel * 0.7
        if nivel:
            ax.plot(
                [0.55, 0.55, x],
                [y + 0.45 if i == 1 else y + 0.22, y, y],
                color=C["gris"],
                lw=1,
            )
        caja(ax, x, y - 0.17, 0.8, 0.34, tipo, col, size=8)
        ax.text(
            x + 1.0,
            y,
            nombre,
            va="center",
            fontsize=9.5,
            weight="bold",
            color="#1A1A1A",
        )
        ax.text(5.2, y, desc, va="center", fontsize=9, color=col)
    nota(
        ax,
        5,
        3.8,
        "Una traza es un árbol: la cadena principal y cada paso con su entrada, salida y costo",
        size=10,
        weight="bold",
    )
    guardar(fig, "arbol_traza.png")


def modos():
    fig, ax = lienzo(10, 3.35)
    caja(
        ax,
        0.1,
        1.05,
        2.0,
        0.9,
        "crear_orden_compra\npasa la política",
        C["azul"],
        C["azul_claro"],
        9,
    )
    datos = [
        (
            "SIMULATE",
            "Informa qué haría.\nNo guarda nada.",
            "pruebas y demos",
            C["gris"],
            C["claro"],
            2.0,
        ),
        (
            "SAFE",
            "Guarda un borrador.\nUn humano lo envía.",
            "primeras semanas",
            C["azul"],
            C["azul_claro"],
            1.05,
        ),
        (
            "LIVE",
            "Envía la orden, salvo\nmontos sobre el umbral.",
            "con métricas a favor",
            C["verde"],
            C["verde_claro"],
            0.1,
        ),
    ]
    for t, d, cuando, col, rel, y in datos:
        caja(ax, 3.4, y, 1.4, 0.8, t, col, rel, 10, True)
        caja(ax, 5.2, y, 2.6, 0.8, d, col, size=8.5)
        ax.text(8.0, y + 0.4, cuando, va="center", fontsize=9, color=col)
        flecha(ax, (2.1, 1.5), (3.4, y + 0.4), color=col)
        flecha(ax, (4.8, y + 0.4), (5.2, y + 0.4), color=col)
    nota(
        ax,
        5,
        3.2,
        "Más autonomía solo cuando las trazas y la evaluación lo justifican",
        size=10,
        weight="bold",
    )
    guardar(fig, "modos.png")


def cache():
    fig, ax = lienzo(10, 3.2)
    llamadas = ["Llamada 1", "Llamada 2", "Llamada 3", "Llamada 4"]
    for i, t in enumerate(llamadas):
        y = 2.3 - i * 0.6
        ax.text(0.1, y + 0.2, t, va="center", fontsize=9)
        col, rel, txt = (
            (C["rojo"], C["rojo_claro"], "escribe caché (1,25x)")
            if i == 0
            else (C["verde"], C["verde_claro"], "lee caché (0,1x)")
        )
        caja(ax, 1.4, y, 4.6, 0.4, f"Instrucciones + catálogo: {txt}", col, rel, 8.5)
        caja(ax, 6.1, y, 1.2 + i * 0.6, 0.4, "historial", C["gris"], C["claro"], 8)
    ax.plot([6.05, 6.05], [0.35, 2.85], color=C["azul"], lw=1.5, ls="--")
    nota(ax, 6.05, 2.95, "cache_control", C["azul"], 9)
    nota(
        ax,
        3.7,
        0.05,
        "Prefijo estable: se cobra completo solo una vez cada 5 minutos",
        C["verde"],
        9,
    )
    nota(ax, 8.4, 0.05, "Lo nuevo se cobra a precio normal", C["gris"], 9)
    guardar(fig, "cache.png")


def evaluacion():
    fig, ax = lienzo(10, 2.8)
    caja(
        ax,
        0.1,
        0.9,
        1.8,
        1.0,
        "Casos con\nresultado\nesperado",
        C["gris"],
        C["claro"],
        9,
    )
    caja(ax, 2.6, 0.9, 1.8, 1.0, "Agente en\nmodo LIVE", C["azul"], C["azul_claro"], 9)
    caja(
        ax,
        5.1,
        0.9,
        2.1,
        1.0,
        "Métricas\nacierto, política,\nevidencia, pasos",
        C["verde"],
        C["verde_claro"],
        9,
    )
    caja(ax, 7.9, 1.45, 2.0, 0.6, "GO", C["verde"], C["verde_claro"], 10, True)
    caja(ax, 7.9, 0.55, 2.0, 0.6, "NO-GO", C["rojo"], C["rojo_claro"], 10, True)
    flecha(ax, (1.9, 1.4), (2.6, 1.4))
    flecha(ax, (4.4, 1.4), (5.1, 1.4))
    flecha(ax, (7.2, 1.5), (7.9, 1.75), color=C["verde"])
    flecha(ax, (7.2, 1.3), (7.9, 0.85), color=C["rojo"])
    nota(ax, 3.5, 0.45, "cada caso deja una traza\ncon la etiqueta eval", C["azul"])
    nota(
        ax,
        5,
        2.5,
        "Umbrales fijados antes de mirar los resultados",
        size=10,
        weight="bold",
    )
    guardar(fig, "evaluacion.png")


def incrustar(ruta):
    """Copia cada PNG citado en el notebook dentro de la celda (adjunto), así Colab no necesita img/."""
    nb = json.loads(ruta.read_text(encoding="utf-8"))
    n = 0
    for celda in nb["cells"]:
        if celda["cell_type"] != "markdown":
            continue
        texto = "".join(celda["source"]).replace("](img/", "](attachment:")
        nombres = re.findall(r"\]\(attachment:([\w.]+\.png)\)", texto)
        if not nombres:
            continue
        celda["source"] = texto.splitlines(keepends=True)
        celda["attachments"] = {
            x: {"image/png": base64.b64encode((OUT / x).read_bytes()).decode()}
            for x in nombres
        }
        n += len(nombres)
    ruta.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return n


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for f in (mapa_clase, politica, loop_react, arbol_traza, modos, cache, evaluacion):
        f()
    for m in range(1, 6):
        mapa_clase(m)
    print(f"{len(list(OUT.glob('*.png')))} diagramas en {OUT}")
    print(f"{incrustar(NB)} imágenes incrustadas en {NB.name}")
