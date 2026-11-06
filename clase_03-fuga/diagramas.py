"""Genera los diagramas del laboratorio en img/ y los incrusta en el notebook. Uso: uv run python diagramas.py"""

import base64
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# Mismos supuestos que el notebook (celda de configuración)
LTV, COSTO_CUPON, TASA_RETENCION = 400_000, 60_000, 0.6

C = {
    "verde": "#2C5F2D",
    "azul": "#065A82",
    "rojo": "#B85042",
    "gris": "#5C6670",
    "claro": "#EEF2F6",
}
OUT = Path(__file__).parent / "img"
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.size": 10,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "text.parse_math": False,
    }
)  # los "$" son pesos, no LaTeX


def lienzo(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set(xlim=(0, w), ylim=(0, h))
    ax.axis("off")
    return fig, ax


def caja(ax, x, y, w, h, texto, color=C["azul"], relleno=None, size=10):
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
    )


def flecha(ax, a, b, texto="", color=C["gris"]):
    ax.add_patch(
        FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color=color, lw=1.5)
    )
    if texto:
        ax.text(
            (a[0] + b[0]) / 2,
            (a[1] + b[1]) / 2 + 0.12,
            texto,
            ha="center",
            fontsize=9,
            color=color,
        )


def guardar(fig, nombre):
    fig.savefig(OUT / nombre, facecolor="white")
    plt.close(fig)


def mapa_clase(activo=None):
    """Sin `activo`: mapa general. Con `activo` (1 a 5): resalta ese bloque («Ustedes están aquí»)."""
    fig, ax = lienzo(10, 2.2)
    pasos = [
        ("1 Diagnóstico", "¿Cuánto nos\ncuesta la fuga?"),
        ("2 Reglas", "SI pasa X,\nENTONCES cupón"),
        ("3 ML", "Probabilidad\nde fuga"),
        ("4 GenAI", "Qué decirle\na cada uno"),
        ("5 Decisión", "¿Qué conviene\nsegún tamaño?"),
    ]
    for i, (t, d) in enumerate(pasos):
        x = 0.1 + i * 2
        if activo is None:
            caja(ax, x, 0.35, 1.6, 1.3, f"{t}\n\n{d}", size=9)
        elif i + 1 == activo:
            caja(ax, x, 0.35, 1.6, 1.3, f"{t}\n\n{d}", C["rojo"], "#F7EAE7", 9)
            ax.text(
                x + 0.8,
                1.85,
                "Ustedes están aquí",
                ha="center",
                color=C["rojo"],
                weight="bold",
            )
        else:
            caja(
                ax,
                x,
                0.35,
                1.6,
                1.3,
                f"{t}\n\n{d}",
                C["gris"] if i + 1 > activo else C["verde"],
                size=9,
            )
        if i:
            flecha(ax, (x - 0.38, 1.0), (x - 0.02, 1.0))
    if activo is None:
        ax.text(
            5,
            2.0,
            "Del más simple al más complejo; siempre contra «no hacer nada»",
            ha="center",
            color=C["gris"],
        )
    guardar(fig, f"mapa_bloque_{activo}.png" if activo else "mapa_clase.png")


def train_test():
    fig, ax = lienzo(10, 1.9)
    caja(
        ax,
        0.1,
        0.5,
        6.9,
        0.8,
        "TRAIN: 350 clientes (70%)\nla «guía de estudio»: aquí calibramos todo",
        C["verde"],
        "#E8F1E8",
    )
    caja(
        ax,
        7.1,
        0.5,
        2.8,
        0.8,
        "TEST: 150 (30%)\nla «prueba»: se mira al final",
        C["rojo"],
        "#F7EAE7",
    )
    ax.text(
        5,
        1.6,
        "500 clientes, misma proporción de fuga (~20%) en ambos lados",
        ha="center",
        color=C["gris"],
    )
    guardar(fig, "train_test.png")


