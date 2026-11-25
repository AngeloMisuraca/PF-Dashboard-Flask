"""Gráficos como imagen (PNG) con matplotlib.

En la web los gráficos son interactivos (los dibuja el navegador con Chart.js). Este módulo
dibuja en el servidor, con matplotlib, los MISMOS datos de cada gráfico de las páginas de
sector (los diccionarios que prepara graficos.py) para descargarlos como imagen: con sus
colores, sus valores escritos y su título, listos para un trabajo o una presentación.

No calcula nada: solo traduce cada "tipo" de gráfico a matplotlib.
  barras      barras verticales agrupadas (con valor encima y texto dentro)
  apiladas    barras verticales apiladas con el total encima
  barras_h    barras horizontales (ranking de comunidades)
  apiladas_h  barras horizontales al 100 %
  burbujas    dispersión con tamaño y líneas de media
  paneles     varios de los anteriores, uno al lado del otro
"""
import io
import re
import textwrap

import matplotlib

matplotlib.use("Agg")                      # sin ventana: solo genera imágenes en el servidor
import matplotlib.pyplot as plt  # noqa: E402

TINTA, GRIS, REJILLA, FONDO = "#241A16", "#74675E", "#ECE6E1", "#FFFFFF"
FUENTE = "Fuente: Ministerio de Cultura (Anuario de Estadísticas Culturales) y Estadística de Cinematografía (ICAA)."

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": TINTA,
    "axes.edgecolor": REJILLA, "axes.labelcolor": GRIS, "xtick.color": TINTA, "ytick.color": TINTA,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
})


# ============================================================ utilidades
def _lista(color, n):
    """Un color o una lista de colores, siempre como lista de n."""
    return list(color) if isinstance(color, (list, tuple)) else [color] * n


def _etiqueta(e):
    """Las etiquetas de varias líneas vienen como lista: se unen con saltos de línea."""
    return "\n".join(e) if isinstance(e, (list, tuple)) else str(e)


def _oscuro(hex_color):
    h = hex_color.lstrip("#")[:6]
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.62


def _sin_eje_y(ax):
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)


def _leyenda(ax, n_series):
    if n_series > 1:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=min(n_series, 4), frameon=False)


# ============================================================ tipos de gráfico
def _barras(ax, s):
    series, etiquetas = s["series"], [_etiqueta(e) for e in s["etiquetas"]]
    n, ancho = len(series), 0.8 / max(len(s["series"]), 1)
    x = range(len(etiquetas))
    tope = max((v for se in series for v in se["valores"] if v is not None), default=1)
    for i, se in enumerate(series):
        pos = [k - 0.4 + ancho * (i + 0.5) for k in x]
        colores = _lista(se["color"], len(etiquetas))
        vals = [v or 0 for v in se["valores"]]
        if se.get("claro"):           # serie "clara": relleno suave con borde del color
            barras = ax.bar(pos, vals, ancho * 0.92, color=[c + "55" for c in colores], edgecolor=colores,
                            linewidth=1.5, label=se["nombre"])
        else:
            barras = ax.bar(pos, vals, ancho * 0.92, color=colores, label=se["nombre"])
        for b, texto, v in zip(barras, se["textos"], se["valores"]):
            if v is not None:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + tope * 0.015, texto, ha="center",
                        va="bottom", fontsize=8.5 if n > 2 else 9.5, fontweight="bold")
        for b, dentro in zip(barras, se.get("dentro") or []):
            if dentro and b.get_height() > tope * 0.12:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() / 2, _etiqueta(dentro), ha="center",
                        va="center", color="white", fontsize=8.5, fontweight="bold")
    ax.set_xticks(list(x), etiquetas)
    ax.set_ylim(0, (s.get("max") or tope * 1.15))
    if s.get("eje_y"):
        ax.yaxis.grid(True, color=REJILLA)
        ax.set_axisbelow(True)
        if s.get("unidad") == "%":
            ax.yaxis.set_major_formatter(lambda v, _p: f"{v:.0f} %")
    else:
        _sin_eje_y(ax)
    if s.get("leyenda") is not False:
        _leyenda(ax, n)


def _apiladas(ax, s):
    etiquetas, base = [_etiqueta(e) for e in s["etiquetas"]], [0.0] * len(s["etiquetas"])
    totales_num = [sum(se["valores"][k] or 0 for se in s["series"]) for k in range(len(etiquetas))]
    for se in s["series"]:
        vals = [v or 0 for v in se["valores"]]
        barras = ax.bar(etiquetas, vals, 0.55, bottom=base, color=se["color"], label=se["nombre"])
        for b, v, texto, t in zip(barras, vals, se["textos"], totales_num):
            if t and v / t > 0.08:
                ax.text(b.get_x() + b.get_width() / 2, b.get_y() + v / 2, texto, ha="center", va="center",
                        color="white" if _oscuro(se["color"]) else TINTA, fontsize=9, fontweight="bold")
        base = [a + v for a, v in zip(base, vals)]
    for k, texto in enumerate(s.get("totales") or []):
        ax.text(k, base[k] * 1.02, texto, ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(base) * 1.15)
    _sin_eje_y(ax)
    _leyenda(ax, len(s["series"]))


