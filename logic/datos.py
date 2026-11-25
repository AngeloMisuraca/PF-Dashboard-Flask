"""Acceso a los datos: lectura de los CSV y consultas (filtrar, ordenar, series...).

Este módulo no sabe nada de Flask ni de gráficos: solo devuelve tablas de pandas.
"""
import os
import unicodedata
from functools import lru_cache

import pandas as pd

from . import config

# Ruta ABSOLUTA a data/. Funciona igual en tu PC y en PythonAnywhere.
# __file__ = este archivo -> subimos 2 niveles (logic/ -> raíz del proyecto) -> data/
CARPETA_DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

COL_DESGLOSE = "Desglose"
COL_ANIO = "Año"


# ------------------------------------------------------------------ carga
@lru_cache(maxsize=None)
def _leer(nombre):
    """Lee el CSV una sola vez (queda en memoria). 'utf-8-sig' elimina la marca BOM de Excel.

    Solo se usan los años de config.ANIOS (2022 a 2025). Los CSV traen también 2021, pero ese
    año solo tiene totales de España, le faltan columnas y está marcado por la COVID-19: no es
    comparable, así que se descarta aquí y ningún gráfico ni texto puede usarlo.
    """
    df = pd.read_csv(os.path.join(CARPETA_DATOS, nombre + ".csv"), encoding="utf-8-sig")
    if COL_ANIO in df.columns:
        df = df[df[COL_ANIO].isin(config.ANIOS)].reset_index(drop=True)
    return df


def cargar(nombre):
    """Devuelve una COPIA de la tabla, para que nadie modifique la que está en caché."""
    return _leer(nombre).copy()


def opciones(nombre, columna):
    """Valores distintos de una columna, en orden de aparición (para los desplegables)."""
    return cargar(nombre)[columna].dropna().unique().tolist()


# ------------------------------------------------------------- consultas
def filas(nombre, desglose, anio=None):
    """Filas de un desglose concreto, opcionalmente de un solo año."""
    df = cargar(nombre)
    df = df[df[COL_DESGLOSE] == desglose]
    if anio is not None:
        df = df[df[COL_ANIO] == anio]
    return df


def serie_espana(nombre):
    """Serie anual del total de España (una fila por año, ordenada)."""
    desglose = "España por tipo de evento" if nombre == "musica" else "España"
    df = filas(nombre, desglose)
    if nombre == "musica":
        df = df[df["Categoría"] == "Total (conciertos + macrofestivales)"]
    return df.sort_values(COL_ANIO).reset_index(drop=True)


def musica_por_tipo():
    """Conciertos y macrofestivales de España, todos los años."""
    df = filas("musica", "España por tipo de evento")
    return df[df["Categoría"].isin(["Conciertos", "Macrofestivales"])].sort_values(COL_ANIO)


def por_comunidad(sector, anio):
    """Una fila por comunidad autónoma. Añade la columna 'Zona' con el nombre, igual en los 3 sectores."""
    cfg = config.SECTORES[sector]
    df = filas(cfg["archivo"], cfg["desglose_ccaa"], anio).copy()
    df["Zona"] = df[cfg["col_zona"]]
    return df.reset_index(drop=True)


def valor(sector_o_df, columna, anio=None):
    """Atajo para leer un único valor del total de España."""
    df = serie_espana(sector_o_df) if isinstance(sector_o_df, str) else sector_o_df
    if anio is not None:
        df = df[df[COL_ANIO] == anio]
    if df.empty:
        return None
    return df.iloc[0][columna]


def media_espana(sector, columna, anio):
    """Valor de España de un indicador (en música, el de los conciertos). Sirve para las líneas de media."""
    if sector == "musica":
        fila = musica_por_tipo()
        fila = fila[(fila["Categoría"] == "Conciertos") & (fila[COL_ANIO] == anio)]
        return None if fila.empty else fila.iloc[0][columna]
    return valor(sector, columna, anio)