def matriz_costos():
    tp = COSTO_CUPON + (1 - TASA_RETENCION) * LTV
    celdas = [  # (fila, columna, sigla, texto, costo, color)
        (
            1,
            0,
            "TP",
            "Se iba y lo contactamos",
            f"${COSTO_CUPON:,.0f} cupón + 40% × ${LTV:,.0f}\n= ${tp:,.0f} esperado",
            C["verde"],
        ),
        (
            1,
            1,
            "FN",
            "Se iba y no lo vimos",
            f"${LTV:,.0f}\n(lo perdemos entero)",
            C["rojo"],
        ),
        (
            0,
            0,
            "FP",
            "No se iba y le dimos cupón",
            f"${COSTO_CUPON:,.0f}\n(margen regalado)",
            C["rojo"],
        ),
        (0, 1, "TN", "No se iba y no hicimos nada", "$0", C["verde"]),
    ]
    fig, ax = lienzo(8, 4.6)
    for f, c, sigla, txt, costo, col in celdas:
        x, y = 1.6 + c * 3.1, 0.2 + f * 1.9
        caja(
            ax,
            x,
            y,
            2.9,
            1.7,
            f"{sigla}: {txt}\n\n{costo}".replace(",", "."),
            col,
            size=9,
        )
    ax.text(3.05, 4.25, "Contactamos", ha="center", weight="bold")
    ax.text(6.15, 4.25, "No contactamos", ha="center", weight="bold")
    ax.text(0.8, 3.0, "Se iba", ha="center", weight="bold")
    ax.text(0.8, 1.05, "Se quedaba", ha="center", weight="bold")
    guardar(fig, "matriz_costos.png")


def regla():
    fig, ax = lienzo(8, 2.4)
    caja(ax, 0.1, 0.8, 1.8, 0.9, "Cliente")
    caja(ax, 2.8, 0.8, 2.2, 0.9, "¿Más de 90 días\nsin comprar?", C["gris"], C["claro"])
    caja(ax, 6.0, 1.45, 1.9, 0.75, "Cupón 15%", C["verde"], "#E8F1E8")
    caja(ax, 6.0, 0.2, 1.9, 0.75, "No hacer nada", C["gris"])
    flecha(ax, (1.9, 1.25), (2.8, 1.25))
    flecha(ax, (5.0, 1.4), (6.0, 1.8), "SÍ", C["verde"])
    flecha(ax, (5.0, 1.1), (6.0, 0.6), "NO")
    guardar(fig, "regla.png")


def pipeline_ml():
    fig, ax = lienzo(10, 2.3)
    pasos = [
        "Fichas de clientes\n(señales del CRM)",
        "Modelo\n(aprende de\nejemplos)",
        "Probabilidad\nde fuga\n(ej. 0,32)",
        "¿p ≥ t* = 0,25?",
        "Contactar\no no",
    ]
    colores = [C["gris"], C["azul"], C["azul"], C["rojo"], C["verde"]]
    for i, (t, col) in enumerate(zip(pasos, colores)):
        x = 0.1 + i * 2
        caja(ax, x, 0.4, 1.6, 1.3, t, col, size=9)
        if i:
            flecha(ax, (x - 0.38, 1.05), (x - 0.02, 1.05))
    ax.text(
        4.9,
        2.05,
        "El modelo estima; el negocio decide (el umbral)",
        ha="center",
        color=C["gris"],
    )
    guardar(fig, "pipeline_ml.png")


def paraguas():
    p = np.linspace(0, 1, 101)
    t_star = COSTO_CUPON / (TASA_RETENCION * LTV)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(
        p,
        p * TASA_RETENCION * LTV / 1e3,
        color=C["azul"],
        lw=2.2,
        label="Lo que esperamos salvar: p × 60% × $400 mil",
    )
    ax.axhline(
        COSTO_CUPON / 1e3,
        color=C["rojo"],
        lw=2.2,
        label="Lo que cuesta el cupón: $60 mil",
    )
    ax.axvline(t_star, color="#1A1A1A", ls="--", lw=1.2)
    ax.fill_between(p, 0, 250, where=p >= t_star, color=C["verde"], alpha=0.08)
    ax.annotate(
        f"t* = {t_star:.2f}".replace(".", ",") + "\ndesde aquí conviene contactar",
        (t_star, 150),
        xytext=(t_star + 0.05, 170),
        fontsize=9,
    )
    ax.set(
        xlabel="Probabilidad de fuga del cliente (p)",
        ylabel="Miles de CLP",
        ylim=(0, 250),
        title="La regla del paraguas aplicada al cupón",
    )
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    guardar(fig, "paraguas.png")


