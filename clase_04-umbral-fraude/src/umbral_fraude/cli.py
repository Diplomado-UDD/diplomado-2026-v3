"""Capa de presentación: un subcomando por paso del laboratorio. Los gráficos van a salidas/."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

from umbral_fraude import datos, expediente, explicar, umbral
from umbral_fraude.expediente import pesos

SALIDAS = Path("salidas")
ROJO, AZUL, VERDE, ROJO_SHAP, AZUL_SHAP = "#D62828", "#1F5AA6", "#2A9D8F", "#FF0051", "#008BFB"


def guardar(fig, nombre: str) -> None:
    SALIDAS.mkdir(exist_ok=True)
    ruta = SALIDAS / nombre
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nGráfico guardado en {ruta.resolve()}")


def titulo(texto: str) -> None:
    print(f"\n{'=' * 70}\n{texto}\n{'=' * 70}")


def paso_datos(_args) -> None:
    titulo("Paso 2 · Los datos: 20.000 transacciones de un banco ficticio")
    d = datos.generar()
    print(f"Transacciones: {len(d):,}".replace(",", "."))
    print(f"Fraudes: {d[datos.ETIQUETA].sum()} ({d[datos.ETIQUETA].mean():.1%} del total)\n")
    print(d.head(8).to_string())


def paso_entrenar(_args) -> None:
    titulo("Paso 3 · El equipo técnico entrena el modelo")
    lab = umbral.preparar()
    print("Modelo entrenado.")
    print(f"Lo evaluaremos sobre {len(lab.X_test):,} transacciones nuevas".replace(",", "."),
          f"(de ellas, {lab.y_real.sum()} son fraude).")


def paso_exactitud(_args) -> None:
    titulo("Paso 4 · La trampa de la exactitud")
    lab = umbral.preparar()
    print(f"Un 'modelo' que dice SIEMPRE 'no es fraude' tiene {(lab.y_real == 0).mean():.1%} "
          "de exactitud...")
    print("...y no atrapa ni un solo fraude. Por eso la exactitud sola engaña cuando el fraude es raro.")


def paso_panel(args) -> None:
    titulo("Paso 5 · Tú decides")
    lab = umbral.preparar()
    r = umbral.evaluar(lab.prob, lab.y_real, args.umbral, args.costo_fraude, args.costo_falsa_alarma)
    print(f"UMBRAL ELEGIDO: {args.umbral:.2f}\n")
    print(f"  Fraudes atrapados (VP) ............ {r['vp']:>6}")
    print(f"  Fraudes que se escaparon (FN) ..... {r['fn']:>6}")
    print(f"  Clientes buenos bloqueados (FP) ... {r['fp']:>6}")
    print(f"  Clientes buenos sin molestia (VN) . {r['vn']:>6}\n")
    print(f"  Precisión: {r['precision']:.0%}  (de cada 100 alertas, cuántas son fraude de verdad)")
    print(f"  Recall:    {r['recall']:.0%}  (de cada 100 fraudes, cuántos atrapamos)")
    print(f"  Exactitud: {r['exactitud']:.1%}")
    print(f"\n  COSTO TOTAL DE LOS ERRORES: {pesos(r['costo'])}")

    t = umbral.tabla(lab.prob, lab.y_real, args.costo_fraude, args.costo_falsa_alarma)
    mejor = t.loc[t["costo"].idxmin(), "umbral"]
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(t["umbral"], t["costo"] / 1e6, color=AZUL, linewidth=2)
    ax.axvline(args.umbral, color=ROJO, linewidth=2, label=f"Tu umbral ({args.umbral:.2f})")
    ax.axvline(mejor, color=VERDE, linestyle="--", linewidth=1.5, label=f"Menor costo ({mejor:.2f})")
    ax.set_xlabel("Umbral")
    ax.set_ylabel("Costo total (millones CLP)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    guardar(fig, "paso5_costo_por_umbral.png")


def paso_comparar(args) -> None:
    titulo("Paso 6 · ¿Qué umbral conviene más?")
    lab = umbral.preparar()
    exacta, barata = umbral.comparar(lab.prob, lab.y_real, args.costo_fraude, args.costo_falsa_alarma)
    print(f"Elegir por costo en vez de por exactitud ahorra {pesos(exacta['costo'] - barata['costo'])}"
          " en esta muestra.\n")
    filas = [("Umbral", "umbral", "{:.2f}"), ("Exactitud", "exactitud", "{:.1%}"),
             ("Precisión", "precision", "{:.1%}"), ("Recall", "recall", "{:.1%}"),
             ("Fraudes atrapados", "vp", "{:.0f}"), ("Fraudes que se escaparon", "fn", "{:.0f}"),
             ("Clientes buenos bloqueados", "fp", "{:.0f}"), ("Costo total (CLP)", "costo", None)]
    print(f"{'':28}{'Mayor exactitud':>17}{'Menor costo':>15}")
    for etiqueta, clave, fmt in filas:
        a, b = ((pesos(f[clave]) if fmt is None else fmt.format(f[clave])) for f in (exacta, barata))
        print(f"{etiqueta:28}{a:>17}{b:>15}")


def caso(args):
    """Cliente bloqueado de los pasos 7 a 9, con el umbral de menor costo."""
    lab = umbral.preparar()
    _, barata = umbral.comparar(lab.prob, lab.y_real, args.costo_fraude, args.costo_falsa_alarma)
    u = float(barata["umbral"])
    return lab, u, explicar.cliente_bloqueado(lab, u)


def paso_shap(args):
    titulo("Paso 7 · Abrir la caja negra con SHAP")
    lab, u, i = caso(args)
    print(f"Probabilidad de fraude según el modelo: {lab.prob[i]:.0%} (umbral {u:.2f}) → BLOQUEADO")
    print("En la realidad, esta compra era LEGÍTIMA.\n")
    print(lab.X_test.iloc[i].to_frame("valor").to_string())
    e = explicar.explicar_shap(lab, i)
    shap.plots.waterfall(e, max_display=8, show=False)
    guardar(plt.gcf(), "paso7_shap_waterfall.png")
    return lab, u, i, e


def paso_lime(args, previo=None):
    lab, u, i, e = previo or paso_shap(args)
    titulo("Paso 8 · La misma decisión con LIME")
    lime = explicar.explicar_lime(lab, i)
    print(f"Probabilidad del modelo (caja negra):     {lime.prob_modelo:.0%}")
    print(f"Probabilidad de la recta local (LIME):    {lime.prob_recta:.0%}")
    print(f"Fidelidad en el vecindario (R² ponderado): {lime.fidelidad:.2f}")
    print("Cerca de 1, la recta imita bien al modelo. Cerca de 0, la regla simple no alcanza.\n")
    print("Reglas del vecindario. Peso positivo = empuja a fraude:")
    for regla, peso in lime.reglas:
        print(f"  {peso:+.3f}   {regla}")

    nombres = [r for r, _ in lime.reglas][::-1]
    valores = [p for _, p in lime.reglas][::-1]
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.barh(nombres, valores, color=[ROJO_SHAP if p > 0 else AZUL_SHAP for p in valores])
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Peso en la recta local")
    ax.set_title("LIME · mismo cliente bloqueado del Paso 7")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    guardar(fig, "paso8_lime.png")

    ficha = explicar.comparar_signos(e, lime)
    print("\nComparación del mismo cliente. El signo dice hacia qué lado empuja la variable.")
    print(ficha.to_string(index=False, formatters={"Peso LIME": "{:+.3f}".format,
                                                   "Aporte SHAP": "{:+.3f}".format}))
    return lab, u, i, lime, ficha


def paso_expediente(args, previo=None) -> None:
    lab, u, i, lime, ficha = previo or paso_lime(args)
    titulo("Paso 9 · Expediente de la decisión")
    print(expediente.redactar(lab.X_test.iloc[i], ficha, lime, u, args.decision, args.revisor,
                              not args.sin_revision, args.fidelidad_minima))


def paso_todo(args) -> None:
    for paso in (paso_datos, paso_entrenar, paso_exactitud, paso_panel, paso_comparar):
        paso(args)
    paso_expediente(args, paso_lime(args, paso_shap(args)))


def main(argv=None) -> None:
    costos = argparse.ArgumentParser(add_help=False)
    costos.add_argument("--costo-fraude", type=int, default=umbral.COSTO_FRAUDE,
                        help="CLP que pierde el banco por fraude no detectado (FN)")
    costos.add_argument("--costo-falsa-alarma", type=int, default=umbral.COSTO_FALSA_ALARMA,
                        help="CLP por cliente bueno bloqueado (FP)")
    persona = argparse.ArgumentParser(add_help=False)
    persona.add_argument("--decision", default="levantar", help="'mantener' o 'levantar'")
    persona.add_argument("--revisor", default="supervisión de fraude")
    persona.add_argument("--sin-revision", action="store_true",
                         help="la persona NO declaró haber revisado los hechos")
    persona.add_argument("--fidelidad-minima", type=float, default=0.70,
                         help="barra de R² ponderado que fija la institución")
    corte = argparse.ArgumentParser(add_help=False)
    corte.add_argument("--umbral", type=float, default=0.50, help="probabilidad desde la que se bloquea")

    p = argparse.ArgumentParser(prog="fraude", description="Laboratorio clase 4: tú decides el umbral")
    sub = p.add_subparsers(dest="cmd", required=True)
    for nombre, fn, padres, ayuda in [
        ("datos", paso_datos, [], "Paso 2: set sintético"),
        ("entrenar", paso_entrenar, [], "Paso 3: entrenar el modelo"),
        ("exactitud", paso_exactitud, [], "Paso 4: la trampa de la exactitud"),
        ("panel", paso_panel, [corte, costos], "Paso 5: métricas y costo de un umbral"),
        ("comparar", paso_comparar, [costos], "Paso 6: mayor exactitud vs menor costo"),
        ("shap", paso_shap, [costos], "Paso 7: explicar un falso positivo con SHAP"),
        ("lime", paso_lime, [costos], "Paso 8: mismo cliente con LIME"),
        ("expediente", paso_expediente, [costos, persona], "Paso 9: expediente y texto al cliente"),
        ("todo", paso_todo, [corte, costos, persona], "Pasos 2 a 9 en orden"),
    ]:
        sub.add_parser(nombre, parents=padres, help=ayuda).set_defaults(fn=fn)
    args = p.parse_args(argv)
    if not 0 < getattr(args, "umbral", 0.5) < 1:
        p.error("--umbral debe estar entre 0 y 1")
    args.fn(args)


if __name__ == "__main__":
    main()
