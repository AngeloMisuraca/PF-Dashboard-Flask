"""Análisis: cifras clave (KPI), hallazgos y conclusiones redactadas a partir de los datos.

Ninguna frase lleva números escritos a mano: todo se calcula desde los CSV, así que si
cambian los datos el texto se actualiza solo y nunca puede contradecir a los gráficos.
"""
from . import config, datos, formato
from .formato import num, pct, signo

SECTOR_CLAVE = {"Cine": "cine", "Teatro": "teatro", "Conciertos": "musica", "Macrofestivales": "macro"}


# ============================================================ utilidades
def _variacion(actual, anterior):
    """Cambio porcentual entre dos valores (None si falta alguno)."""
    if formato.vacio(actual) or formato.vacio(anterior) or anterior == 0:
        return None
    return (actual / anterior - 1) * 100


def _par(anio):
    """Los dos años que se comparan en los textos de una página: el elegido y el anterior.
    Si el elegido es el primero de la serie, el elegido y el siguiente."""
    anios = sorted(config.ANIOS)
    i = anios.index(anio)
    return (anios[i - 1], anio) if i > 0 else (anio, anios[i + 1])


def _cambio_txt(v, unidad="%"):
    """'sube un 12,4 %' / 'baja un 8,2 %' / 'se mantiene' (el verbo depende del signo)."""
    if v is None:
        return "no se puede comparar"
    if abs(v) < 0.05:
        return "se mantiene"
    cifra = pct(abs(v)) if unidad == "%" else num(abs(v)) + unidad
    return f"{'sube' if v > 0 else 'baja'} un {cifra}"


def _kpi(valor, etiqueta, detalle=None, cambio=None, ayuda=None, clave=None, extra=None):
    """Tarjeta de cifra clave. 'detalle' es texto; si hay 'cambio', se marca con flecha.

    Con 'extra', el detalle es solo texto y el cambio (con flecha) va en una segunda línea."""
    tendencia = None
    if cambio is not None:
        tendencia = "sube" if cambio > 0.05 else ("baja" if cambio < -0.05 else "igual")
    return {"valor": valor, "etiqueta": etiqueta, "detalle": detalle, "tendencia": tendencia,
            "ayuda": ayuda, "clave": clave, "extra": extra}


def _vs(cambio, anio_previo, sufijo=" %", dec=1):
    """Texto '+29,8 % vs 2022' (o None si no hay dato anterior: con 2022 elegido no hay año previo)."""
    return None if cambio is None else f"{signo(cambio, dec, sufijo)} vs {anio_previo}"


def _lista(nombres, maximo=4):
    nombres = [config.corto(n) for n in nombres]
    if len(nombres) > maximo:
        return ", ".join(nombres[:maximo]) + "…"
    if len(nombres) > 1:
        return ", ".join(nombres[:-1]) + " y " + nombres[-1]
    return nombres[0] if nombres else "ninguna"


def _por_comunidad(sector, anio):
    return datos.por_comunidad(sector, anio)


def _extremos(df, col):
    """Fila con el valor más alto y fila con el más bajo de una columna."""
    d = df.dropna(subset=[col]).sort_values(col)
    return d.iloc[-1], d.iloc[0]


def _hallazgo(icono, titulo, texto):
    return {"icono": icono, "titulo": titulo, "texto": texto}


def texto_ranking(sector, indicador, anio):
    """Frase que explica el ranking por comunidad del indicador elegido."""
    df = _por_comunidad(sector, anio).dropna(subset=[indicador]).sort_values(indicador, ascending=False)
    if len(df) < 4:
        return ""
    tipo = config.SECTORES[sector]["indicadores"][indicador][0]
    f = lambda v: formato.columna(v, indicador)
    a, b, c = df.iloc[0], df.iloc[1], df.iloc[2]
    ultimo = df.iloc[-1]
    texto = (f"{config.corto(a['Zona'])} lidera con {f(a[indicador])}, seguida de {config.corto(b['Zona'])} "
             f"({f(b[indicador])}) y {config.corto(c['Zona'])} ({f(c[indicador])}). ")
    if tipo == "abs":
        suma3 = df[indicador].head(3).sum() / df[indicador].sum() * 100
        texto += (f"Esas tres comunidades suman el {pct(suma3)} del total, así que el ranking de totales "
                  f"refleja sobre todo el tamaño de cada comunidad: para comparar de forma justa conviene "
                  f"usar los indicadores 'por habitante' o 'por función'.")
    else:
        veces = df.iloc[0][indicador] / df.iloc[-1][indicador] if df.iloc[-1][indicador] else None
        texto += f"El valor más bajo es el de {config.corto(ultimo['Zona'])} ({f(ultimo[indicador])})"
        texto += f", {num(veces)} veces menos que el más alto." if veces and veces >= 1.15 else "."
    return texto


