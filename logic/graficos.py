"""Gráficos interactivos.

Cada función devuelve un diccionario con los DATOS del gráfico (no una imagen): valores,
textos ya formateados al estilo español y colores. La plantilla lo incrusta como JSON y
static/js/graficos.js lo dibuja en el navegador con Chart.js, así que el usuario puede
pasar el ratón por encima, ver el detalle de cada barra y ocultar o mostrar series
pulsando en la leyenda.

Tipos de gráfico (clave "tipo"):
  barras        barras verticales agrupadas            apiladas      barras verticales apiladas
  barras_h      barras horizontales (ranking, cambios) apiladas_h    barras horizontales al 100 %
  lineas        líneas por años (o índice 100)         burbujas      dispersión con tamaño y medias
  paneles       varios gráficos, uno por sector        tartas_anios  una tarta por año con su tabla
"""
from functools import lru_cache

from . import config, datos, formato

C = config.COLORES
num = formato.num


# ============================================================ utilidades de color
def _rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def aclarar(color, f):
    """Mezcla un color con blanco (f=0 igual, f=1 blanco). Da tonos del mismo color."""
    return _hex(c + (255 - c) * f for c in _rgb(color))


def _serie(nombre, valores, textos=None, color=None, **extra):
    valores = [None if formato.vacio(v) else round(float(v), 3) for v in valores]
    return {"nombre": nombre, "valores": valores, "textos": textos or [num(v) for v in valores],
            "color": color, **extra}


# ============================================================ INICIO
@lru_cache(maxsize=8)
def publico_vs_dinero(anio):
    df = datos.resumen_sectores(anio).dropna()
    pub = df["espectadores_miles"] / df["espectadores_miles"].sum() * 100
    din = df["recaudacion_miles"] / df["recaudacion_miles"].sum() * 100
    colores = [config.COLOR_SECTOR[s] for s in df["Sector"]]
    return {
        "tipo": "barras", "alto": 380, "etiquetas": df["Sector"].tolist(), "unidad": "%",
        "series": [
            _serie("% del público (espectadores)", pub, [formato.pct(v) for v in pub], colores),
            _serie("% de la recaudación (dinero)", din, [formato.pct(v) for v in din], colores, claro=True),
        ],
    }


# ============================================================ CINE
def _evolucion(anios, valores, color, texto, titulo):
    """Un panel de evolución: barras de tono creciente, valor encima y variación dentro."""
    n = len(valores)
    tonos = [aclarar(color, 0.65 * (n - 1 - i) / max(n - 1, 1)) for i in range(n)]     # del más claro al color pleno
    dentro = [""] + [formato.signo((v / valores[i - 1] - 1) * 100) for i, v in enumerate(valores) if i > 0]
    return {"tipo": "barras", "titulo": titulo, "alto": 280, "etiquetas": anios, "leyenda": False,
            "series": [_serie(titulo, valores, [texto(v) for v in valores], tonos, dentro=dentro)]}


@lru_cache(maxsize=2)
def evolucion_cine():
    s = datos.serie_espana("cine")
    anios = [str(int(a)) for a in s["Año"]]
    return {"tipo": "paneles", "paneles": [
        _evolucion(anios, s["Espectadores (millones)"].tolist(), C["cine"], lambda v: num(v) + " M",
                   "Espectadores (millones)"),
        _evolucion(anios, s["Recaudación (millones €)"].tolist(), C["cine"], lambda v: num(v) + " M€",
                   "Recaudación (millones de €)"),
    ]}


def _apiladas_h(etiquetas, series, alto=None):
    return {"tipo": "apiladas_h", "alto": alto or 70 + 46 * len(etiquetas), "etiquetas": etiquetas,
            "unidad": "%",
            "series": [_serie(n, v, [formato.pct(x) for x in v], c) for n, v, c in series]}


@lru_cache(maxsize=2)
def origen_cine():
    orden = ["Cine español", "Cine EEUU", "Cine Unión Europea (sin España)", "Otros países"]
    nombres = {"Cine español": "Cine español", "Cine EEUU": "Cine de EE. UU.",
               "Cine Unión Europea (sin España)": "Resto de la UE", "Otros países": "Otros países"}
    colores = {"Cine español": C["cine"], "Cine EEUU": C["usa"], "Cine Unión Europea (sin España)": C["ue"],
               "Otros países": C["otros"]}
    df = datos.filas("cine", "Origen de la película")
    anios = sorted(config.ANIOS)
    series = []
    for cat in orden:
        vals = [float(df[(df["Categoría"] == cat) & (df["Año"] == a)]["% de los espectadores de España"].iloc[0])
                for a in anios]
        series.append((nombres[cat], vals, colores[cat]))
    return _apiladas_h([str(a) for a in anios], series, alto=190)


