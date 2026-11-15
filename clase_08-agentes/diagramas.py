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
NB = Path(__file__).parent / "clase_08-lab_agentes.ipynb"
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
            bbox=dict(fc="white", ec="none", pad=1),
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
        ("1 Regla", "¿Agente o\nautomatización?"),
        ("2 Camino (a)", "El modelo clasifica,\nlas reglas deciden"),
        ("3 Camino (b)", "El modelo elige,\nel código limita"),
        ("4 Comparar", "Mismos tickets,\nambos caminos"),
        ("5 Control", "Kill switch\ny HITL"),
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
        nota(ax, 5, 2.0, "Los mismos cinco tickets de Tienda Andina recorren todo el laboratorio", size=10)
    guardar(fig, f"mapa_mision_{activo}.png" if activo else "mapa_clase.png")


def regla():
    fig, ax = lienzo(10, 3.4)
    preguntas = [
        "¿Hay ambigüedad\nen la entrada?",
        "¿Se necesita razonamiento\ncontextual?",
        "¿Las excepciones\nson frecuentes?",
    ]
    for i, p in enumerate(preguntas):
        caja(ax, 0.1, 2.35 - i * 1.05, 2.6, 0.8, p, C["gris"], C["claro"], 9)
        flecha(ax, (2.7, 2.75 - i * 1.05), (3.6, 1.7))
    caja(ax, 3.6, 1.2, 2.0, 1.0, "Cuenta los SÍ", C["azul"], C["azul_claro"], 10, True)
    salidas = [
        ("0 SÍ", "Automatización\nreglas if/else", C["verde"], C["verde_claro"]),
        ("1 SÍ", "Híbrido\nel modelo propone,\nel código ejecuta", C["azul"], C["azul_claro"]),
        ("2 o 3 SÍ", "Agente con\nautonomía controlada", C["rojo"], C["rojo_claro"]),
    ]
    for i, (n, t, col, rel) in enumerate(salidas):
        y = 2.35 - i * 1.05
        caja(ax, 7.0, y, 2.9, 0.8, t, col, rel, 9)
        flecha(ax, (5.6, 1.7), (7.0, y + 0.4), n, col, dy=0.08)
    nota(ax, 5, 3.25, "Si puedes escribir los if, escríbelos", C["gris"], 10, weight="bold")
    guardar(fig, "regla.png")


def espectro():
    fig, ax = lienzo(10, 2.9)
    niveles = [
        ("Automatización\npura", "Solo reglas.\nSin modelo.", C["gris"], None),
        ("(a) Automatización con\ncomponente agéntico", "El modelo lee texto;\nlas reglas deciden.", C["verde"], C["verde_claro"]),
        ("(b) Agente con\nautonomía controlada", "El modelo elige\nherramientas; el código\npone límites.", C["rojo"], C["rojo_claro"]),
        ("Agente\nautónomo", "Sin límites duros.\nNo lo usamos aquí.", C["gris"], None),
    ]
    for i, (t, d, col, rel) in enumerate(niveles):
        x = 0.1 + i * 2.5
        caja(ax, x, 0.75, 2.2, 1.55, f"{t}\n\n{d}", col, rel, 8.5)
    flecha(ax, (0.2, 0.35), (9.7, 0.35), color=C["azul"])
    nota(ax, 1.4, 0.05, "más control, menos costo", C["azul"])
    nota(ax, 8.5, 0.05, "más flexibilidad, más riesgo", C["azul"])
    nota(ax, 5, 2.55, "Este laboratorio compara los dos niveles del centro", size=10)
    guardar(fig, "espectro.png")


def camino_a():
    fig, ax = lienzo(10, 2.6)
    caja(ax, 0.1, 0.8, 1.6, 0.9, "Ticket\n(texto libre)", C["gris"])
    caja(ax, 2.4, 0.8, 2.2, 0.9, "Claude clasifica\n1 llamada, formato fijo", C["azul"], C["azul_claro"], 9)
    caja(ax, 5.3, 0.8, 2.0, 0.9, "Reglas en Python\ndecidir()", C["verde"], C["verde_claro"], 9)
    caja(ax, 8.1, 1.45, 1.8, 0.7, "Acción\nautomática", C["verde"], size=9)
    caja(ax, 8.1, 0.25, 1.8, 0.7, "Derivar a\nhumano", C["rojo"], size=9)
    flecha(ax, (1.7, 1.25), (2.4, 1.25))
    flecha(ax, (4.6, 1.25), (5.3, 1.25))
    nota(ax, 4.95, 1.75, "datos", C["azul"])
    flecha(ax, (7.3, 1.4), (8.1, 1.8), color=C["verde"])
    nota(ax, 7.3, 2.0, "regla aplica", C["verde"])
    flecha(ax, (7.3, 1.1), (8.1, 0.6), color=C["rojo"])
    nota(ax, 7.2, 0.35, "ninguna aplica", C["rojo"])
    nota(ax, 3.5, 0.45, "El modelo no ejecuta nada", C["azul"])
    nota(ax, 5, 2.35, "Camino (a): el modelo solo traduce texto a datos", size=10, weight="bold")
    guardar(fig, "camino_a.png")