def texto_burbujas(sector, anio):
    """Frase que clasifica las comunidades respecto a la media de España (cuadrantes del gráfico)."""
    xc, yc, _sc = config.BURBUJAS[sector]
    df = _por_comunidad(sector, anio).dropna(subset=[xc, yc])
    mx, my = datos.media_espana(sector, xc, anio), datos.media_espana(sector, yc, anio)
    if formato.vacio(mx) or formato.vacio(my):
        return ""
    sup = df[(df[xc] > mx) & (df[yc] > my)].sort_values(yc, ascending=False)["Zona"].tolist()
    inf = df[(df[xc] <= mx) & (df[yc] <= my)].sort_values(yc)["Zona"].tolist()
    ba = df[(df[xc] <= mx) & (df[yc] > my)].sort_values(yc, ascending=False)["Zona"].tolist()
    partes = []
    if sup:
        partes.append(f"Con asistencia y precio por encima de la media de España: {_lista(sup)}.")
    if ba:
        partes.append(f"Mucha asistencia con precio por debajo de la media: {_lista(ba)}.")
    if inf:
        partes.append(f"Por debajo de la media en ambos ejes: {_lista(inf)}.")
    return " ".join(partes)


# ============================================================ INICIO
def inicio(anio):
    res = datos.resumen_sectores(anio).set_index("Sector")
    previo = datos.resumen_sectores(anio - 1).set_index("Sector")
    tot_pub = res["espectadores_miles"].sum()
    tot_din = res["recaudacion_miles"].sum()
    pub = res["espectadores_miles"] / tot_pub * 100
    din = res["recaudacion_miles"] / tot_din * 100

    kpis = []
    for sector in res.index:
        cambio = _variacion(res.loc[sector, "espectadores_miles"], previo.loc[sector, "espectadores_miles"])
        kpis.append(_kpi(formato.desde_miles(res.loc[sector, "espectadores_miles"]), f"espectadores · {sector}",
                         f"{formato.euros_desde_miles(res.loc[sector, 'recaudacion_miles'])} · "
                         f"{formato.euros(res.loc[sector, 'gasto_medio'])} por persona",
                         cambio, clave=SECTOR_CLAVE[sector], extra=_vs(cambio, anio - 1)))

    gasto_cine = res.loc["Cine", "gasto_medio"]
    gasto_macro = res.loc["Macrofestivales", "gasto_medio"]
    from . import comparar
    tot = comparar.totales()
    c_pub = _variacion(tot[comparar.B]["publico"], tot[comparar.A]["publico"])
    c_din = _variacion(tot[comparar.B]["dinero"], tot[comparar.A]["dinero"])

    teatro = datos.por_comunidad("teatro", anio)
    madrid = teatro[teatro["Zona"] == "Madrid (Comunidad de)"].iloc[0]

    hallazgos = [
        _hallazgo("🎬", "El cine gana en público, no en dinero",
                  f"El cine reúne el {pct(pub['Cine'])} del público de los cuatro sectores, pero solo el "
                  f"{pct(din['Cine'])} de la recaudación. Es el sector más barato: una entrada cuesta de media "
                  f"{formato.euros(gasto_cine)}."),
        _hallazgo("🎪", "Pocos macrofestivales, mucho dinero",
                  f"Los macrofestivales son el {pct(pub['Macrofestivales'])} del público pero el "
                  f"{pct(din['Macrofestivales'])} del dinero: cada espectador paga de media "
                  f"{formato.euros(gasto_macro)}, {formato.veces(gasto_macro, gasto_cine)} lo que cuesta ir al cine."),
        _hallazgo("🎭", "El teatro está muy concentrado",
                  f"Madrid concentra el {pct(madrid['% de la recaudación de España'])} de la recaudación del teatro "
                  f"y el {pct(madrid['% de los espectadores de España'])} del público, con solo el "
                  f"{pct(madrid['% de las funciones de España'])} de las funciones."),
        _hallazgo("📈", f"De {comparar.A} a {comparar.B}",
                  f"El público de los cuatro sectores {_cambio_txt(c_pub)} y la recaudación {_cambio_txt(c_din)}. "
                  f"La página Comparativa lo desglosa por sector, indicador y comunidad, para cualquier par de años."),
    ]
    conclusion = (f"El cine mueve el {pct(pub['Cine'])} del público pero el {pct(din['Cine'])} del dinero; "
                  f"los macrofestivales hacen justo lo contrario ({pct(pub['Macrofestivales'])} del público, "
                  f"{pct(din['Macrofestivales'])} del dinero).")
    return {"kpis": kpis, "hallazgos": hallazgos, "conclusion": conclusion,
            "total_pub": formato.desde_miles(tot_pub), "total_din": formato.euros_desde_miles(tot_din, 0)}


