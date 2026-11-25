"""Ensambla el contexto (los datos) que necesita cada página.

app.py solo decide QUÉ plantilla se pinta; aquí se decide con QUÉ datos. Este módulo
lee y valida los parámetros de la URL (año, filtros, orden...), pide los cálculos a
analisis, los gráficos a graficos y la tabla a tablas.
"""
from . import analisis, config, datos, formato, graficos, tablas

NOMBRES_DESCARGA = {
    "cine": "cine.csv", "teatro": "teatro.csv", "musica": "musica.csv",
    "comparativa_2023": "comparativa_2023.csv",
}


# ============================================================ lectura de parámetros
def _entero(texto, defecto):
    try:
        return int(texto)
    except (TypeError, ValueError):
        return defecto


def _anio(args):
    """Año elegido. Solo se aceptan los años de config.ANIOS; cualquier otra cosa vale el año por defecto."""
    anio = _entero(args.get("anio"), config.ANIO_DEFECTO)
    return anio if anio in config.ANIOS else config.ANIO_DEFECTO


def _elegir(valor, permitidos, defecto):
    return valor if valor in permitidos else defecto


def _anio_seccion(args, nombre, defecto):
    """Año propio de una sección (anio_c, anio_t...). Si no viene en la URL, el de la página."""
    anio = _entero(args.get(nombre), defecto)
    return anio if anio in config.ANIOS else defecto


OPCIONES_ANIO = [(a, a) for a in config.ANIOS]


def _grafico(clave, spec, conclusion="", sub_extra="", ancho=False, selector=None, titulo_extra=""):
    """Diccionario con todo lo que la plantilla necesita para pintar un gráfico con su explicación.

    'spec' son los datos del gráfico (de graficos.py o tartas.py); el navegador los dibuja.
    """
    textos = config.GRAFICOS[clave]
    return {
        "id": clave,
        "titulo": textos["titulo"] + titulo_extra,
        "sub": textos["sub"] + sub_extra,
        "lectura": textos["lectura"],
        "conclusion": conclusion,
        "spec": spec,
        "alt": f"{textos['titulo']}{titulo_extra}. {conclusion or textos['sub']}",
        "ancho": ancho,
        "selector": selector,
    }


def _tabla(nombre_csv, args, ruta, columnas_resumen, desglose=None, anio=None, extra=None):
    """Aplica filtros, orden, vista y límite de filas y devuelve la tabla lista para Jinja."""
    buscar = (args.get("buscar") or "").strip()[:40]
    vista = _elegir(args.get("vista"), ("resumen", "completa"), "resumen")
    filas = _elegir(_entero(args.get("filas"), 25), (10, 25, 0), 25)
    direccion = "asc" if args.get("dir") == "asc" else "desc"

    df = datos.filtrar(nombre_csv, desglose, anio, buscar=buscar, extra=extra)
    orden = args.get("orden") if args.get("orden") in df.columns else None
    if orden:
        df = datos.filtrar(nombre_csv, desglose, anio, orden, direccion == "asc", buscar, extra)
    tabla = tablas.preparar(tablas.recortar(df, columnas_resumen, vista), filas)

    # Parámetros que se conservan al pulsar una cabecera para ordenar
    conservar = {k: v for k, v in {
        "anio": args.get("anio"), "indicador": args.get("indicador"), "desglose": desglose or args.get("desglose"),
        "sector": args.get("sector"), "comunidad": args.get("comunidad"), "todos": args.get("todos"),
        "anio_r": args.get("anio_r"), "anio_c": args.get("anio_c"), "anio_t": args.get("anio_t"),
        "buscar": buscar, "vista": vista, "filas": filas,
    }.items() if v not in (None, "")}
    return {
        "datos": tabla,
        "enlaces": tablas.enlaces_orden(ruta, conservar, tabla["columnas"], orden, direccion),
        "orden": orden, "dir": direccion, "buscar": buscar, "vista": vista, "filas": filas, "ayudas": {},
    }


