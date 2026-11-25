"""Servidor Flask del dashboard.

Este archivo SOLO contiene rutas: recibe la petición, pide los datos a logic/ y
entrega la plantilla. Toda la lógica (CSV, análisis, gráficos) está en logic/.
"""
from flask import Flask, Response, abort, redirect, render_template, request, send_from_directory, url_for

from logic import datos, paginas

app = Flask(__name__)


@app.context_processor
def textos_comunes():
    """Datos que usan todas las plantillas (la explicación de los años elegibles)."""
    from logic import config
    return {"nota_anios": config.NOTA_ANIOS, "anio_inicio": config.ANIO_INICIO,
            "anio_fin": max(config.ANIOS), "aviso_periodo": config.AVISO_PERIODO}


@app.route("/")
def inicio():
    return render_template("index.html", **paginas.inicio(request.args))


@app.route("/cine")
def cine():
    return render_template("sector.html", **paginas.sector("cine", request.args))


@app.route("/teatro")
def teatro():
    return render_template("sector.html", **paginas.sector("teatro", request.args))


@app.route("/musica")
def musica():
    return render_template("sector.html", **paginas.sector("musica", request.args))


@app.route("/comparativa")
def comparativa():
    return render_template("comparativa.html", **paginas.comparativa(request.args))


@app.route("/grafico/<sector>/<clave>.png")
def grafico_png(sector, clave):
    """Un gráfico de un sector como imagen PNG, dibujado con matplotlib (logic/imagenes.py)."""
    if sector not in ("cine", "teatro", "musica"):
        abort(404)
    png = paginas.imagen_sector(sector, clave, request.args)
    if png is None:
        abort(404)
    return Response(png, mimetype="image/png",
                    headers={"Content-Disposition": f'inline; filename="{sector}-{clave}.png"'})


@app.route("/tartas")
def tartas():
    """Las tartas ahora son una forma de verlo dentro del comparador: los enlaces antiguos llevan allí."""
    return redirect(url_for("comparativa", estilo="tartas") + "#comparador", code=301)


@app.route("/fuentes")
def fuentes():
    return render_template("fuentes.html", **paginas.fuentes())


@app.route("/descargar/<archivo>")
def descargar(archivo):
    """Descarga de los CSV (solo los de la lista, nunca un nombre cualquiera)."""
    if archivo not in paginas.NOMBRES_DESCARGA.values():
        abort(404)
    return send_from_directory(datos.CARPETA_DATOS, archivo, as_attachment=True)


@app.errorhandler(404)
def no_encontrado(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
