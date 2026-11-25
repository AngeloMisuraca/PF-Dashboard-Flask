"""Configuración y textos del dashboard.

Aquí viven los datos "fijos": colores, nombres cortos, qué indicadores se
pueden comparar y las definiciones que se enseñan al usuario. Así el resto de
módulos no tienen textos ni constantes mezclados con la lógica.
"""

# ---------------------------------------------------------------- colores
COLORES = {
    "cine": "#E76F51",
    "teatro": "#6A4C93",
    "musica": "#2A9D8F",
    "macro": "#E9A23B",      # macrofestivales
    "usa": "#4A2C2A",        # granate oscuro (antes azul petróleo)
    "ue": "#E9C46A",
    "otros": "#BDB3AA",
    "tinta": "#2A1F1B",
    "gris": "#74675E",
    "rejilla": "#ECE6E1",
}

# Color de cada sector tal y como aparece en los gráficos del inicio
COLOR_SECTOR = {
    "Cine": COLORES["cine"],
    "Teatro": COLORES["teatro"],
    "Conciertos": COLORES["musica"],
    "Macrofestivales": COLORES["macro"],
}

# ------------------------------------------------------ nombres de comunidades
NOMBRES_CORTOS = {
    "Madrid (Comunidad de)": "Madrid",
    "Asturias (Principado de)": "Asturias",
    "Navarra (Comunidad Foral de)": "Navarra",
    "Murcia (Región de)": "Murcia",
    "Rioja (La)": "La Rioja",
    "Balears (Illes)": "Baleares",
    "Comunitat Valenciana": "C. Valenciana",
    "Castilla-La Mancha": "Castilla-La Mancha",
}


def corto(nombre):
    """Nombre abreviado de una comunidad (para que quepa en los gráficos)."""
    return NOMBRES_CORTOS.get(nombre, nombre)


# Orden lógico (de menor a mayor) de las categorías de tamaño de municipio
ORDEN_TAMANOS = [
    "Menos de 5.000 hab",
    "De 5.001 a 10.000 hab",
    "De 10.001 a 30.000 hab",
    "De 30.001 a 200.000 hab",
    "Zonas metropolitanas",
]

# Años del dashboard: los que tienen el mismo detalle en los tres sectores (comunidades, tamaño
# de municipio, origen de la película). datos.py descarta cualquier otro año de los CSV.
ANIOS = [2025, 2024, 2023, 2022]
ANIO_DEFECTO = 2025
ANIO_INICIO = min(ANIOS)
NOTA_ANIOS = (f"Los cambios se calculan respecto al año anterior; {min(ANIOS)} es el primero de la serie y "
              f"no tiene con qué compararse.")

# Qué pasa con los años que no están (se enseña en Fuentes, en la Comparativa y en "Ten en cuenta")
AVISO_PERIODO = {
    "antes": ("2021 y los años anteriores no se incluyen. 2020 y 2021 están marcados por la pandemia de COVID-19 "
              "(cierres, aforos limitados y espectáculos cancelados), así que cualquier comparación con ellos mide la "
              "caída y la recuperación, no la evolución normal del sector. Además, para 2021 no hay datos completos "
              "publicados: la fuente solo da totales de España, sin comunidades, y en teatro ni siquiera el número de "
              "espectadores. Los años anteriores a la pandemia no se han incorporado a este dashboard."),
    "ultimo": ("2025 es el último año publicado: llegó con el Anuario de Estadísticas Culturales 2026 (19 de noviembre "
               "de 2026). Son datos de primera publicación y la siguiente edición puede revisarlos. Al comparar "
               "ediciones, la de 2025 tenía dos erratas en el gasto medio de 2024 (conciertos y macrofestivales) que "
               "la de 2026 corrige; aquí se usan los valores corregidos."),
}

