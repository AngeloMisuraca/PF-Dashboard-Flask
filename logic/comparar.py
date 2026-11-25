"""El comparador entre años: las reglas de cómo se compara un año con otro.

Todas las cifras, gráficos y frases del comparador salen de aquí, así que usan el mismo criterio:

1. Se comparan los años de config.ANIOS (2022 a 2025): los únicos con el mismo detalle en los
   tres sectores (comunidades, tamaño de municipio, origen de la película...).
2. Todos los cambios entre años se dan en %:
     · cantidades (entradas, euros) → cuánto suben o bajan (+12,4 %)
     · medias (gasto por espectador) → en % y también en euros (+12,4 %, +0,40 €)
     · porcentajes (peso en el público, reparto) → cuánto crece o se reduce ese porcentaje
       (pasar del 10 % al 12 % es un +20 %)
3. El total de España es el publicado por la fuente, no la suma de comunidades, y en las
   comunidades solo hay conciertos (los macrofestivales solo tienen total de España).
4. Las comunidades con menos del 1 % del público de España del sector se marcan como "base
   pequeña": su % de cambio se dispara con muy pocas entradas.
5. Los euros son corrientes (sin descontar la inflación).
"""
from functools import lru_cache

from . import config, datos, formato
from .formato import num, pct, signo

A, B = sorted(config.ANIOS)[-2:]       # año de partida y de llegada por defecto: los dos últimos
UMBRAL_BASE = 1.0                      # % del público del sector por debajo del cual la base es "pequeña"


def _tendencia(v):
    """'sube', 'baja' o 'igual': da el color verde o rojo de cada cambio."""
    return "sube" if v > 0.05 else ("baja" if v < -0.05 else "igual")


@lru_cache(maxsize=16)
def totales(a=None, b=None):
    """Público, dinero y gasto medio de los cuatro sectores juntos, cada año (para la portada)."""
    out = {}
    for anio in (a or A, b or B):
        r = datos.resumen_sectores(anio).set_index("Sector")
        out[anio] = {"publico": r["espectadores_miles"].sum(), "dinero": r["recaudacion_miles"].sum(),
                     "sectores": r}
        out[anio]["gasto"] = out[anio]["dinero"] / out[anio]["publico"]
    return out


# ============================================================ el comparador (lo que elige el usuario)
# Sectores que se pueden elegir: clave de la URL, nombre en pantalla y nombre en datos.comparativa()
SECTORES_CMP = {
    "cine": ("Cine", "Cine"),
    "teatro": ("Teatro", "Teatro"),
    "conciertos": ("Conciertos", "Música popular - conciertos"),
    "macro": ("Macrofestivales", "Música popular - macrofestivales"),
}

# Para escribir las frases con su artículo: "el cine se lleva", "los macrofestivales ganan"
ARTICULO = {"cine": "el cine", "teatro": "el teatro", "conciertos": "los conciertos", "macro": "los macrofestivales"}
SUJETO = {"publico": "el público", "dinero": "la recaudación", "gasto": "el gasto por espectador",
          "peso": "el peso en el público", "cuota": "la parte de España"}


def de_sector(clave):
    """'del cine', 'de los conciertos'."""
    art = ARTICULO[clave]
    return "del " + art[3:] if art.startswith("el ") else "de " + art

# Qué se compara. tipo: "cantidad" y "media" cambian en %; "puntos" cambia en puntos.
MEDIDAS_CMP = {
    "publico": {"nombre": "Público", "pregunta": "¿Cuánta gente va?", "tipo": "cantidad", "eje": "Millones de espectadores"},
    "dinero": {"nombre": "Recaudación", "pregunta": "¿Cuánto dinero entra?", "tipo": "cantidad",
               "eje": "Millones de euros"},
    "gasto": {"nombre": "Gasto por espectador", "pregunta": "¿Cuánto paga cada persona?", "tipo": "media",
              "eje": "Euros por espectador"},
    "peso": {"nombre": "Peso en el público", "pregunta": "¿Qué parte del público se lleva?", "tipo": "puntos",
             "eje": "% del público"},
    "cuota": {"nombre": "Parte de España", "pregunta": "¿Qué parte del sector en España está aquí?",
              "tipo": "puntos", "eje": "% del público de España", "solo_comunidad": True},
}

ESTILOS_CMP = {
    "barras": "Barras",
    "lineas": "Líneas",
    "indice": "Crecimiento (100 = primer año)",
    "cambio": "Solo el cambio",
    "tartas": "Tartas (reparto)",
}

# Con qué cantidad se dibuja el reparto en tartas: el peso es el reparto del público
BASE_TARTAS = {"publico": "publico", "peso": "publico", "dinero": "dinero"}