# ============================================================ CINE
def cine(anio, indicador):
    serie = datos.serie_espana("cine").set_index("Año")
    v = lambda col, a=anio: serie.loc[a, col] if a in serie.index else None
    ant = anio - 1

    cambio_esp = _variacion(v("Espectadores (millones)"), v("Espectadores (millones)", ant))
    cambio_rec = _variacion(v("Recaudación (millones €)"), v("Recaudación (millones €)", ant))
    dif_precio = None if v("Precio medio entrada (€)", ant) is None else v("Precio medio entrada (€)") - v("Precio medio entrada (€)", ant)
    dif_veces = None if v("Veces al cine por habitante", ant) is None else v("Veces al cine por habitante") - v("Veces al cine por habitante", ant)
    cuota_ant = v("% espectadores que vieron cine español", ant)
    dif_cuota = (None if not cuota_ant else
                 (v("% espectadores que vieron cine español") / cuota_ant - 1) * 100)   # en %, no en puntos

    kpis = [
        _kpi(num(v("Espectadores (millones)")) + " M", "espectadores", _vs(cambio_esp, ant), cambio_esp,
             "Entradas vendidas en todo el año."),
        _kpi(num(v("Recaudación (millones €)")) + " M€", "recaudación", _vs(cambio_rec, ant), cambio_rec,
             "Dinero total ingresado en taquilla."),
        _kpi(formato.euros(v("Precio medio entrada (€)")), "precio medio de la entrada",
             _vs(dif_precio, ant, " €"), dif_precio, "Recaudación entre espectadores."),
        _kpi(num(v("Veces al cine por habitante")), "veces al cine por habitante",
             _vs(dif_veces, ant, "", 1), dif_veces, "Entradas por habitante al año."),
        _kpi(pct(v("% espectadores que vieron cine español")), "cuota del cine español",
             _vs(dif_cuota, ant), dif_cuota, "Porcentaje de entradas que fueron de películas españolas."),
    ]

    ccaa = _por_comunidad("cine", anio)
    top2 = ccaa.sort_values("Espectadores (millones)", ascending=False).head(2)
    suma2 = top2["% de los espectadores de España"].sum()
    mas_veces, menos_veces = _extremos(ccaa, "Veces al cine por habitante")
    top2_hab = ccaa.sort_values("Veces al cine por habitante", ascending=False).head(2)["Zona"].tolist()
    if set(top2_hab) != set(top2["Zona"]):
        matiz = (f" Pero el tamaño engaña: por habitante lideran {_lista(top2_hab)}.")
    else:
        matiz = " También lideran en asistencia por habitante."
    cara, barata = _extremos(ccaa, "Precio medio entrada (€)")
    origen = datos.filas("cine", "Origen de la película", anio).set_index("Categoría")
    usa, esp = origen.loc["Cine EEUU"], origen.loc["Cine español"]
    origen_prev = datos.filas("cine", "Origen de la película", ant).set_index("Categoría")
    cambio_cuota = ""
    if not origen_prev.empty:
        c_prev = origen_prev.loc["Cine español", "% de los espectadores de España"]
        rel = (esp['% de los espectadores de España'] / c_prev - 1) * 100       # cambio en %, no en puntos
        if abs(rel) < 0.05:
            cambio_cuota = " Es la misma cuota que hace un año."
        else:
            cambio_cuota = (f" Hace un año era el {pct(c_prev)}: "
                            f"{'se ha reducido' if rel < 0 else 'ha crecido'} un {pct(abs(rel))}.")
    pa, pb = _par(anio)
    sa, sb = serie.loc[pa], serie.loc[pb]
    c_pub = _variacion(sb["Espectadores (millones)"], sa["Espectadores (millones)"])
    c_din = _variacion(sb["Recaudación (millones €)"], sa["Recaudación (millones €)"])

    hallazgos = [
        _hallazgo("📈" if c_pub >= 0 else "📉", f"{'Más' if c_pub >= 0 else 'Menos'} público en {pb} que en {pa}",
                  f"En {pb} hubo {num(sb['Espectadores (millones)'])} M de espectadores, un {pct(abs(c_pub))} "
                  f"{'más' if c_pub >= 0 else 'menos'} que en {pa} ({num(sa['Espectadores (millones)'])} M)."),
        _hallazgo("🇺🇸", "El cine de EE. UU., el más visto",
                  f"Las películas de EE. UU. se llevan el {pct(usa['% de los espectadores de España'])} del público y el "
                  f"{pct(usa['% de la recaudación de España'])} del dinero. El cine español tiene el "
                  f"{pct(esp['% de los espectadores de España'])}.{cambio_cuota}"),
        _hallazgo("📍", "El público está concentrado",
                  f"{_lista(top2['Zona'].tolist())} suman el {pct(suma2)} de los espectadores de España.{matiz}"),
        _hallazgo("🎟️", "Dónde se va más al cine",
                  f"En {config.corto(mas_veces['Zona'])} se va {num(mas_veces['Veces al cine por habitante'])} veces al año "
                  f"por habitante; en {config.corto(menos_veces['Zona'])}, {num(menos_veces['Veces al cine por habitante'])} "
                  f"({num(mas_veces['Veces al cine por habitante'] / menos_veces['Veces al cine por habitante'])} veces menos)."),
        _hallazgo("💶", "El precio también varía",
                  f"La entrada media más cara está en {config.corto(cara['Zona'])} "
                  f"({formato.euros(cara['Precio medio entrada (€)'])}) y la más barata en "
                  f"{config.corto(barata['Zona'])} ({formato.euros(barata['Precio medio entrada (€)'])})."),
    ]

    pico = serie["Espectadores (millones)"].idxmax()
    precio_a, precio_b = sa["Precio medio entrada (€)"], sb["Precio medio entrada (€)"]
    conclusiones = {
        "evolucion_cine": (f"El máximo de la serie es {pico}, con {num(serie.loc[pico, 'Espectadores (millones)'])} M de "
                           f"espectadores. De {pa} a {pb} el público {_cambio_txt(c_pub)} y la recaudación {_cambio_txt(c_din)}"
                           + (f": la recaudación va mejor que el público porque el precio medio sube de "
                              f"{formato.euros(precio_a)} a {formato.euros(precio_b)}." if c_din > c_pub else ".")),
        "origen_cine": _conclusion_origen(pa, pb),
        "ranking": texto_ranking("cine", indicador, anio),
        "burbujas": texto_burbujas("cine", anio),
    }
    return {"kpis": kpis, "hallazgos": hallazgos, "conclusiones": conclusiones}


