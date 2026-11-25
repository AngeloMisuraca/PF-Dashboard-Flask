"""Preparación de la tabla que se muestra en pantalla (recortar columnas, formatear, enlaces de orden)."""
from urllib.parse import urlencode

import pandas as pd

from . import formato


def recortar(df, columnas_resumen, vista):
    """Vista 'resumen' = solo las columnas clave. Vista 'completa' = todas las que tengan algún dato."""
    if not df.empty:
        df = df.dropna(axis=1, how="all")                # fuera columnas totalmente vacías
    # (con una búsqueda sin resultados se conservan las columnas para que la tabla no desaparezca)
    if vista == "resumen":
        visibles = [c for c in columnas_resumen if c in df.columns]
        if visibles:
            return df[visibles]
    return df


def preparar(df, limite=0):
    """Convierte la tabla en algo que Jinja pueda pintar.

    Devuelve un diccionario con las columnas, las filas YA formateadas (1.234,5),
    si cada columna es numérica (para alinear a la derecha) y cuántas filas hay en total.
    """
    total = len(df)
    if limite:
        df = df.head(limite)
    columnas = df.columns.tolist()
    numericas = [pd.api.types.is_numeric_dtype(df[c]) for c in columnas]
    # Las columnas de porcentaje llevan una barra proporcional al valor máximo de la columna (se lee de un vistazo)
    maximos = {c: df[c].max() for c, num in zip(columnas, numericas) if num and c.startswith("%") and len(df)}
    filas_fmt = []
    for _, fila in df.iterrows():
        celdas = []
        for c, num in zip(columnas, numericas):
            if not num:
                celdas.append({"t": "" if formato.vacio(fila[c]) else str(fila[c]), "b": None})
                continue
            barra = None
            if c in maximos and not formato.vacio(fila[c]) and maximos[c] > 0:
                barra = round(max(float(fila[c]), 0) / float(maximos[c]) * 100, 1)
            celdas.append({"t": formato.columna(fila[c], c), "b": barra})
        filas_fmt.append(celdas)
    return {"columnas": columnas, "numericas": numericas, "filas": filas_fmt,
            "total": total, "mostradas": len(filas_fmt)}


def enlaces_orden(ruta, parametros, columnas, orden, direccion, ancla="tabla"):
    """Para cada cabecera, el enlace que ordena por esa columna.

    Pulsar una columna nueva ordena de mayor a menor; pulsarla otra vez invierte el orden.
    Se conservan el resto de filtros que haya en la URL.
    """
    enlaces = {}
    for c in columnas:
        nueva = "asc" if (orden == c and direccion == "desc") else "desc"
        consulta = dict(parametros, orden=c, dir=nueva)
        enlaces[c] = {
            "url": f"{ruta}?{urlencode(consulta)}#{ancla}",
            "estado": ("▲" if direccion == "asc" else "▼") if orden == c else "",
            "aria": ("ascending" if direccion == "asc" else "descending") if orden == c else "none",
        }
    return enlaces