# ============================================================ TEATRO
@lru_cache(maxsize=2)
def evolucion_teatro():
    s = datos.serie_espana("teatro")
    color = C["teatro"]
    anios = [str(int(a)) for a in s["Año"]]
    rec = (s["Recaudación (miles €)"] / 1000).tolist()

    con_pub = s.dropna(subset=["Espectadores (miles)"])
    pub = (con_pub["Espectadores (miles)"] / 1000).tolist()
    gasto = con_pub["Gasto medio por espectador (€)"].tolist()
    panel_pub = _evolucion([str(int(a)) for a in con_pub["Año"]], pub, color, lambda v: num(v) + " M",
                           "Espectadores (millones)")
    panel_pub["series"][0]["dentro"] = [["Gasto medio", formato.euros(g)] for g in gasto]     # dos líneas
    return {"tipo": "paneles", "paneles": [
        _evolucion(anios, rec, color, lambda v: num(v) + " M€", "Recaudación (millones de €)"),
        panel_pub,
    ]}


@lru_cache(maxsize=4)
def tamano_teatro(anio):
    df = datos.filas("teatro", "Tamaño del municipio", anio).set_index("Zona").loc[config.ORDEN_TAMANOS]
    color = C["teatro"]
    cortos = {"Menos de 5.000 hab": "Menos de 5.000 hab.", "De 5.001 a 10.000 hab": "5.001 a 10.000 hab.",
              "De 10.001 a 30.000 hab": "10.001 a 30.000 hab.", "De 30.001 a 200.000 hab": "30.001 a 200.000 hab.",
              "Zonas metropolitanas": "Zonas metropolitanas"}
    series = [("% de las funciones", "% de las funciones de España", aclarar(color, 0.62)),
              ("% del público", "% de los espectadores de España", aclarar(color, 0.3)),
              ("% de la recaudación", "% de la recaudación de España", color)]
    return {"tipo": "barras", "alto": 380, "etiquetas": [cortos.get(t, t) for t in df.index], "unidad": "%",
            "eje_y": True, "max": 100,
            "series": [_serie(n, df[col], [formato.pct(v) for v in df[col]], c) for n, col, c in series]}


# ============================================================ MÚSICA
@lru_cache(maxsize=4)
def tipo_musica(anio):
    mus = datos.musica_por_tipo()
    mus = mus[mus["Año"] == anio].set_index("Categoría")
    pub, din = mus["Espectadores (miles)"], mus["Recaudación (miles €)"]
    series = [("Conciertos", [pub["Conciertos"] / pub.sum() * 100, din["Conciertos"] / din.sum() * 100], C["musica"]),
              ("Macrofestivales", [pub["Macrofestivales"] / pub.sum() * 100,
                                   din["Macrofestivales"] / din.sum() * 100], C["macro"])]
    return _apiladas_h(["Público (espectadores)", "Dinero (recaudación)"], series, alto=190)


@lru_cache(maxsize=2)
def evolucion_musica():
    mus = datos.musica_por_tipo()
    anios = sorted(mus["Año"].unique())

    def rec(cat):
        return [mus[(mus["Categoría"] == cat) & (mus["Año"] == a)]["Recaudación (miles €)"].iloc[0] / 1000
                for a in anios]

    conc, macro = rec("Conciertos"), rec("Macrofestivales")
    return {"tipo": "apiladas", "alto": 340, "etiquetas": [str(int(a)) for a in anios],
            "totales": [num(c + m, 0) + " M€" for c, m in zip(conc, macro)],
            "series": [_serie("Conciertos", conc, [num(v, 0) + " M€" for v in conc], C["musica"]),
                       _serie("Macrofestivales", macro, [num(v, 0) + " M€" for v in macro], C["macro"])]}


