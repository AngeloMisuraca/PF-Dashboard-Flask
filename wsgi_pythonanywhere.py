# Contenido que hay que PEGAR en el "WSGI configuration file" de PythonAnywhere
# (pestaña Web > Code > WSGI configuration file). Este archivo NO se ejecuta aquí.
#
# Sustituye TU_USUARIO por tu nombre de usuario de PythonAnywhere.
import sys

# Ruta exacta al directorio del proyecto (la carpeta que contiene app.py)
project_home = '/home/TU_USUARIO/flask_dashboard'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Importar la instancia app definida en app.py como 'application'
from app import app as application