def validacion_cruzada():
    fig, ax = lienzo(8, 3.2)
    for r in range(5):
        y = 2.5 - r * 0.55
        ax.text(0.6, y + 0.2, f"Vuelta {r + 1}", ha="center", fontsize=9)
        for k in range(5):
            prueba = k == r
            caja(
                ax,
                1.3 + k * 1.15,
                y,
                1.05,
                0.42,
                "predice" if prueba else "aprende",
                C["rojo"] if prueba else C["verde"],
                "#F7EAE7" if prueba else "#E8F1E8",
                size=8,
            )
    ax.text(
        4.2,
        3.05,
        "Train se divide en 5 partes: cada parte se predice sin haberla visto",
        ha="center",
        color=C["gris"],
    )
    guardar(fig, "validacion_cruzada.png")


def privacidad():
    fig, ax = lienzo(9, 3.2)
    caja(
        ax,
        0.1,
        0.3,
        2.8,
        2.5,
        "CRM (queda en la empresa)\n\nRUT · gasto · NPS\nprobabilidad de fuga\nhistorial completo",
        C["gris"],
        C["claro"],
        9,
    )
    caja(
        ax,
        3.7,
        0.9,
        2.2,
        1.3,
        "Solo se envía:\nnombre de pila\ncategoría favorita\núltimo producto",
        C["verde"],
        "#E8F1E8",
        9,
    )
    caja(
        ax,
        6.7,
        0.9,
        2.2,
        1.3,
        "LLM\n(redacta el correo)\n\nrevisión humana\nantes de enviar",
        C["azul"],
        size=9,
    )
    flecha(ax, (2.9, 1.55), (3.7, 1.55))
    flecha(ax, (5.9, 1.55), (6.7, 1.55))
    ax.plot([3.3, 3.3], [0.1, 3.0], color=C["rojo"], ls="--", lw=1.4)
    ax.text(
        3.3,
        3.05,
        "frontera de privacidad (Ley 21.719)",
        ha="center",
        color=C["rojo"],
        fontsize=9,
    )
    guardar(fig, "privacidad.png")


def auto_uber():
    n = np.linspace(0, 10, 101)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(
        n,
        1.0 * n - 1,
        color=C["verde"],
        lw=2.2,
        label="Solución simple: costo fijo bajo, ahorra poco por cliente",
    )
    ax.plot(
        n,
        2.0 * n - 6,
        color=C["azul"],
        lw=2.2,
        label="Solución compleja: costo fijo alto, ahorra más por cliente",
    )
    ax.axhline(0, color=C["gris"], lw=1)
    ax.axvline(5, color="#1A1A1A", ls="--", lw=1.2)
    ax.annotate("punto de cruce", (5, 4), xytext=(5.3, 1.5), fontsize=9)
    ax.set(
        xlabel="Tamaño de la base de clientes",
        ylabel="Valor neto",
        xticks=[],
        yticks=[],
        title="Auto propio o Uber: el costo fijo se paga con volumen (ilustrativo)",
    )
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    guardar(fig, "auto_uber.png")


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
        json.dumps(nb, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return n


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for f in (
        mapa_clase,
        train_test,
        matriz_costos,
        regla,
        pipeline_ml,
        paraguas,
        validacion_cruzada,
        privacidad,
        auto_uber,
    ):
        f()
    for b in range(1, 6):
        mapa_clase(b)
    print(f"{len(list(OUT.glob('*.png')))} diagramas en {OUT}")
    print(
        f"{incrustar(Path(__file__).parent / 'clase_03_laboratorio.ipynb')} imágenes incrustadas en el notebook"
    )