@lru_cache(maxsize=2)
def gasto_musica():
    mus = datos.musica_por_tipo()
    anios = sorted(mus["Año"].unique())
    series = []
    for cat, color in [("Conciertos", C["musica"]), ("Macrofestivales", C["macro"])]:
        vals = [mus[(mus["Categoría"] == cat) & (mus["Año"] == a)]["Gasto medio por espectador (€)"].iloc[0]
                for a in anios]
        series.append(_serie(cat, vals, [formato.euros(v) for v in vals], color))
    return {"tipo": "barras", "alto": 340, "etiquetas": [str(int(a)) for a in anios], "series": series}


# ============================================================ COMUNIDADES (los 3 sectores)
@lru_cache(maxsize=64)
def ranking(sector, indicador, anio):
    cfg = config.SECTORES[sector]
    df = datos.por_comunidad(sector, anio).dropna(subset=[indicador]).sort_values(indicador, ascending=False)
    vals = df[indicador].astype(float).tolist()
    colores = [cfg["color"] if i < 3 else aclarar(cfg["color"], 0.55) for i in range(len(vals))]
    return {"tipo": "barras_h", "alto": 60 + 28 * len(vals), "etiquetas": [config.corto(n) for n in df["Zona"]],
            "series": [_serie(indicador, vals, [formato.columna(v, indicador) for v in vals], colores)]}


@lru_cache(maxsize=16)
def burbujas(sector, anio):
    cfg = config.SECTORES[sector]
    xc, yc, sc = config.BURBUJAS[sector]
    df = datos.por_comunidad(sector, anio).dropna(subset=[xc, yc, sc])
    tope = df[sc].max()
    puntos = [{"x": round(float(r[xc]), 3), "y": round(float(r[yc]), 3),
               "r": round(6 + 26 * (float(r[sc]) / tope) ** 0.5, 2),
               "nombre": config.corto(r["Zona"]),
               "detalle": [f"{xc}: {formato.columna(r[xc], xc)}", f"{yc}: {formato.columna(r[yc], yc)}",
                           f"{sc}: {formato.columna(r[sc], sc)}"]}
              for _i, r in df.iterrows()]
    mx, my = datos.media_espana(sector, xc, anio), datos.media_espana(sector, yc, anio)
    return {"tipo": "burbujas", "alto": 460, "color": cfg["color"], "puntos": puntos,
            "eje_x": xc + ", más caro hacia la derecha", "eje_y": yc + ", más asistencia hacia arriba",
            "media_x": None if formato.vacio(mx) else float(mx), "media_y": None if formato.vacio(my) else float(my),
            "nota": "El tamaño de cada burbuja es " + sc.lower() + ". Las líneas discontinuas marcan la media de España."}


# ============================================================ COMPARATIVA: el comparador
COLOR_CMP = {"cine": C["cine"], "teatro": C["teatro"], "conciertos": C["musica"], "macro": C["macro"]}