def _conic(porcentajes):
    """Cadena CSS 'conic-gradient(...)' con el color de cada sector: una tarta dibujada solo con CSS."""
    acumulado, tramos, leyenda = 0.0, [], []
    for sector, valor in porcentajes.items():
        color = config.COLOR_SECTOR[sector]
        tramos.append(f"{color} {acumulado:.2f}% {acumulado + valor:.2f}%")
        leyenda.append({"nombre": sector, "pct": formato.pct(valor), "color": color})
        acumulado += valor
    return {"css": "conic-gradient(" + ", ".join(tramos) + ")", "leyenda": leyenda}


# ============================================================ INICIO
def inicio(args):
    anio = _anio(args)
    resumen = analisis.inicio(anio)
    img = graficos.publico_vs_dinero(anio)
    res = datos.resumen_sectores(anio).set_index("Sector")

    # Abanico de cartas: una tarta por año, en orden cronológico. La del año elegido va en el
    # centro y delante; las demás se abren a sus lados (pos negativa = años anteriores).
    cartas = []
    orden = sorted(config.ANIOS)
    elegida = orden.index(anio)
    for i, a in enumerate(orden):
        r = datos.resumen_sectores(a).set_index("Sector")
        carta = _conic(r["espectadores_miles"] / r["espectadores_miles"].sum() * 100)
        carta.update(anio=a, total=formato.desde_miles(r["espectadores_miles"].sum()),
                     pos=i - elegida, elegida=(a == anio), distancia=abs(i - elegida))
        cartas.append(carta)
    return {
        "cartas": cartas, "alcance": max(elegida, len(orden) - 1 - elegida),
        "demo": _conic(res["espectadores_miles"] / res["espectadores_miles"].sum() * 100),
        "anio": anio, "anios": config.ANIOS, "anio_inicio": config.ANIO_INICIO,
        "kpis": resumen["kpis"], "hallazgos": resumen["hallazgos"],
        "total_pub": resumen["total_pub"], "total_din": resumen["total_din"],
        "grafico": _grafico("publico_dinero", img, resumen["conclusion"], f" Datos de {anio}.", ancho=True),
        "sectores": [(k, config.SECTORES[k]) for k in ("cine", "teatro", "musica")],
        "glosario": config.GLOSARIO, "notas": config.NOTAS_GENERALES,
    }