def camino_b():
    fig, ax = lienzo(10, 4.2)
    caja(ax, 0.1, 1.7, 1.5, 0.9, "Ticket", C["gris"])
    caja(ax, 2.3, 1.7, 2.0, 0.9, "Claude elige\nla herramienta", C["azul"], C["azul_claro"], 9)
    caja(ax, 5.0, 1.7, 2.1, 0.9, "Guardrails\nen el código", C["rojo"], C["rojo_claro"], 9, True)
    caja(ax, 7.8, 1.7, 2.1, 0.9, "Ejecuta la\nherramienta", C["verde"], C["verde_claro"], 9)
    flecha(ax, (1.6, 2.15), (2.3, 2.15))
    flecha(ax, (4.3, 2.15), (5.0, 2.15), "tool_use")
    flecha(ax, (7.1, 2.15), (7.8, 2.15))
    flecha(ax, (8.85, 1.7), (3.3, 1.7), "tool_result: el resultado vuelve al modelo", C["verde"], curva=-0.35, dy=-1.15)
    caja(ax, 4.6, 3.15, 2.9, 0.85, "Lista permitida · Límite de pasos\nHITL sobre el umbral · Kill switch", C["rojo"], size=8.5)
    flecha(ax, (6.05, 3.15), (6.05, 2.6), color=C["rojo"])
    caja(ax, 7.8, 3.15, 2.1, 0.85, "Bitácora\n(cada llamada)", C["gris"], C["claro"], 9)
    flecha(ax, (8.85, 2.6), (8.85, 3.15))
    caja(ax, 0.1, 3.15, 3.4, 0.85, "Termina: respuesta al cliente,\nescala o se detiene", C["azul"], size=9)
    flecha(ax, (3.0, 2.6), (2.2, 3.15), "end_turn", C["azul"], dy=0.05)
    guardar(fig, "camino_b.png")


def hibrido():
    fig, ax = lienzo(10, 3.3)
    caja(ax, 0.1, 1.3, 1.4, 0.8, "Ticket", C["gris"])
    caja(ax, 2.1, 1.3, 2.0, 0.8, "Camino (a)\nclasifica + reglas", C["verde"], C["verde_claro"], 9)
    caja(ax, 4.9, 2.3, 2.0, 0.75, "Acción automática\n1 llamada", C["verde"], size=9)
    caja(ax, 4.9, 0.3, 2.0, 0.8, "Camino (b)\nagente con límites", C["rojo"], C["rojo_claro"], 9)
    caja(ax, 7.7, 1.15, 2.2, 0.75, "Respuesta con\ncontexto", C["azul"], size=9)
    caja(ax, 7.7, 0.05, 2.2, 0.75, "Supervisor\n(HITL)", C["rojo"], size=9)
    flecha(ax, (1.5, 1.7), (2.1, 1.7))
    flecha(ax, (4.1, 1.9), (4.9, 2.65), color=C["verde"])
    nota(ax, 3.9, 2.45, "regla aplica", C["verde"])
    flecha(ax, (4.1, 1.5), (4.9, 0.7), color=C["rojo"])
    nota(ax, 3.95, 0.85, "derivar", C["rojo"])
    flecha(ax, (6.9, 0.85), (7.7, 1.5))
    flecha(ax, (6.9, 0.55), (7.7, 0.4))
    nota(ax, 5, 3.15, "Híbrido: lo estándar por reglas, lo ambiguo por el agente", size=10, weight="bold")
    guardar(fig, "hibrido.png")


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
    ruta.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return n


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for f in (mapa_clase, regla, espectro, camino_a, camino_b, hibrido):
        f()
    for m in range(1, 6):
        mapa_clase(m)
    print(f"{len(list(OUT.glob('*.png')))} diagramas en {OUT}")
    print(f"{incrustar(NB)} imágenes incrustadas en {NB.name}")
