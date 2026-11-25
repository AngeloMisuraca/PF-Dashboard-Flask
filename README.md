# Ocio cultural en cifras

Dashboard interactivo hecho con **Flask** sobre el cine, el teatro y la música popular en España
(2022–2025), con datos públicos del Ministerio de Cultura.

**🔗 Web online:** https://pf-dashboard-flask.onrender.com/

> Está alojada en el plan gratuito de Render: si nadie la ha visitado en un rato, la primera carga
> puede tardar hasta un minuto mientras el servidor se reactiva. Después va con normalidad.

## Qué se puede hacer

- **Inicio:** las cifras clave de los tres sectores y cómo han evolucionado desde la pandemia.
- **Cine, Teatro y Música:** una página por sector con cifras clave, conclusiones calculadas a partir
  de los datos, gráficos interactivos, un ranking por comunidades y una tabla de datos completa.
  - Filtrar por año, indicador y comunidad.
  - Ordenar la tabla por cualquier columna, buscar y elegir cuántas filas ver.
  - Descargar cada gráfico como imagen PNG, generada en el servidor con **matplotlib**.
- **Comparativa:** un comparador en el que eliges los años, los sectores, qué medir (público,
  recaudación, gasto, peso…) y cómo verlo (barras, líneas, crecimiento, cambio o tartas).
- **Fuentes:** el origen de los datos, el método seguido y los CSV para descargar.

Cada gráfico incluye su conclusión y un apartado «Cómo leer este gráfico», y cada página tiene un
glosario.

## Datos

Los CSV de la carpeta `data/` proceden de fuentes públicas:

- Ministerio de Cultura: *Anuario de Estadísticas Culturales* (ediciones 2024 y 2026).
- ICAA: *Estadística de Cinematografía*.

Los datos de 2021 y anteriores están afectados por la pandemia, y así se avisa en la web.

## Tecnologías

| Parte | Herramienta |
|---|---|
| Servidor y rutas | Flask |
| Lectura y análisis de datos | pandas |
| Gráficos en imagen (PNG) | matplotlib |
| Plantillas | Jinja (herencia de `base.html` y macros) |
| Gráficos interactivos en la web | Chart.js |
| Hosting | Render (servidor gunicorn) |

## Estructura del proyecto

```
app.py              solo las rutas de la web
logic/
  config.py         colores, textos y constantes
  datos.py          lectura de los CSV con pandas
  analisis.py       cifras clave y conclusiones
  comparar.py       lógica del comparador
  graficos.py       prepara los datos de cada gráfico
  imagenes.py       dibuja los gráficos en PNG con matplotlib
  tablas.py         filtrar, ordenar y paginar las tablas
  formato.py        formato de números y porcentajes
  paginas.py        junta todo lo que necesita cada página
templates/          plantillas Jinja
static/             CSS, JavaScript e iconos
data/               los CSV
```

## Ejecutarlo en local

```bash
python -m venv venv
venv\Scripts\activate          # en Windows (en Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Después, abre http://127.0.0.1:5000

## Despliegue en Render

- **Tipo de servicio:** Web Service.
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
