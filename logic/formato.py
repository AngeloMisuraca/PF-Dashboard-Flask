"""Formato de números al estilo español: 1.234,5 (punto de millar, coma decimal)."""
import pandas as pd

MENOS = "−"      # signo menos tipográfico


def vacio(valor):
    return valor is None or bool(pd.isna(valor))


def num(valor, decimales=1):
    """76.7 -> '76,7' · 16192 -> '16.192' (decimales=0). Los vacíos salen como '–'."""
    if vacio(valor):
        return "–"
    texto = f"{float(valor):,.{decimales}f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def es_decimal(columna):
    """¿Esta columna se muestra con decimales? (millones, porcentajes, euros por unidad, per cápita)."""
    c = columna.lower()
    return "millones" in c or "%" in c or c.endswith("(€)") or "habitante" in c


def columna(valor, nombre_columna):
    """Formatea un valor según el tipo de columna al que pertenece."""
    if vacio(valor):
        return "–"
    if nombre_columna in ("Año", "Nivel"):
        return str(int(valor))
    return num(valor, 1 if es_decimal(nombre_columna) else 0)


def pct(valor, decimales=1):
    return "–" if vacio(valor) else num(valor, decimales) + " %"


def signo(valor, decimales=1, sufijo=" %"):
    """+29,8 % / −4,6 %."""
    if vacio(valor):
        return "–"
    texto = num(abs(valor), decimales) + sufijo
    return ("+" if valor >= 0 else MENOS) + texto


def desde_miles(valor_miles, decimales=1):
    """8287 (miles) -> '8,3 M' · 950 (miles) -> '950 mil'."""
    if vacio(valor_miles):
        return "–"
    if abs(valor_miles) >= 1000:
        return num(valor_miles / 1000, decimales) + " M"
    return num(valor_miles, 0) + " mil"


def euros_desde_miles(valor_miles, decimales=1):
    """138802 (miles de €) -> '138,8 M€'."""
    if vacio(valor_miles):
        return "–"
    return num(valor_miles / 1000, decimales) + " M€"


def euros(valor, decimales=1):
    return "–" if vacio(valor) else num(valor, decimales) + " €"


def veces(a, b, decimales=1):
    """'3,8 veces' (a entre b)."""
    return num(a / b, decimales) + " veces"