def texto_tartas(r, base, ambito):
    """Conclusión de las tartas: quién se lleva más y qué porción cambia más entre el primer y el último año."""
    filas, anios = r["filas"], r["anios"]
    lugar = "España" if ambito == "España" else config.corto(ambito)
    que = "del público" if base == "publico" else "del dinero"
    # redondeados igual que en las tartas (graficos.tartas_comparador), para que las cifras coincidan
    pcts = [[round(v, 2) for v in p] for p in _repartos(filas, len(anios))]
    ultimo = [p[-1] for p in pcts]
    i = max(range(len(filas)), key=lambda k: ultimo[k])
    lleva = "se llevan" if ARTICULO[filas[i]["clave"]].startswith("los") else "se lleva"
    texto = (f"En {anios[-1]}, {ARTICULO[filas[i]['clave']]} {lleva} el {pct(ultimo[i])} {que} de los sectores "
             f"marcados en {lugar}.")
    if len(anios) > 1:
        difs = [(p[-1] / p[0] - 1) * 100 if p[0] else 0 for p in pcts]
        j = max(range(len(filas)), key=lambda k: abs(difs[k]))
        verbo = "crece" if difs[j] > 0 else "se reduce"
        texto += (f" De {anios[0]} a {anios[-1]}, la porción que más cambia es la {de_sector(filas[j]['clave'])}: "
                  f"{verbo} un {num(abs(difs[j]))} %.")
    return texto


def _repartos(filas, n_anios):
    """Porcentaje de cada sector sobre la suma de los sectores marcados, año a año."""
    totales = [sum(f["valores"][k] or 0 for f in filas) for k in range(n_anios)]
    return [[(f["valores"][k] or 0) / totales[k] * 100 if totales[k] else 0 for k in range(n_anios)] for f in filas]


def _valores_ambito(ambito, anio):
    """Las cinco medidas de cada sector en un lugar (España o una comunidad) y un año."""
    df = datos.comparativa(anio)
    df = df[df["Comunidad"] == ambito].set_index("Sector")
    total_pub = df["Espectadores (miles)"].sum()        # el público de todos los sectores del lugar
    out = {}
    for clave, (_n, nombre_datos) in SECTORES_CMP.items():
        if nombre_datos not in df.index:
            continue
        f = df.loc[nombre_datos]
        pub, din = f["Espectadores (miles)"], f["Recaudación (miles €)"]
        if formato.vacio(pub):
            continue
        gasto = f["Gasto medio por espectador (€)"]
        if formato.vacio(gasto) and not formato.vacio(din) and pub:
            gasto = din / pub                               # miles de € / miles de personas = € por persona
        cuota = f["% de los espectadores de España en ese sector"] if ambito != "España" else None
        out[clave] = {"publico": float(pub), "dinero": None if formato.vacio(din) else float(din),
                      "gasto": None if formato.vacio(gasto) else float(gasto),
                      "peso": float(pub / total_pub * 100) if total_pub else None,
                      "cuota": None if formato.vacio(cuota) else float(cuota)}
    return out


def texto_medida(medida, v):
    """Valor con su unidad, como se lee en pantalla."""
    if v is None:
        return "–"
    if medida == "publico":
        return formato.desde_miles(v)
    if medida == "dinero":
        return formato.euros_desde_miles(v)
    if medida == "gasto":
        return formato.euros(v)
    return pct(v)


def valor_eje(medida, v):
    """Valor en la unidad del eje del gráfico (millones para público y dinero)."""
    if v is None:
        return None
    return v / 1000 if medida in ("publico", "dinero") else v


def cambio_medida(medida, a, b):
    """Cambio de a a b con la regla de la medida: % para cantidades y medias, puntos para porcentajes."""
    if a is None or b is None:
        return {"valor": None, "texto": "–", "secundario": "", "tendencia": None}
    if not a:
        return {"valor": None, "texto": "–", "secundario": "", "tendencia": None}
    r = (b / a - 1) * 100
    secundario = signo(b - a, 2, " €") if medida == "gasto" else ""
    return {"valor": r, "texto": signo(r), "secundario": secundario, "tendencia": _tendencia(r)}