def indicadores_disponibles(sector, anio):
    """Indicadores del sector que tienen datos por comunidad ese año (algunos años faltan columnas)."""
    df = por_comunidad(sector, anio)
    return [i for i in config.SECTORES[sector]["indicadores"] if i in df.columns and df[i].notna().any()]


def resumen_sectores(anio):
    """Cine, teatro, conciertos y macrofestivales de un año, en las mismas unidades.

    Devuelve columnas: Sector, espectadores_miles, recaudacion_miles, gasto_medio.
    El cine viene en millones, así que se pasa a miles para poder compararlo.
    """
    cine = valor("cine", "Espectadores (millones)", anio)
    cine_rec = valor("cine", "Recaudación (millones €)", anio)
    teatro = serie_espana("teatro")
    mus = musica_por_tipo()
    filas_res = [
        ("Cine", cine * 1000 if cine is not None else None,
         cine_rec * 1000 if cine_rec is not None else None, valor("cine", "Precio medio entrada (€)", anio)),
        ("Teatro", valor(teatro, "Espectadores (miles)", anio), valor(teatro, "Recaudación (miles €)", anio),
         valor(teatro, "Gasto medio por espectador (€)", anio)),
    ]
    for etiqueta, categoria in (("Conciertos", "Conciertos"), ("Macrofestivales", "Macrofestivales")):
        sub = mus[(mus["Categoría"] == categoria) & (mus[COL_ANIO] == anio)]
        fila = sub.iloc[0] if not sub.empty else None
        filas_res.append((etiqueta,
                          fila["Espectadores (miles)"] if fila is not None else None,
                          fila["Recaudación (miles €)"] if fila is not None else None,
                          fila["Gasto medio por espectador (€)"] if fila is not None else None))
    return pd.DataFrame(filas_res, columns=["Sector", "espectadores_miles", "recaudacion_miles", "gasto_medio"])


SECTORES_CRUCE = ["Cine", "Teatro", "Música popular - conciertos"]


@lru_cache(maxsize=8)
def _cruce(anio):
    """Cine, teatro y conciertos por comunidad para UN año, calculado desde los tres CSV de sector.

    Reproduce exactamente comparativa_2023.csv (se comprueba en comprobar_cruce) y permite tener
    la misma tabla para 2022. Todo se pasa a miles para poder sumar sectores.
    """
    filas_ = []
    # (sector, archivo, desglose, columna de zona, factor a miles, col. funciones, col. % de España)
    fuentes = [
        ("Cine", "cine", "Comunidad autónoma", "Categoría", 1000, None, "% de los espectadores de España"),
        ("Teatro", "teatro", "Comunidad autónoma", "Zona", 1, "Funciones", "% de los espectadores de España"),
        ("Música popular - conciertos", "musica", "Conciertos por comunidad", "Categoría", 1, "Conciertos",
         "% de los espectadores"),
    ]
    col_esp = {"cine": "Espectadores (millones)", "teatro": "Espectadores (miles)", "musica": "Espectadores (miles)"}
    col_rec = {"cine": "Recaudación (millones €)", "teatro": "Recaudación (miles €)", "musica": "Recaudación (miles €)"}
    for sector, archivo, desglose, zona, factor, col_fun, col_pct in fuentes:
        for _, f in filas(archivo, desglose, anio).iterrows():
            filas_.append({"Comunidad": f[zona], "Sector": sector,
                           "Espectadores (miles)": f[col_esp[archivo]] * factor,
                           "Recaudación (miles €)": f[col_rec[archivo]] * factor,
                           "Funciones o conciertos": f[col_fun] if col_fun else None,
                           "% de los espectadores de España en ese sector": f[col_pct]})
    df = pd.DataFrame(filas_)

    # España: totales oficiales de cada sector (no la suma de comunidades, que difiere por redondeos)
    res = resumen_sectores(anio).set_index("Sector")
    tipos = musica_por_tipo()
    conc = tipos[(tipos["Categoría"] == "Conciertos") & (tipos[COL_ANIO] == anio)].iloc[0]
    teatro = serie_espana("teatro")
    espana = [
        ("Cine", res.loc["Cine"], None),
        ("Teatro", res.loc["Teatro"], valor(teatro, "Funciones", anio)),
        ("Música popular - conciertos", res.loc["Conciertos"], conc["Conciertos"]),
        ("Música popular - macrofestivales", res.loc["Macrofestivales"], None),
    ]
    filas_esp = [{"Comunidad": "España", "Sector": s, "Espectadores (miles)": r["espectadores_miles"],
                  "Recaudación (miles €)": r["recaudacion_miles"], "Gasto medio por espectador (€)": r["gasto_medio"],
                  "Funciones o conciertos": fun,
                  "% de los espectadores de España en ese sector": 100.0 if s in SECTORES_CRUCE else None}
                 for s, r, fun in espana]
    df = pd.concat([pd.DataFrame(filas_esp), df], ignore_index=True)

    # Reparto dentro de cada comunidad (solo cine + teatro + conciertos: los macrofestivales no tienen comunidad)
    tres = df["Sector"].isin(SECTORES_CRUCE)
    for col, nueva in (("Espectadores (miles)", "% de los espectadores de la comunidad"),
                       ("Recaudación (miles €)", "% de la recaudación de la comunidad")):
        total = df[tres].groupby("Comunidad")[col].transform("sum")
        df.loc[tres, nueva] = (df.loc[tres, col] / total * 100).round(1)
    columnas = ["Comunidad", "Sector", "Espectadores (miles)", "Recaudación (miles €)", "Gasto medio por espectador (€)",
                "Funciones o conciertos", "% de los espectadores de la comunidad", "% de la recaudación de la comunidad",
                "% de los espectadores de España en ese sector"]
    return df[columnas]