# ============================================================ CINE · TEATRO · MÚSICA
def sector(nombre, args):
    """Página de un sector. Cada sección tiene SU año:
    anio (resumen y análisis) · anio_r (reparto de España) · anio_c (comunidades) · anio_t (tabla)."""
    cfg = config.SECTORES[nombre]
    ruta = "/" + nombre
    anio = _anio(args)
    anio_r = _anio_seccion(args, "anio_r", anio)
    anio_c = _anio_seccion(args, "anio_c", anio)
    anio_t_texto = args.get("anio_t")
    todos = anio_t_texto == "todos" or args.get("todos") == "1"      # tabla con todos los años
    anio_t = _anio_seccion(args, "anio_t", anio)

    disponibles = datos.indicadores_disponibles(nombre, anio_c)
    indicador = _elegir(args.get("indicador"), disponibles,
                        cfg["indicador_defecto"] if cfg["indicador_defecto"] in disponibles else disponibles[0])
    desgloses = datos.opciones(cfg["archivo"], "Desglose")
    desglose = _elegir(args.get("desglose"), desgloses, cfg["desglose_defecto"])

    calcular = {"cine": analisis.cine, "teatro": analisis.teatro, "musica": analisis.musica}[nombre]
    resultado = calcular(anio, indicador)
    concl_c = calcular(anio_c, indicador)["conclusiones"] if anio_c != anio else resultado["conclusiones"]
    concl_r = calcular(anio_r, indicador)["conclusiones"] if anio_r != anio else resultado["conclusiones"]
    definicion = cfg["indicadores"][indicador][1]

    ranking = _grafico("ranking", graficos.ranking(nombre, indicador, anio_c), concl_c["ranking"],
                       sub_extra=f" Indicador: {indicador} · {anio_c}. {definicion}", ancho=True, selector="indicador")
    burbujas = _grafico("burbujas", graficos.burbujas(nombre, anio_c), concl_c["burbujas"], titulo_extra=f" · {anio_c}",
                        ancho=True)

    # La sección de reparto mezcla gráficos de todos los años (evolución) y gráficos de un año (con selector)
    if nombre == "cine":
        graficos_fijos = [
            _grafico("evolucion_cine", graficos.evolucion_cine(), concl_r["evolucion_cine"], ancho=True),
            _grafico("origen_cine", graficos.origen_cine(), concl_r["origen_cine"], ancho=True),
        ]
        reparto_con_anio = False
    elif nombre == "teatro":
        graficos_fijos = [
            _grafico("tamano_teatro", graficos.tamano_teatro(anio_r), concl_r["tamano_teatro"],
                     titulo_extra=f" · {anio_r}", ancho=True),
            _grafico("evolucion_teatro", graficos.evolucion_teatro(), concl_r["evolucion_teatro"], ancho=True),
        ]
        reparto_con_anio = True
    else:
        graficos_fijos = [
            _grafico("tipo_musica", graficos.tipo_musica(anio_r), concl_r["tipo_musica"], titulo_extra=f" · {anio_r}",
                     ancho=True),
            _grafico("evolucion_musica", graficos.evolucion_musica(), concl_r["evolucion_musica"]),
            _grafico("gasto_musica", graficos.gasto_musica(), concl_r["gasto_musica"]),
        ]
        reparto_con_anio = True

    # Cada gráfico lleva el enlace a su versión en imagen (la dibuja matplotlib, ver imagen_sector)
    from flask import url_for
    filtros = {"anio": anio, "anio_r": anio_r, "anio_c": anio_c, "indicador": indicador}
    for g in graficos_fijos + [ranking, burbujas]:
        g["png"] = url_for("grafico_png", sector=nombre, clave=g["id"], **filtros)

    tabla = _tabla(cfg["archivo"], args, ruta, cfg["resumen"], desglose, None if todos else anio_t)
    tabla["ayudas"] = {col: info[1] for col, info in cfg["indicadores"].items()}     # tooltips de las cabeceras
    return {
        "sector": nombre, "cfg": cfg, "ruta": ruta,
        "anio": anio, "anio_r": anio_r, "anio_c": anio_c, "anio_t": "todos" if todos else anio_t,
        "anios": config.ANIOS, "opciones_anio": OPCIONES_ANIO,
        "opciones_tabla": OPCIONES_ANIO + [("todos", "Todos")], "todos": todos,
        "reparto_con_anio": reparto_con_anio,
        "indicador": indicador, "indicadores": disponibles, "definicion": definicion,
        "desglose": desglose, "desgloses": desgloses,
        "kpis": resultado["kpis"], "hallazgos": resultado["hallazgos"],
        "graficos_fijos": graficos_fijos, "graficos_comunidad": [ranking, burbujas],
        "tabla": tabla, "glosario": config.GLOSARIO, "notas": config.NOTAS_GENERALES,
        "ayuda_vista": cfg["resumen"],
    }


def imagen_sector(nombre, clave, args):
    """PNG (matplotlib) de un gráfico de la página de un sector, con los mismos filtros que la página.

    Se arma la página igual que al verla y se dibuja el gráfico pedido: así la imagen coincide
    siempre con el gráfico interactivo. Devuelve None si el gráfico no existe."""
    from . import imagenes
    pagina = sector(nombre, args)
    g = next((g for g in pagina["graficos_fijos"] + pagina["graficos_comunidad"] if g["id"] == clave), None)
    return None if g is None else imagenes.png(g["spec"], g["titulo"], g["sub"])


