"""Capa de lógica: expediente de la decisión y texto para el cliente (Paso 9)."""

import pandas as pd

from umbral_fraude.explicar import Lime

DECISIONES = ("mantener", "levantar")


def pesos(x: float) -> str:
    """Formato chileno: $1.234.567."""
    return "$" + f"{x:,.0f}".replace(",", ".")


def hecho_observable(variable: str, valor) -> str:
    if variable == "monto_clp":
        return f"el monto de la compra es {pesos(valor)}"
    if variable == "hora_del_dia":
        return f"la compra se hizo a las {int(valor):02d}:00"
    if variable == "distancia_km":
        return f"la distancia al domicilio es {valor:g} km"
    if variable == "intentos_fallidos_24h":
        n = int(valor)
        return f"hubo {n} intento fallido en 24 horas" if n == 1 else f"hubo {n} intentos fallidos en 24 horas"
    if variable == "antiguedad_cliente_meses":
        return f"el cliente tiene {int(valor)} meses de antigüedad"
    if variable == "compra_internacional":
        return "la compra es internacional" if int(valor) == 1 else "la compra es nacional"
    if variable == "comercio_nuevo":
        return ("el comercio es nuevo para el cliente" if int(valor) == 1
                else "el cliente ya había comprado en ese comercio")
    return f"{variable} = {valor}"


def puede_cerrar(decision: str, hechos_revisados: bool) -> bool:
    """Levantar siempre cierra. Mantener exige que una persona declare haber revisado los hechos."""
    return decision in DECISIONES and (decision == "levantar" or hechos_revisados)


def redactar(cliente: pd.Series, ficha: pd.DataFrame, lime: Lime, umbral: float,
             decision: str, revisor: str, hechos_revisados: bool,
             fidelidad_minima: float) -> str:
    decision = decision.strip().lower()
    se_dicen = ficha[ficha["Mismo signo"] == "sí"]
    no_se_dicen = ficha[ficha["Mismo signo"] != "sí"]
    elementos = [
        f"{hecho_observable(r['Variable'], cliente[r['Variable']])} "
        f"({'aumenta' if r['Peso LIME'] > 0 else 'disminuye'} la sospecha)"
        for _, r in se_dicen.iterrows()
    ]

    s = ["EXPEDIENTE DE LA DECISIÓN", "",
         "Finalidad prevista: detectar fraude en una transacción con tarjeta.",
         "Fuera de finalidad: solvencia, puntaje de crédito, precio de seguro de vida o de salud,",
         "acceso a vivienda, electricidad o telecomunicaciones.",
         "Clasificación de este uso: excepción del Anexo III, punto 5(b), fraude financiero.", "",
         f"Probabilidad del modelo: {lime.prob_modelo:.0%}",
         f"Umbral del negocio:      {umbral:.0%}",
         "Alerta automática:       bloqueo provisorio",
         (f"Fidelidad de la recta:   {lime.fidelidad:.2f}  "
         f"(barra de la institución: {fidelidad_minima:.2f})")]
    s.append("El puntaje no cierra solo el bloqueo: la recta no reproduce la probabilidad."
             if lime.fidelidad < fidelidad_minima
             else "La recta supera la barra fijada por la institución.")
    s += ["", "Elementos que se pueden decir, porque ambos métodos coinciden en el signo:"]
    s += [f"  {n}. {e}" for n, e in enumerate(elementos, start=1)]
    if len(no_se_dicen):
        s += ["", "Quedan fuera del texto al cliente:"]
        s += [f"  - {r['Variable']}: {r['Mismo signo']}" for _, r in no_se_dicen.iterrows()]
    s += ["", f"Revisor: {revisor}",
          f"Decisión humana: {decision if decision in DECISIONES else 'pendiente'}",
          f"Declaró haber revisado los hechos: {'sí' if hechos_revisados else 'no'}"]

    if not puede_cerrar(decision, hechos_revisados):
        s += ["", "EXPEDIENTE ABIERTO.",
              "Falta una decisión humana válida ('mantener' o 'levantar'),",
              "o falta la declaración de que una persona revisó los hechos antes de mantener el bloqueo."]
        return "\n".join(s)

    cierre = ("La supervisión levanta el bloqueo provisorio. La compra puede continuar."
              if decision == "levantar" else
              "La supervisión mantiene el bloqueo después de revisar los hechos observables. "
              "El puntaje del modelo no es, por sí solo, la razón de ese cierre.")
    hechos = " ".join(f"({n}) {e}." for n, e in enumerate(elementos, start=1))
    texto = (
        "Usamos un sistema automático para detectar fraude en transacciones con tarjeta. "
        "Ese sistema no evalúa su solvencia ni decide si puede obtener crédito.\n\n"
        f"En esta compra el sistema estimó {lime.prob_modelo:.0%} de probabilidad de fraude. "
        f"El banco había fijado el bloqueo desde {umbral:.0%}. "
        "Ese corte lo define el negocio.\n\n"
        "Los datos de la compra que dos revisiones distintas marcan en el mismo sentido son: "
        f"{hechos} "
        "Puede pedir que corrijamos cualquiera de esos datos si no corresponden.\n\n"
        f"Una explicación simple, armada con casos parecidos al suyo, estima {lime.prob_recta:.0%}, "
        f"no el {lime.prob_modelo:.0%} del sistema. "
        "Por eso el sistema no tiene la última palabra.\n\n"
        f"{cierre} Quedó registrada a nombre de la {revisor}. "
        "Puede pedir una nueva revisión hecha por una persona y puede oponerse a esta decisión."
    )
    s += ["", "TEXTO PARA EL CLIENTE", "", texto, "",
          "El expediente queda cerrado con la finalidad, la decisión humana y este texto."]
    return "\n".join(s)
