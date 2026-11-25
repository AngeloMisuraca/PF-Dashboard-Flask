# Cómo publicar el dashboard (PythonAnywhere) y entregar

Fecha límite: **25/11/2026 a las 23:59**, por Clickedu: enlace al hosting + enlace al repositorio.

## 0. Antes de subir: comprueba que funciona en tu ordenador

```powershell
cd "C:\Users\angel\Desktop\big data\flask_dashboard"
venv\Scripts\Activate.ps1
python app.py
```
Abre http://127.0.0.1:5000 y recorre las 5 páginas del menú. Prueba cambiar el año, el indicador, la comunidad,
ordenar la tabla y usar el comparador.

## 1. Subir el código a GitHub

1. En github.com crea un repositorio nuevo (por ejemplo `ocio-cultural-dashboard`), **sin** marcar README.
2. En la terminal de VS Code, dentro de `flask_dashboard`:
   ```powershell
   git init
   git add .
   git commit -m "Dashboard de ocio cultural en España"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/ocio-cultural-dashboard.git
   git push -u origin main
   ```
3. Comprueba en GitHub que se ven `app.py`, `logic/`, `templates/`, `static/`, `data/` y `requirements.txt`,
   y que **no** aparece `venv/`.

## 2. PythonAnywhere (sigue el anexo del enunciado, con estos cambios)

1. Crea una cuenta **Beginner** (gratuita) en pythonanywhere.com.
2. **Consoles → Bash** y descarga el código desde GitHub (más cómodo que subir archivos uno a uno):
   ```bash
   git clone https://github.com/TU_USUARIO/ocio-cultural-dashboard.git flask_dashboard
   ```
   Si tu repositorio es privado, hazlo público o usa un token de acceso.
3. Crea el entorno virtual e instala las librerías. **Ojo: el anexo no menciona pandas y aquí es necesario.**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 meuentorn
   pip install -r flask_dashboard/requirements.txt
   ```
4. Pestaña **Web → Add a new web app → Manual configuration → Python 3.10**.
5. En **Virtualenv** escribe: `/home/TU_USUARIO/.virtualenvs/meuentorn`
6. En **Code**, abre el enlace **WSGI configuration file**, borra todo su contenido y pega el de
   `wsgi_pythonanywhere.py` (cambiando `TU_USUARIO`).
7. Guarda y pulsa el botón verde **Reload**.
8. Abre `https://TU_USUARIO.pythonanywhere.com`.

### Si sale «Something went wrong»
Pestaña **Web → Error log**: la última línea dice qué falla. Los errores típicos:
- `ModuleNotFoundError: No module named 'pandas'` → falta instalar las librerías en el entorno (paso 3) o el
  entorno no está puesto en «Virtualenv» (paso 5).
- `ModuleNotFoundError: No module named 'app'` → la ruta `project_home` del WSGI está mal escrita.
- `FileNotFoundError: ... data/cine.csv` → no se clonó la carpeta `data/`.

### Cada vez que cambies algo
En tu PC: `git add .`, `git commit -m "..."`, `git push`.
En la consola de PythonAnywhere: `cd flask_dashboard`, `git pull`, y pulsa **Reload** en la pestaña Web.

## 3. Entregar en Clickedu
- Enlace al hosting: `https://TU_USUARIO.pythonanywhere.com`
- Enlace al repositorio: `https://github.com/TU_USUARIO/ocio-cultural-dashboard`

---

# Dónde se cumple cada punto de la rúbrica

| Rúbrica | Cómo se cumple | Dónde verlo |
|---|---|---|
| **Arquitectura del backend (20 %)** | `app.py` solo tiene rutas. La lógica está en módulos independientes con una sola responsabilidad: leer datos, analizar, dibujar, formatear tabla, montar la página. Validación de todos los parámetros de la URL. Caché de CSV y de gráficos. | `app.py`, `logic/` |
| **Aplicación alojada online (10 %)** | `requirements.txt`, `.gitignore`, `wsgi_pythonanywhere.py` y esta guía. Rutas de datos absolutas para que funcione en el hosting. | este archivo |
| **Relevancia y didáctica del análisis (40 %)** | Cada página tiene cifras clave, «Lo que dicen los datos», y cada gráfico lleva su subtítulo, una **conclusión calculada desde los datos** y un «Cómo leer este gráfico». Glosario y avisos metodológicos. Página de fuentes y método. | todas las páginas, `logic/analisis.py` |
| **Diseño: usabilidad, estructura, estilos (30 %)** | Un color por sector, tarjetas, menú fijo, responsive (probado a 390 px), tabla con cabecera fija y orden por columnas, accesible (alt en gráficos, foco visible, `aria-sort`, enlace «saltar al contenido»), estilos de impresión, controles segmentados, tabla con barras de datos y animaciones que respetan `prefers-reduced-motion`. **Comparador** en el que se eligen años, sectores, qué medir y cómo verlo (barras, líneas, crecimiento, cambio o tartas). | `static/css/style.css`, `static/js/app.js`, `templates/` |

## Requisitos del enunciado

| # | Requisito | Cumplido en |
|---|---|---|
| 1 | CSV de un portal público | `data/*.csv` (Ministerio de Cultura); descargables en `/fuentes` |
| 2 | Flask | `app.py` |
| 3 | Filtrar, ordenar, mostrar más o menos | Año, indicador, comunidad, «Ver por», buscador, ordenar por columna, vista resumen/completa, 10/25/todas las filas |
| 4 | Formato libre | Tarjetas, gráficos, tabla, listas de hallazgos |
| 5 | Páginas dinámicas con Jinja | `templates/` (herencia de `base.html` y macros en `_macros.html`) |
| 6 | `app.py` solo rutas; lógica modular | `logic/` |
| 7 | Gráficos (matplotlib) | En pantalla, `logic/graficos.py` prepara los datos y `static/js/graficos.js` los dibuja interactivos (Chart.js). Cada gráfico de Cine, Teatro y Música tiene «Descargar como imagen (PNG)»: la ruta `/grafico/<sector>/<gráfico>.png` lo dibuja en el servidor con **matplotlib** (`logic/imagenes.py`) con los mismos datos y filtros |
| 8 | Hosting (opcional) | esta guía |
| 9 | Didáctico | explicaciones, conclusiones y glosario en cada página |

> Nota: las tipografías (Big Shoulders Display y Hanken Grotesk) se cargan desde Google Fonts. Si no hay conexión, el navegador usa la fuente del sistema y todo sigue funcionando.