# ============================================================ COMPARATIVA
LECTURA_ESTILO = {
    "barras": "Un panel por sector, cada uno con su propia escala, y en cada panel una barra por año: la más clara es "
              "el año más antiguo. Encima de cada barra está su valor y en el título del panel, el cambio. Así se ve "
              "cómo cambia cada sector aunque unos sean mucho más grandes que otros.",
    "lineas": "Un panel por sector, cada uno con su propia escala: la línea recorre los años y en cada punto está su "
              "valor. Si sube, ese año hubo más que el anterior. El cambio total está en el título del panel.",
    "indice": "Todos los sectores empiezan en 100 en el primer año, así que se comparan aunque uno sea mucho más "
              "grande que otro. 110 significa un 10 % más que al principio; 90, un 10 % menos. La línea gris marca "
              "el 100: por encima, ha crecido; por debajo, ha caído.",
    "cambio": "Una barra por sector con el cambio del primer al último año elegido, ordenadas de más a menos. Las "
              "barras a la derecha de la línea suben y las de la izquierda bajan (en tono más claro).",
    "tartas": "Una tarta por año: cada porción es la parte del total de los sectores marcados que se lleva cada uno. "
              "Pasa el ratón por una fila de la tabla para resaltar su porción en todas las tartas. La última columna "
              "dice en qué % crece (verde) o se reduce (rojo) cada porción.",
    "un_anio": "Una barra por sector con su valor en el año elegido. Marca otro año para ver cómo cambia.",
}


def _comparador(args, comunidades):
    """Lo que el usuario elige en el comparador: años, sectores, qué medir, dónde y cómo verlo.

    'cmp=1' marca que el formulario se ha enviado: así, si el usuario desmarca todo, se le avisa en
    vez de volver en silencio a los valores por defecto."""
    from . import comparar
    enviado = args.get("cmp") == "1"
    anios = sorted({a for a in (_entero(x, None) for x in args.getlist("anios")) if a in config.ANIOS})
    if not anios and not enviado:
        anios = [comparar.A, comparar.B]             # al entrar, los dos últimos años
    sectores = [s for s in comparar.SECTORES_CMP if s in args.getlist("sectores")]
    if not sectores and not enviado:
        sectores = list(comparar.SECTORES_CMP)
    donde = _elegir(args.get("donde"), ["España"] + comunidades, "España")
    medidas = [m for m, d in comparar.MEDIDAS_CMP.items() if not (d.get("solo_comunidad") and donde == "España")]
    medida = _elegir(args.get("medida"), medidas, "publico")
    estilo = _elegir(args.get("estilo"), tuple(comparar.ESTILOS_CMP), "barras")

    out = {"anios": anios, "sectores": sectores, "donde": donde, "medida": medida, "estilo": estilo,
           "opciones_anios": sorted(config.ANIOS), "opciones_donde": ["España"] + comunidades,
           "opciones_sectores": [(k, v[0], graficos.COLOR_CMP[k]) for k, v in comparar.SECTORES_CMP.items()],
           "opciones_medidas": [(m, comparar.MEDIDAS_CMP[m]) for m in medidas],
           "opciones_estilos": list(comparar.ESTILOS_CMP.items()), "colores": graficos.COLOR_CMP,
           "vacio": None, "grafico": None, "tabla": None, "aviso_estilo": None, "avisos": [], "con_cambio": False}
    if not anios:
        out["vacio"] = "Marca al menos un año para ver los datos (dos o más para compararlos)."
        return out
    if not sectores:
        out["vacio"] = "Marca al menos un sector para comparar."
        return out

    r = comparar.comparador(donde, anios, sectores, medida)
    if not r["filas"]:
        out["vacio"] = " ".join(r["avisos"]) or "No hay datos para esta combinación."
        return out

    # Cada forma de verlo solo vale para algunas combinaciones. Si no encaja, se usa otra y se dice por qué.
    usado, aviso = estilo, None
    if estilo == "tartas":
        if medida not in comparar.BASE_TARTAS:
            usado, aviso = "barras", ("Las tartas reparten un total, así que sirven para el público, la recaudación o "
                                      "el peso, no para precios ni para la parte de España: se muestran barras.")
        elif len(r["filas"]) < 2:
            usado, aviso = "barras", "Con un solo sector la tarta sería un círculo entero: marca otro sector."
    elif len(anios) == 1 and estilo != "barras":
        usado, aviso = "barras", "Con un solo año no hay evolución ni cambio: se muestran barras. Marca otro año."
    elif estilo == "indice" and comparar.MEDIDAS_CMP[medida]["tipo"] == "puntos":
        usado, aviso = "lineas", ("El crecimiento con base 100 no sirve para porcentajes (pasar del 10 % al 12 % no "
                                  "es «un 20 % más»): se muestran líneas.")
    out["aviso_estilo"] = aviso

    lugar = "España" if donde == "España" else config.corto(donde)
    anios_txt = str(anios[0]) if len(anios) == 1 else ", ".join(map(str, anios[:-1])) + " y " + str(anios[-1])
    lista = [f["nombre"].lower() for f in r["filas"]]
    lista_txt = lista[0] if len(lista) == 1 else ", ".join(lista[:-1]) + " y " + lista[-1]
    if usado == "tartas":
        base = comparar.BASE_TARTAS[medida]
        r = comparar.comparador(donde, anios, sectores, base)
        spec = graficos.tartas_comparador(r, base)
        titulo = f"Reparto {'del público' if base == 'publico' else 'de la recaudación'} entre {lista_txt} en {lugar}"
        conclusion = comparar.texto_tartas(r, base, donde)
        sub = f"Qué parte del total se lleva cada sector. Años: {anios_txt}."
        lectura = LECTURA_ESTILO["tartas"]
    else:
        spec = graficos.comparador(r, medida, usado)
        titulo = f"{comparar.MEDIDAS_CMP[medida]['nombre']} de {lista_txt} en {lugar}"
        conclusion = comparar.texto_comparador(r, medida, donde)
        sub = f"{comparar.MEDIDAS_CMP[medida]['pregunta']} Años: {anios_txt}."
        lectura = LECTURA_ESTILO["un_anio" if len(anios) == 1 else usado]
    out["grafico"] = {"id": "comparador", "titulo": titulo, "ancho": True, "spec": spec, "selector": None,
                      "sub": sub, "lectura": lectura, "conclusion": conclusion,
                      "alt": f"{titulo}, {anios_txt}. {conclusion}"}
    out["tabla"] = r
    out["avisos"] = r["avisos"]
    out["con_cambio"] = len(anios) > 1
    return out