def _conclusion_origen(pa, pb):
    """Cómo cambia la cuota de cada origen entre dos años (en %), con el mayor cambio destacado."""
    o = datos.filas("cine", "Origen de la película").set_index(["Categoría", "Año"])
    col = "% de los espectadores de España"
    nombres = {"Cine español": "el del cine español", "Cine EEUU": "el del cine de EE. UU.",
               "Cine Unión Europea (sin España)": "el del cine del resto de la UE",
               "Otros países": "el del cine de otros países"}
    dif = {c: (o.loc[(c, pb), col] / o.loc[(c, pa), col] - 1) * 100 for c in nombres}     # cambio de cada cuota, en %
    mayor = max(dif, key=lambda c: abs(dif[c]))
    def tramo(c):
        a, b = pct(o.loc[(c, pa), col]), pct(o.loc[(c, pb), col])
        return f"se mantiene en el {b}" if a == b else f"pasa del {a} al {b}"

    return (f"De {pa} a {pb} el cine español {tramo('Cine español')} del público y el de EE. UU. "
            f"{tramo('Cine EEUU')}. "
            f"El mayor cambio es {nombres[mayor]} ({signo(dif[mayor])}).")


# ============================================================ TEATRO
def teatro(anio, indicador):
    serie = datos.serie_espana("teatro").set_index("Año")
    v = lambda col, a=anio: serie.loc[a, col] if a in serie.index else None
    ant = anio - 1
    c_fun = _variacion(v("Funciones"), v("Funciones", ant))
    c_esp = _variacion(v("Espectadores (miles)"), v("Espectadores (miles)", ant))
    c_rec = _variacion(v("Recaudación (miles €)"), v("Recaudación (miles €)", ant))
    g_ant = v("Gasto medio por espectador (€)", ant)
    d_gasto = None if formato.vacio(g_ant) else v("Gasto medio por espectador (€)") - g_ant
    p_ant = v("Espectadores por función", ant)
    d_pf = None if formato.vacio(p_ant) else v("Espectadores por función") - p_ant

    kpis = [
        _kpi(num(v("Funciones"), 0), "funciones", _vs(c_fun, ant), c_fun, "Representaciones de obras teatrales."),
        _kpi(formato.desde_miles(v("Espectadores (miles)")), "espectadores", _vs(c_esp, ant), c_esp,
             "Entradas vendidas en el año."),
        _kpi(formato.euros_desde_miles(v("Recaudación (miles €)")), "recaudación", _vs(c_rec, ant), c_rec,
             "Dinero ingresado por entradas."),
        _kpi(formato.euros(v("Gasto medio por espectador (€)")), "gasto medio por espectador",
             _vs(d_gasto, ant, " €"), d_gasto, "Incluye espectáculos gratuitos."),
        _kpi(num(v("Espectadores por función"), 0), "espectadores por función", _vs(d_pf, ant, "", 0), d_pf,
             "Público medio de cada función."),
    ]

    ccaa = _por_comunidad("teatro", anio)
    lider = ccaa.sort_values("% de la recaudación de España", ascending=False).iloc[0]
    tam = datos.filas("teatro", "Tamaño del municipio", anio).set_index("Zona")
    met, peq = tam.loc["Zonas metropolitanas"], tam.loc["Menos de 5.000 hab"]
    mas_pf, menos_pf = _extremos(ccaa, "Espectadores por función")
    g_lider = lider["Gasto medio por espectador (€)"]
    g_esp = v("Gasto medio por espectador (€)")
    if g_lider > g_esp:
        comparacion = f"su gasto medio por espectador ({formato.euros(g_lider)}) supera al de España ({formato.euros(g_esp)})"
    else:
        comparacion = f"su gasto medio por espectador ({formato.euros(g_lider)}) no supera al de España ({formato.euros(g_esp)})"

    # El año elegido frente al anterior. Si el público crece más que el dinero, el gasto medio baja (y al revés)
    pa, pb = _par(anio)
    ea, eb = serie.loc[pa], serie.loc[pb]
    cp = _variacion(eb["Espectadores (miles)"], ea["Espectadores (miles)"])
    cr = _variacion(eb["Recaudación (miles €)"], ea["Recaudación (miles €)"])
    ga, gb = ea["Gasto medio por espectador (€)"], eb["Gasto medio por espectador (€)"]
    publico_gana = cp > cr
    titulo_paradoja = "Más público, no más dinero por persona" if publico_gana else "Cada espectador paga más"
    paradoja = (f"De {pa} a {pb} el público {_cambio_txt(cp)} y la recaudación {_cambio_txt(cr)}. "
                f"Por eso el gasto medio {'baja' if gb < ga else 'sube'} de {formato.euros(ga)} a {formato.euros(gb)}"
                + (": cada espectador aporta menos dinero." if gb < ga else "."))

    hallazgos = [
        _hallazgo("📍", f"{config.corto(lider['Zona'])} concentra el teatro",
                  f"{config.corto(lider['Zona'])} se lleva el {pct(lider['% de la recaudación de España'])} de la recaudación "
                  f"y el {pct(lider['% de los espectadores de España'])} del público, con el "
                  f"{pct(lider['% de las funciones de España'])} de las funciones; {comparacion}."),
        _hallazgo("🏙️", "El dinero está en las ciudades grandes",
                  f"Las zonas metropolitanas recaudan el {pct(met['% de la recaudación de España'])} con el "
                  f"{pct(met['% de las funciones de España'])} de las funciones. En los municipios de menos de 5.000 "
                  f"habitantes el gasto medio por espectador es de solo {formato.euros(peq['Gasto medio por espectador (€)'])}."),
        _hallazgo("⚖️", titulo_paradoja, paradoja),
        _hallazgo("🎟️", "Salas más y menos llenas",
                  f"Cada función de {config.corto(mas_pf['Zona'])} reúne {num(mas_pf['Espectadores por función'], 0)} "
                  f"espectadores de media; las de {config.corto(menos_pf['Zona'])}, {num(menos_pf['Espectadores por función'], 0)}."),
    ]
    conclusiones = {
        "evolucion_teatro": paradoja,
        "tamano_teatro": (f"Las zonas metropolitanas tienen el {pct(met['% de las funciones de España'])} de las funciones, "
                          f"el {pct(met['% de los espectadores de España'])} del público y el "
                          f"{pct(met['% de la recaudación de España'])} de la recaudación: cuanto más grande el municipio, "
                          f"más dinero por función. Los pueblos pequeños hacen el {pct(peq['% de las funciones de España'])} de las funciones "
                          f"pero recaudan solo el {pct(peq['% de la recaudación de España'])}."),
        "ranking": texto_ranking("teatro", indicador, anio),
        "burbujas": texto_burbujas("teatro", anio),
    }
    return {"kpis": kpis, "hallazgos": hallazgos, "conclusiones": conclusiones}