def comparador(ambito, anios, sectores, medida):
    """Datos del comparador: una fila por sector con el valor de cada año elegido y el cambio
    entre el primero y el último. También devuelve avisos para leer bien la comparación."""
    anios = sorted(anios)
    por_anio = {a: _valores_ambito(ambito, a) for a in anios}
    filas, avisos = [], []
    for clave in sectores:
        if not all(clave in por_anio[a] for a in anios):
            continue
        vals = [por_anio[a][clave][medida] for a in anios]
        if all(v is None for v in vals):
            continue
        c = cambio_medida(medida, vals[0], vals[-1]) if len(anios) > 1 else None
        cuota = por_anio[anios[-1]][clave]["cuota"]
        filas.append({"clave": clave, "nombre": SECTORES_CMP[clave][0], "valores": vals,
                      "textos": [texto_medida(medida, v) for v in vals], "cambio": c,
                      "pequena": cuota is not None and cuota < UMBRAL_BASE})

    elegidos_sin_datos = [SECTORES_CMP[s][0] for s in sectores if s not in [f["clave"] for f in filas]]
    if elegidos_sin_datos:
        n = "n" if len(elegidos_sin_datos) > 1 else ""
        motivo = (f" no tiene{n} datos por comunidad (solo hay total de España)" if ambito != "España"
                  else f" no tiene{n} datos de esta medida")
        avisos.append(f"{', '.join(elegidos_sin_datos)}{motivo}, así que no aparece{n}.")
    if len(anios) > 1:
        orden = sorted(config.ANIOS)
        if orden.index(anios[-1]) - orden.index(anios[0]) > 1:
            avisos.append(f"El cambio va de {anios[0]} a {anios[-1]}: es el acumulado de todo el periodo, no el de un año.")
    if medida in ("dinero", "gasto"):
        avisos.append("Euros de cada año, sin descontar la inflación: una subida pequeña puede ser, en realidad, una bajada.")
    if medida == "peso":
        quienes = "cine, teatro, conciertos y macrofestivales" if ambito == "España" else "cine, teatro y conciertos"
        avisos.append(f"El peso se calcula sobre el público de {quienes} juntos en {config.corto(ambito)}. "
                      "Su cambio es cuánto crece o se reduce ese porcentaje: pasar del 10 % al 12 % es un +20 %.")
    if medida == "cuota":
        avisos.append("Qué parte del público de cada sector en España va en esta comunidad. Su cambio es cuánto "
                      "crece o se reduce esa parte, en %.")
    pequenas = [f["nombre"] for f in filas if f["pequena"]]
    if pequenas and medida != "cuota":
        avisos.append(f"Base pequeña en {', '.join(pequenas)}: menos del 1 % del público de España del sector, "
                      "así que su % de cambio se mueve con muy pocas entradas.")
    return {"filas": filas, "anios": anios, "avisos": avisos}


def texto_comparador(r, medida, ambito):
    """Conclusión en una o dos frases, escrita según lo que sube y lo que baja."""
    filas, anios = r["filas"], r["anios"]
    if not filas:
        return ""
    lugar = "España" if ambito == "España" else config.corto(ambito)
    nombre = MEDIDAS_CMP[medida]["nombre"].lower()
    if len(anios) == 1 and len(filas) == 1:
        f = filas[0]
        return (f"En {anios[0]}, en {lugar}, {SUJETO[medida]} {de_sector(f['clave'])} es {f['textos'][0]}. "
                "Marca otro año para ver cómo cambia.")
    if len(anios) == 1:
        orden = sorted(filas, key=lambda f: f["valores"][0] or 0, reverse=True)
        texto = f"En {anios[0]}, en {lugar}, el sector con más {nombre} es {orden[0]['nombre'].lower()} ({orden[0]['textos'][0]})"
        if len(orden) > 1:
            texto += f" y el que menos, {orden[-1]['nombre'].lower()} ({orden[-1]['textos'][0]})"
        return texto + ". Elige otro año para ver cómo cambia."
    validas = [f for f in filas if f["cambio"] and f["cambio"]["valor"] is not None]
    if not validas:
        return ""
    validas.sort(key=lambda f: f["cambio"]["valor"], reverse=True)
    suben = [f for f in validas if f["cambio"]["tendencia"] == "sube"]
    bajan = [f for f in validas if f["cambio"]["tendencia"] == "baja"]

    def lista(fs):
        partes = [f"{f['nombre'].lower()} ({f['cambio']['texto']})" for f in fs]
        return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " y " + partes[-1]

    sujeto = {"publico": "el público", "dinero": "la recaudación", "gasto": "el gasto por espectador",
              "peso": "el peso en el público", "cuota": "la parte de España"}[medida]
    iguales = [f for f in validas if f["cambio"]["tendencia"] == "igual"]
    frases = []
    if suben:
        frases.append(f"sube en {lista(suben)}")
    if bajan:
        frases.append(f"baja en {lista(bajan)}")
    if iguales:
        frases.append(f"se mantiene en {lista(iguales)}")
    unidas = frases[0] if len(frases) == 1 else ", ".join(frases[:-1]) + " y " + frases[-1]
    texto = f"De {anios[0]} a {anios[-1]}, en {lugar}, {sujeto} {unidas}."
    if len(validas) > 1 and suben:
        texto += f" Donde más crece es en {validas[0]['nombre'].lower()}."
    elif len(validas) > 1 and not suben:
        texto += f" Donde menos cae es en {validas[0]['nombre'].lower()}."
    return texto