def _destacados():
    """Cuatro comparaciones llamativas para el entreacto, calculadas siempre con los datos.

    Cada una lleva la cifra, la frase y el enlace que la abre en el comparador."""
    from flask import url_for
    from . import comparar
    todos = sorted(config.ANIOS)
    primero, ultimo = todos[0], todos[-1]
    sectores = list(comparar.SECTORES_CMP)

    def enlace(anios, medida, estilo, secs=None):
        return url_for("comparativa", cmp=1, anios=anios, sectores=secs or sectores,
                       medida=medida, estilo=estilo) + "#comparador"

    def fila(r, clave):
        return next((f for f in r["filas"] if f["clave"] == clave), None)

    # Para escribir bien: "los macrofestivales ganan", "del cine"
    articulo = {"cine": "el cine", "teatro": "el teatro", "conciertos": "los conciertos", "macro": "los macrofestivales"}

    def de(clave):
        return "del " + articulo[clave][3:] if articulo[clave].startswith("el ") else "de " + articulo[clave]

    def n(clave):
        return "n" if articulo[clave].startswith("los ") else ""

    out = []
    # 1. Quién gana más público en todo el periodo, frente al cine
    r = comparar.comparador("España", [primero, ultimo], sectores, "publico")
    orden = sorted(r["filas"], key=lambda f: f["cambio"]["valor"], reverse=True)
    top, cine = orden[0], fila(r, "cine")
    if top["clave"] != "cine" and cine:
        texto = (f"De {primero} a {ultimo}, {articulo[top['clave']]} gana{n(top['clave'])} un "
                 f"{top['cambio']['texto'].lstrip('+')} de público; el cine, un {cine['cambio']['texto'].lstrip('+')}.")
    else:
        texto = f"De {primero} a {ultimo}, el cine es el sector que más público gana."
    out.append({"cifra": top["cambio"]["texto"], "texto": texto,
                "url": enlace(todos, "publico", "indice")})

    # 2. La entrada más cara frente a la más barata, en el último año
    r = comparar.comparador("España", [ultimo], sectores, "gasto")
    orden = sorted([f for f in r["filas"] if f["valores"][0]], key=lambda f: f["valores"][0], reverse=True)
    caro, barato = orden[0], orden[-1]
    veces = caro["valores"][0] / barato["valores"][0]
    out.append({"cifra": "×" + formato.num(veces), "texto":
                f"En {ultimo}, cada espectador {de(caro['clave'])} paga {caro['textos'][0]}; "
                f"{de(barato['clave'])}, {barato['textos'][0]}. {formato.num(veces)} veces más.",
                "url": enlace([ultimo], "gasto", "barras")})

    # 3. El mayor cambio de recaudación del periodo
    r = comparar.comparador("España", [primero, ultimo], sectores, "dinero")
    top = max(r["filas"], key=lambda f: abs(f["cambio"]["valor"]))
    verbo = "pasa" if top["cambio"]["valor"] >= 0 else "cae"
    out.append({"cifra": top["cambio"]["texto"], "texto":
                f"La recaudación {de(top['clave'])} {verbo} de {top['textos'][0]} a {top['textos'][-1]} "
                f"entre {primero} y {ultimo}, en euros de cada año.",
                "url": enlace([primero, ultimo], "dinero", "cambio")})

    # 4. Cuánto peso gana o pierde el cine en el público
    r = comparar.comparador("España", todos, sectores, "peso")
    cine = fila(r, "cine")
    if cine:
        movimiento = "pierde" if cine["cambio"]["valor"] < 0 else "gana"
        out.append({"cifra": cine["cambio"]["texto"], "texto":
                    f"El cine {movimiento} peso: era el {cine['textos'][0]} del público de los cuatro sectores en "
                    f"{primero} y es el {cine['textos'][-1]} en {ultimo}.",
                    "url": enlace(todos, "peso", "lineas")})
    return out