# ============================================================ MÚSICA
def musica(anio, indicador):
    tipos = datos.musica_por_tipo().set_index(["Categoría", "Año"])
    total = datos.serie_espana("musica").set_index("Año")
    ant = anio - 1
    t = lambda col, a=anio: total.loc[a, col] if a in total.index else None
    c_esp = _variacion(t("Espectadores (miles)"), t("Espectadores (miles)", ant))
    c_rec = _variacion(t("Recaudación (miles €)"), t("Recaudación (miles €)", ant))
    g_ant = t("Gasto medio por espectador (€)", ant)
    d_g = None if formato.vacio(g_ant) else t("Gasto medio por espectador (€)") - g_ant
    conc = tipos.loc[("Conciertos", anio)]
    macro = tipos.loc[("Macrofestivales", anio)]
    conc_ant = tipos.loc[("Conciertos", ant)] if ("Conciertos", ant) in tipos.index else None
    c_conc = None if conc_ant is None else _variacion(conc["Conciertos"], conc_ant["Conciertos"])
    pct_rec_macro = macro["Recaudación (miles €)"] / t("Recaudación (miles €)") * 100
    pct_pub_macro = macro["Espectadores (miles)"] / t("Espectadores (miles)") * 100

    kpis = [
        _kpi(formato.desde_miles(t("Espectadores (miles)")), "espectadores", _vs(c_esp, ant), c_esp,
             "Conciertos más macrofestivales."),
        _kpi(formato.euros_desde_miles(t("Recaudación (miles €)")), "recaudación", _vs(c_rec, ant), c_rec,
             "Conciertos más macrofestivales."),
        _kpi(formato.euros(t("Gasto medio por espectador (€)")), "gasto medio por espectador",
             _vs(d_g, ant, " €"), d_g, "Incluye espectáculos gratuitos."),
        _kpi(pct(pct_rec_macro), "de la recaudación, de macrofestivales", f"con el {pct(pct_pub_macro)} del público",
             None, "Los macrofestivales recaudan mucho con poco público.", clave="macro"),
        _kpi(num(conc["Conciertos"], 0) if not formato.vacio(conc["Conciertos"]) else "–", "conciertos",
             _vs(c_conc, ant), c_conc, "Número de conciertos de música popular (sin macrofestivales)."),
    ]

    pa, pb = _par(anio)
    rec22_t, rec23_t = total.loc[pa, "Recaudación (miles €)"], total.loc[pb, "Recaudación (miles €)"]
    rec22_m = tipos.loc[("Macrofestivales", pa), "Recaudación (miles €)"]
    rec23_m = tipos.loc[("Macrofestivales", pb), "Recaudación (miles €)"]
    rec22_c = tipos.loc[("Conciertos", pa), "Recaudación (miles €)"]
    rec23_c = tipos.loc[("Conciertos", pb), "Recaudación (miles €)"]
    c_m, c_c = _variacion(rec23_m, rec22_m), _variacion(rec23_c, rec22_c)
    tira = "macrofestivales" if c_m > c_c else "conciertos"
    ccaa = _por_comunidad("musica", anio)
    mas_conc = ccaa.sort_values("Conciertos", ascending=False).iloc[0]
    mas_rec = ccaa.sort_values("Recaudación (miles €)", ascending=False).iloc[0]
    mas_pc, menos_pc = _extremos(ccaa, "Espectadores por concierto")

    hallazgos = [
        _hallazgo("🎪", "Pocos macrofestivales, mucho dinero",
                  f"Los macrofestivales son el {pct(pct_pub_macro)} del público pero se llevan el "
                  f"{pct(pct_rec_macro)} de la recaudación: recaudan más que todos los conciertos juntos."
                  if pct_rec_macro > 50 else
                  f"Los macrofestivales son el {pct(pct_pub_macro)} del público y el {pct(pct_rec_macro)} de la recaudación."),
        _hallazgo("💶", "Cada espectador paga distinto",
                  f"Un espectador de macrofestival paga de media {formato.euros(macro['Gasto medio por espectador (€)'])} "
                  f"frente a {formato.euros(conc['Gasto medio por espectador (€)'])} en un concierto: "
                  f"{formato.veces(macro['Gasto medio por espectador (€)'], conc['Gasto medio por espectador (€)'])} más."),
        _hallazgo("🚀", f"Los {tira} tiran del dinero",
                  f"De {pa} a {pb} la recaudación pasó de {formato.euros_desde_miles(rec22_t)} a "
                  f"{formato.euros_desde_miles(rec23_t)} ({signo(_variacion(rec23_t, rec22_t))}). En los macrofestivales "
                  f"{_cambio_txt(c_m)} y en los conciertos {_cambio_txt(c_c)}."),
        _hallazgo("📍", "Comunidades con perfiles distintos",
                  f"{config.corto(mas_conc['Zona'])} hace más conciertos ({num(mas_conc['Conciertos'], 0)}) y "
                  f"{config.corto(mas_rec['Zona'])} recauda más ({formato.euros_desde_miles(mas_rec['Recaudación (miles €)'])}). "
                  f"Los conciertos más llenos están en {config.corto(mas_pc['Zona'])} "
                  f"({num(mas_pc['Espectadores por concierto'], 0)} personas de media) y los más pequeños en "
                  f"{config.corto(menos_pc['Zona'])} ({num(menos_pc['Espectadores por concierto'], 0)})."),
    ]
    conclusiones = {
        "tipo_musica": (f"En {anio}, el {pct(pct_pub_macro)} del público de música popular fue a un macrofestival, "
                        f"pero ese público generó el {pct(pct_rec_macro)} de la recaudación."),
        "evolucion_musica": (f"De {pa} a {pb} la recaudación total {_cambio_txt(_variacion(rec23_t, rec22_t))}: en los "
                             f"conciertos {_cambio_txt(c_c)} y en los macrofestivales {_cambio_txt(c_m)}. "
                             f"La parte que más crece son los {tira}."),
        "gasto_musica": (f"El macrofestival cuesta de media {formato.euros(macro['Gasto medio por espectador (€)'])} por persona y el concierto "
                         f"{formato.euros(conc['Gasto medio por espectador (€)'])}. La diferencia ({formato.veces(macro['Gasto medio por espectador (€)'], conc['Gasto medio por espectador (€)'])}) "
                         f"explica por qué los macrofestivales pesan tanto en el dinero."),
        "ranking": texto_ranking("musica", indicador, anio),
        "burbujas": texto_burbujas("musica", anio),
    }
    return {"kpis": kpis, "hallazgos": hallazgos, "conclusiones": conclusiones}