# -------------------------------------------------------- definición de sectores
SECTORES = {
    "cine": {
        "titulo": "Cine",
        "icono": "🎬",
        "archivo": "cine",
        "color": COLORES["cine"],
        "col_zona": "Categoría",
        "desglose_ccaa": "Comunidad autónoma",
        "desglose_defecto": "Comunidad autónoma",
        "lema": "El sector que más público mueve, y el más barato por entrada.",
        "intro": (
            "Estos datos salen del registro de taquilla de todas las salas de España que "
            "gestiona el ICAA (Instituto de Cinematografía). Aquí puedes ver cuánta gente "
            "va al cine, cuánto se recauda, de qué país son las películas que se ven y "
            "cómo cambia todo según la comunidad autónoma."
        ),
        "indicador_defecto": "Veces al cine por habitante",
        "indicadores": {
            "Espectadores (millones)": (
                "abs", "Entradas vendidas en el año, en millones. Cada entrada cuenta como un espectador."),
            "Recaudación (millones €)": (
                "abs", "Dinero total ingresado en taquilla, en millones de euros."),
            "Veces al cine por habitante": (
                "ratio", "Entradas vendidas divididas entre la población. Permite comparar de forma "
                         "justa comunidades grandes y pequeñas: dice cuántas veces va al año, de media, cada habitante."),
            "Precio medio entrada (€)": (
                "ratio", "Recaudación dividida entre espectadores: lo que cuesta de media una entrada."),
            "% espectadores que vieron cine español": (
                "ratio", "De cada 100 entradas vendidas en la comunidad, cuántas fueron de películas españolas."),
            "Espectadores por pantalla": (
                "ratio", "Entradas vendidas divididas entre el número de pantallas: indica cuánto se llena cada pantalla."),
        },
        "resumen": ["Categoría", "Año", "Espectadores (millones)", "Recaudación (millones €)",
                    "Precio medio entrada (€)", "Veces al cine por habitante", "% de los espectadores de España"],
        "col_pct_espectadores": "% de los espectadores de España",
        "col_pct_recaudacion": "% de la recaudación de España",
    },
    "teatro": {
        "titulo": "Teatro",
        "icono": "🎭",
        "archivo": "teatro",
        "color": COLORES["teatro"],
        "col_zona": "Zona",
        "desglose_ccaa": "Comunidad autónoma",
        "desglose_defecto": "Comunidad autónoma",
        "lema": "Poco público, pero con la entrada más cara si dejamos aparte los macrofestivales.",
        "intro": (
            "Datos de la SGAE (Sociedad General de Autores y Editores) recogidos en el Anuario de "
            "Estadísticas Culturales del Ministerio de Cultura. Se refieren solo a obras teatrales: "
            "no incluyen ópera, zarzuela ni danza. Muestran cuántas funciones se hacen, cuánta gente "
            "asiste y cuánto se recauda, por comunidad y por tamaño del municipio."
        ),
        "indicador_defecto": "Espectadores por función",
        "indicadores": {
            "Funciones": ("abs", "Número de representaciones (funciones) de obras teatrales en el año."),
            "Espectadores (miles)": ("abs", "Entradas vendidas en el año, en miles."),
            "Recaudación (miles €)": ("abs", "Dinero ingresado por entradas, en miles de euros."),
            "Espectadores por función": (
                "ratio", "Público medio de cada función: cuánto se llena una sala de media."),
            "Gasto medio por espectador (€)": (
                "ratio", "Recaudación dividida entre espectadores. La SGAE lo calcula incluyendo los "
                         "espectáculos gratuitos, así que baja cuando hay mucha función gratuita."),
        },
        "resumen": ["Zona", "Año", "Funciones", "Espectadores (miles)", "Recaudación (miles €)",
                    "Gasto medio por espectador (€)", "% de la recaudación de España"],
        "col_pct_espectadores": "% de los espectadores de España",
        "col_pct_recaudacion": "% de la recaudación de España",
    },
    "musica": {
        "titulo": "Música popular",
        "icono": "🎤",
        "archivo": "musica",
        "color": COLORES["musica"],
        "col_zona": "Categoría",
        "desglose_ccaa": "Conciertos por comunidad",
        "desglose_defecto": "España por tipo de evento",
        "lema": "Los macrofestivales son pocos, pero pesan enormemente en el dinero.",
        "intro": (
            "Datos de la SGAE recogidos en el Anuario de Estadísticas Culturales. Separamos dos cosas: "
            "los conciertos de música popular (que se pueden ver por comunidad) y los macrofestivales "
            "(que la fuente solo publica a nivel nacional, sin número de eventos)."
        ),
        "indicador_defecto": "Espectadores por concierto",
        "indicadores": {
            "Conciertos": ("abs", "Número de conciertos de música popular en el año."),
            "Espectadores (miles)": ("abs", "Entradas vendidas en el año, en miles."),
            "Recaudación (miles €)": ("abs", "Dinero ingresado por entradas, en miles de euros."),
            "Espectadores por concierto": (
                "ratio", "Público medio de cada concierto: indica si en esa comunidad predominan "
                         "los conciertos pequeños o los grandes."),
            "Gasto medio por espectador (€)": (
                "ratio", "Recaudación dividida entre espectadores. Incluye los espectáculos gratuitos "
                         "(criterio de la SGAE)."),
        },
        "resumen": ["Categoría", "Año", "Conciertos", "Espectadores (miles)", "Recaudación (miles €)",
                    "Gasto medio por espectador (€)", "% de la recaudación"],
        "col_pct_espectadores": "% de los espectadores",
        "col_pct_recaudacion": "% de la recaudación",
    },
}