def comparativa(args):
    """El comparador (años, sectores, qué medir, dónde y cómo verlo) y cuatro comparaciones destacadas."""
    comunidades = [c for c in datos.comparativa()["Comunidad"].unique() if c != "España"]
    return {"ruta": "/comparativa", "cmp": _comparador(args, comunidades), "destacados": _destacados()}


# ============================================================ FUENTES
def fuentes():
    conjuntos = []
    descripcion = {
        "cine": ("Cine", "Estadística de Cinematografía (ICAA) · Anuarios de Estadísticas Culturales 2024 y 2026 "
                         "(tablas 16.6 a 16.16)",
                 "Totales de España, por comunidad, por origen de la película y por país."),
        "teatro": ("Teatro", "Anuarios de Estadísticas Culturales 2024 y 2026 · tablas 15.22 y 15.23 (datos de la SGAE)",
                   "Totales de España, por comunidad y por tamaño del municipio. Solo obras teatrales."),
        "musica": ("Música popular", "Anuarios de Estadísticas Culturales 2024 y 2026 · tabla 15.28 (datos de la SGAE)",
                   "Conciertos y macrofestivales de España; conciertos por comunidad."),
        "comparativa_2023": ("Comparativa 2023", "Combinación de las tres tablas anteriores (CSV oficial de 2023)",
                             "Cine, teatro y conciertos en cada comunidad. El dashboard la recalcula para cada año."),
    }
    for archivo, (titulo, origen, contenido) in descripcion.items():
        df = datos.cargar(archivo)
        conjuntos.append({"archivo": archivo, "descarga": NOMBRES_DESCARGA[archivo], "titulo": titulo,
                          "origen": origen, "contenido": contenido, "filas": len(df), "columnas": len(df.columns)})
    return {"conjuntos": conjuntos, "glosario": config.GLOSARIO, "notas": config.NOTAS_GENERALES}