def _barras_h(ax, s):
    se = s["series"][0]
    etiquetas = [_etiqueta(e) for e in s["etiquetas"]]
    vals = [v or 0 for v in se["valores"]]
    y = range(len(etiquetas))
    ax.barh(list(y), vals, 0.75, color=_lista(se["color"], len(vals)))
    ax.set_yticks(list(y), etiquetas)
    ax.invert_yaxis()                     # el primero del ranking, arriba
    tope = max((abs(v) for v in vals), default=1)
    for k, (v, texto) in enumerate(zip(vals, se["textos"])):
        ax.text(v + (tope * 0.01 if v >= 0 else -tope * 0.01), k, " " + texto + " ", va="center",
                ha="left" if v >= 0 else "right", fontsize=8.5, fontweight="bold" if k < 3 else "normal")
    if s.get("divergente"):
        ax.axvline(0, color=GRIS, linewidth=1)
        ax.set_xlim(min(min(vals) * 1.3, 0), max(max(vals) * 1.3, 0))
    else:
        ax.set_xlim(0, tope * 1.18)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def _apiladas_h(ax, s):
    etiquetas = [_etiqueta(e) for e in s["etiquetas"]]
    y, base = list(range(len(etiquetas))), [0.0] * len(etiquetas)
    for se in s["series"]:
        vals = [v or 0 for v in se["valores"]]
        ax.barh(y, vals, 0.7, left=base, color=se["color"], edgecolor="white", linewidth=1.5, label=se["nombre"])
        for k, (v, texto) in enumerate(zip(vals, se["textos"])):
            if v >= 6.5:
                ax.text(base[k] + v / 2, k, texto, ha="center", va="center", fontsize=8.5, fontweight="bold",
                        color="white" if _oscuro(se["color"]) else TINTA)
        base = [a + v for a, v in zip(base, vals)]
    ax.set_yticks(y, etiquetas)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _leyenda(ax, len(s["series"]))


def _burbujas(ax, s):
    puntos = s["puntos"]
    ax.scatter([p["x"] for p in puntos], [p["y"] for p in puntos], s=[(p["r"] * 1.6) ** 2 for p in puntos],
               color=s["color"], alpha=0.45, edgecolors=s["color"], linewidths=1.2)
    for p in puntos:
        ax.annotate(p["nombre"], (p["x"], p["y"]), xytext=(0, p["r"] * 0.9 + 3), textcoords="offset points",
                    ha="center", fontsize=8, color=TINTA)
    for valor, linea in ((s.get("media_x"), ax.axvline), (s.get("media_y"), ax.axhline)):
        if valor is not None:
            linea(valor, color=GRIS, linestyle="--", linewidth=1)
    ax.set_xlabel(s.get("eje_x", ""))
    ax.set_ylabel(s.get("eje_y", ""))
    ax.grid(True, color=REJILLA)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(True)
    ax.margins(0.12)


DIBUJAR = {"barras": _barras, "apiladas": _apiladas, "barras_h": _barras_h, "apiladas_h": _apiladas_h,
           "burbujas": _burbujas}


# ============================================================ la imagen completa
def _sin_instrucciones(texto):
    """Quita las frases que solo tienen sentido en la web ('Elige el indicador en el selector...')."""
    frases = re.split(r"(?<=\.)\s+", texto or "")
    return " ".join(f for f in frases if not re.match(r"(Elige|Cambia|Pulsa|Pasa el ratón)", f)).strip()


def png(spec, titulo, subtitulo=""):
    """Dibuja el gráfico 'spec' con matplotlib y devuelve los bytes del PNG (o None si el tipo no existe)."""
    paneles = spec["paneles"] if spec.get("tipo") == "paneles" else [spec]
    if any(p.get("tipo") not in DIBUJAR for p in paneles):
        return None
    sub = textwrap.wrap(_sin_instrucciones(subtitulo), 125)
    pie = textwrap.wrap(" ".join(t for t in [spec.get("nota", ""), FUENTE] if t), 165)
    # alturas en pulgadas: cabecera (título + líneas del subtítulo), gráfico y pie
    cabecera = 0.62 + 0.24 * len(sub)
    grafico = max(max(p.get("alto", 360) for p in paneles) / 100 + 0.4, 3.2)
    pie_alto = 0.18 + 0.2 * len(pie)
    alto = cabecera + grafico + pie_alto
    fig, ejes = plt.subplots(1, len(paneles), figsize=(11, alto), squeeze=False)
    for ax, p in zip(ejes[0], paneles):
        DIBUJAR[p["tipo"]](ax, p)
        if p.get("titulo") and len(paneles) > 1:
            ax.set_title(p["titulo"], fontsize=10.5, fontweight="bold", loc="left")
    fig.text(0.02, 1 - 0.18 / alto, titulo, ha="left", va="top", fontsize=14, fontweight="bold")
    if sub:
        fig.text(0.02, 1 - 0.52 / alto, "\n".join(sub), ha="left", va="top", fontsize=9.5, color=GRIS,
                 linespacing=1.35)
    fig.text(0.02, 0.06 / alto, "\n".join(pie), ha="left", va="bottom", fontsize=8, color=GRIS, linespacing=1.3)
    fig.tight_layout(rect=(0, pie_alto / alto, 1, 1 - cabecera / alto))
    salida = io.BytesIO()
    fig.savefig(salida, format="png", dpi=150)
    plt.close(fig)                       # libera la memoria de la figura
    return salida.getvalue()