# Columnas de "público" y "dinero" de cada sector (para los gráficos de tarta)
SECTORES["cine"].update(col_publico="Espectadores (millones)", col_dinero="Recaudación (millones €)", escala=1_000_000)
SECTORES["teatro"].update(col_publico="Espectadores (miles)", col_dinero="Recaudación (miles €)", escala=1_000)
SECTORES["musica"].update(col_publico="Espectadores (miles)", col_dinero="Recaudación (miles €)", escala=1_000)


# Para cada sector: ejes del gráfico de burbujas (x, y, tamaño)
BURBUJAS = {
    "cine": ("Precio medio entrada (€)", "Veces al cine por habitante", "Espectadores (millones)"),
    "teatro": ("Gasto medio por espectador (€)", "Espectadores por función", "Recaudación (miles €)"),
    "musica": ("Gasto medio por espectador (€)", "Espectadores por concierto", "Recaudación (miles €)"),
}

# ---------------------------------------------------- textos de cada gráfico
# Cada gráfico lleva: título, qué muestra (subtítulo) y cómo se lee.
GRAFICOS = {
    "publico_dinero": {
        "titulo": "¿Dónde está el público y dónde está el dinero?",
        "sub": "Para cada sector, qué parte del público total y qué parte de la recaudación total le corresponde.",
        "lectura": "Compara las dos barras de cada sector: si la barra rayada (dinero) es más alta que la "
                   "lisa (público), cada espectador de ese sector paga más que la media.",
    },
    "evolucion_cine": {
        "titulo": "La recuperación del cine",
        "sub": "Espectadores y recaudación de España, año a año. El porcentaje es el cambio respecto al año anterior.",
        "lectura": "Compara la altura de las dos barras de cada panel: si la recaudación crece más que el público, la entrada media es más cara.",
    },
    "origen_cine": {
        "titulo": "¿De dónde son las películas que se ven?",
        "sub": "Reparto del público según el país de origen de la película, año a año.",
        "lectura": "Cada barra suma el 100 % del público de ese año. Fíjate en cómo cambia el trozo del cine español.",
    },
    "evolucion_teatro": {
        "titulo": "El teatro: más público, pero no más dinero por persona",
        "sub": "Recaudación y público de España, año a año. El porcentaje es el cambio respecto al año anterior.",
        "lectura": "Si el público crece más rápido que la recaudación, el gasto medio por espectador baja.",
    },
    "tamano_teatro": {
        "titulo": "El teatro según el tamaño del municipio",
        "sub": "Qué porcentaje de las funciones, del público y de la recaudación de España se concentra en cada tipo de municipio.",
        "lectura": "Si la barra de recaudación es mucho más alta que la de funciones, ese tipo de municipio "
                   "recauda más de lo que le correspondería por su número de funciones.",
    },
    "tipo_musica": {
        "titulo": "Conciertos frente a macrofestivales",
        "sub": "Qué parte del público y qué parte del dinero de la música popular corresponde a cada tipo de evento.",
        "lectura": "Las dos barras suman el 100 %. Si el color de los macrofestivales ocupa más en la barra de "
                   "recaudación que en la de público, cada espectador de macrofestival paga más.",
    },
    "evolucion_musica": {
        "titulo": "El crecimiento de la música popular",
        "sub": "Recaudación total de cada año, dividida entre conciertos y macrofestivales.",
        "lectura": "Cada barra es un año. Compara el tamaño de cada color de una barra a otra para ver qué parte crece más.",
    },
    "gasto_musica": {
        "titulo": "Cuánto paga cada espectador",
        "sub": "Gasto medio por espectador, en euros, según tipo de evento.",
        "lectura": "El gasto medio es la recaudación dividida entre los espectadores (incluye espectáculos gratuitos).",
    },
    "ranking": {
        "titulo": "Ranking por comunidad autónoma",
        "sub": "Elige el indicador en el selector y el año en la cabecera. Las tres primeras barras aparecen más oscuras.",
        "lectura": "Los indicadores 'por habitante', 'por función' o 'precio medio' permiten comparar comunidades "
                   "de distinto tamaño; los totales (espectadores, recaudación) favorecen siempre a las más pobladas.",
    },
    "burbujas": {
        "titulo": "Precio frente a asistencia",
        "sub": "Cada burbuja es una comunidad. El tamaño de la burbuja indica el volumen total.",
        "lectura": "Arriba = más asistencia. A la derecha = entrada o gasto más caro. "
                   "Una comunidad arriba y a la izquierda tiene mucho público con precios bajos.",
    },
}