def comparador(r, medida, estilo):
    """Gráfico del comparador en el estilo elegido. 'r' viene de comparar.comparador().

    Regla: cada gráfico compara AÑOS. Los que dibujan valores (barras y líneas) ponen un panel
    por sector con su propia escala, para que el cine (decenas de millones) no aplaste al teatro.
    Los que comparan sectores entre sí lo hacen con una medida común: el índice 100 o el % de cambio.

    barras  → un panel por sector: una barra por año (gris = antes, granate = después)
    lineas  → un panel por sector: su línea a lo largo de los años, con el valor en cada punto
    indice  → todos juntos, cada sector empieza en 100: se ve quién crece más
    cambio  → todos juntos, el cambio del primer al último año
    Con un solo año no hay nada que comparar en el tiempo: barras de los sectores ese año.
    """
    from . import comparar
    filas, anios = r["filas"], r["anios"]
    tipo_medida = comparar.MEDIDAS_CMP[medida]["tipo"]
    eje = comparar.MEDIDAS_CMP[medida]["eje"]
    unidad = "%" if tipo_medida == "puntos" else ""
    tramo = f"de {anios[0]} a {anios[-1]}"

    if len(anios) == 1:
        vals = [comparar.valor_eje(medida, f["valores"][0]) for f in filas]
        return {"tipo": "barras", "alto": 380, "etiquetas": [f["nombre"] for f in filas], "leyenda": False,
                "eje_y": True, "unidad": unidad, "eje": eje,
                "series": [_serie(str(anios[0]), vals, [f["textos"][0] for f in filas],
                                  [COLOR_CMP[f["clave"]] for f in filas])]}

    if estilo == "cambio":
        orden = sorted([f for f in filas if f["cambio"] and f["cambio"]["valor"] is not None],
                       key=lambda f: f["cambio"]["valor"], reverse=True)
        vals = [f["cambio"]["valor"] for f in orden]
        textos = [f["cambio"]["texto"] + (f" ({f['cambio']['secundario']})" if f["cambio"]["secundario"] else "")
                  for f in orden]
        colores = [COLOR_CMP[f["clave"]] if v >= 0 else aclarar(COLOR_CMP[f["clave"]], 0.45)
                   for f, v in zip(orden, vals)]
        return {"tipo": "barras_h", "alto": 90 + 56 * len(orden), "etiquetas": [f["nombre"] for f in orden],
                "divergente": True, "primero_fuerte": False,
                "series": [_serie(f"Cambio {tramo}", vals, textos, colores)],
                "nota": (f"Cambio {tramo} en %."
                         + " A la derecha de la línea, sube; a la izquierda, baja.")}

    if estilo == "indice":
        series = []
        for f in filas:
            base = f["valores"][0]
            vals = [None if (v is None or not base) else v / base * 100 for v in f["valores"]]
            final = f["cambio"]["texto"] if f["cambio"] else ""
            series.append(_serie(f["nombre"], vals, [num(v, 0) for v in vals], COLOR_CMP[f["clave"]],
                                 final=f"{f['nombre']} {final}"))
        return {"tipo": "lineas", "alto": 400, "etiquetas": [str(a) for a in anios], "series": series,
                "base": 100, "eje": f"Índice: {anios[0]} = 100", "unidad": "",
                "nota": f"Cada sector empieza en 100 en {anios[0]}. Por encima de 100, ha crecido; por debajo, "
                        "ha caído. 110 = un 10 % más."}

    # barras y líneas: un panel por sector, con sus años y su propia escala
    n = len(anios)
    paneles = []
    for f in filas:
        vals = [comparar.valor_eje(medida, v) for v in f["valores"]]
        titulo = f["nombre"] + (f": {f['cambio']['texto']} {tramo}" if f["cambio"] else "")
        color = COLOR_CMP[f["clave"]]
        tonos = [aclarar(color, 0.62 * (n - 1 - i) / (n - 1)) for i in range(n)]     # más claro = más antiguo
        if estilo == "lineas":
            paneles.append({"tipo": "lineas", "titulo": titulo, "alto": 240, "etiquetas": [str(a) for a in anios],
                            "cero": False, "puntos": True, "unidad": unidad,
                            "series": [_serie(f["nombre"], vals, f["textos"], color)]})
        else:
            paneles.append({"tipo": "barras", "titulo": titulo, "alto": 240, "etiquetas": [str(a) for a in anios],
                            "leyenda": False, "unidad": unidad,
                            "series": [_serie(f["nombre"], vals, f["textos"], tonos)]})
    return {"tipo": "paneles", "paneles": paneles, "acento": [COLOR_CMP[f["clave"]] for f in filas]}


def tartas_comparador(r, base):
    """Una tarta por año con el reparto entre los sectores marcados, y la tabla que las une."""
    from . import comparar
    filas, anios = r["filas"], r["anios"]
    pcts = comparar._repartos(filas, len(anios))
    por_anio = [[round(p[k], 2) for p in pcts] for k in range(len(anios))]
    totales = [sum(f["valores"][k] or 0 for f in filas) for k in range(len(anios))]
    total_txt = [comparar.texto_medida(base, t) for t in totales]
    que = "de público" if base == "publico" else "recaudados"
    return {
        "tipo": "tartas_anios", "anios": [str(a) for a in anios], "nombres": [f["nombre"] for f in filas],
        "colores": [COLOR_CMP[f["clave"]] for f in filas],
        "tartas": [{"titulo": str(a), "pcts": por_anio[k], "textos": [formato.pct(v) for v in por_anio[k]],
                    "centro": [total_txt[k], que]} for k, a in enumerate(anios)],
        # cuánto crece o se reduce cada porción, en %; la tendencia pinta el cambio en verde o en rojo
        "cambio": [formato.signo((p[-1] / p[0] - 1) * 100) if p[0] else "–" for p in pcts] if len(anios) > 1 else None,
        "tendencias": [("sube" if p[-1] > p[0] * 1.0005 else "baja" if p[-1] < p[0] * 0.9995 else "igual")
                       for p in pcts] if len(anios) > 1 else None,
        "cabecera_cambio": f"Cambio {anios[0]}–{anios[-1]}",
    }