def comparativa(anio=None):
    """Tabla cine/teatro/música por comunidad del año pedido (por defecto, el último)."""
    return _cruce(anio or config.ANIO_DEFECTO).copy()


def comprobar_cruce():
    """Diferencia máxima entre la tabla recalculada de 2023 y el CSV oficial comparativa_2023.csv."""
    propia = comparativa(2023).set_index(["Comunidad", "Sector"])
    oficial = cargar("comparativa_2023").set_index(["Comunidad", "Sector"])
    numericas = [c for c in oficial.columns if pd.api.types.is_numeric_dtype(oficial[c])]
    comun = oficial.index.intersection(propia.index)
    return (propia.loc[comun, numericas] - oficial.loc[comun, numericas]).abs().max()


# ------------------------------------------------ filtrado para la tabla
def _sin_acentos(texto):
    return unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()


def filtrar(nombre, desglose=None, anio=None, orden=None, ascendente=False, buscar=None, extra=None):
    """Aplica a un CSV los filtros del usuario: desglose, año, columnas concretas, texto y orden."""
    df = cargar(nombre)
    for columna, valor_ in (extra or {}).items():
        if columna in df.columns and valor_:
            df = df[df[columna] == valor_]
    if desglose and COL_DESGLOSE in df.columns:
        df = df[df[COL_DESGLOSE] == desglose]
    if anio is not None and COL_ANIO in df.columns:
        df = df[df[COL_ANIO] == anio]
    if buscar:
        # Busca el texto (sin tener en cuenta mayúsculas ni tildes) en las columnas de texto
        columnas_texto = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        consulta = _sin_acentos(buscar)
        mascara = pd.Series(False, index=df.index)
        for c in columnas_texto:
            mascara |= df[c].map(_sin_acentos).str.contains(consulta, regex=False)
        df = df[mascara]
    if orden in df.columns:
        # na_position="last": los huecos siempre van al final, ordenes como ordenes
        df = df.sort_values(orden, ascending=ascendente, na_position="last", kind="mergesort")
    return df.reset_index(drop=True)