# -------------------------------------------------------------------- glosario
GLOSARIO = [
    ("Espectador (o asistencia)",
     "Cada entrada vendida. Una persona que va tres veces al cine cuenta como tres espectadores."),
    ("Recaudación",
     "Dinero total que se ingresa por la venta de entradas."),
    ("Gasto medio por espectador",
     "Recaudación dividida entre espectadores. En teatro y música lo calcula la SGAE incluyendo los espectáculos gratuitos."),
    ("Macrofestival",
     "Festival de música popular de gran formato. La fuente los contabiliza aparte de los conciertos."),
    ("Cuota (o %)",
     "Parte del total que corresponde a un grupo. Por ejemplo, la cuota del cine español es el porcentaje de entradas que son de películas españolas."),
    ("Por habitante",
     "Un dato dividido entre la población. Sirve para comparar territorios de distinto tamaño."),
]

NOTAS_GENERALES = [
    "Los espectadores son asistencias, no personas distintas.",
    "No se incluyen 2021 ni los años anteriores: están marcados por la pandemia de COVID-19 y no hay datos completos "
    "publicados. A principios de 2022 aún quedaban algunas restricciones, así que parte del crecimiento de 2023 es "
    "recuperación.",
    "2025 es el último año publicado (Anuario de Estadísticas Culturales 2026) y la próxima edición puede revisarlo.",
    "Cine (ICAA) y teatro/música (SGAE) vienen de fuentes distintas, con distinta cobertura: "
    "son comparables como orden de magnitud, no al céntimo.",
    "Las fuentes no publican géneros de película (comedia, drama...). La única categoría disponible es el país de origen.",
]
