# -*- coding: utf-8 -*-
import os
import sys
import platform
from dotenv import load_dotenv

# El archivo de entorno se llama '.env'.
# Buscamos primero relativo a este archivo (config/../.env), luego en CWD como fallback.
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(_env_path):
    load_dotenv(_env_path)
else:
    load_dotenv()  # fallback: busca .env en el directorio de trabajo


def obtener_ruta_base():
    """Detecta si estamos en un .exe o en un script normal para resolver rutas relativas."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# --- RUTAS DEL PROYECTO ---
BASE_DIR = obtener_ruta_base()
DATA_DIR = os.path.join(BASE_DIR, 'data')


# Buscar que sino exista la carpeta se crea. tener en cuenta
# que el proceso que la ruta debe ser agnostico

# DOWNLOAD_DIR: configurable via env (DOWNLOAD_DIR=ruta) o por defecto documentos/ del proyecto.
_download_env = os.getenv('DOWNLOAD_DIR', '').strip("'\"")
DOWNLOAD_DIR = _download_env if _download_env else os.path.join(BASE_DIR, 'documentos')

# Crear la carpeta de descargas si no existe
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- CREDENCIALES SECOP II ---
USUARIO_SECOP = os.getenv('USUARIO_SECOP')
PASS_SECOP = os.getenv('PASS_SECOP')

# --- CREDENCIALES ONBASE ---
USER_ONBASE = os.getenv('USER_ONBASE')
PASS_ONBASE = os.getenv('PASS_ONBASE')

# --- URLS ---
URL_LOGIN_SECOP = os.getenv('URL_LOGIN_SECOP')
URL_SECOP = os.getenv('URL_SECOP')
URL_ONBASE = os.getenv('URL_ONBASE')

# --- CONFIGURACION GOOGLE SHEETS ---
BD_NAME = os.getenv('HOJA_DATOS')
WORKSHEET_NAME = os.getenv('WORKSHEET')
CREDENCIALES_JSON = os.path.join(DATA_DIR, 'client_sheet.json')

# Si el archivo de credenciales no esta en data/, buscar en la raiz del proyecto
if not os.path.exists(CREDENCIALES_JSON):
    CREDENCIALES_JSON = os.path.join(BASE_DIR, 'client_sheet.json')

# --- CONFIGURACION DEL ROBOT ---
NOMBRE_ESTACION = os.getenv('NOMBRE_ESTACION')
CASO_PRUEBA = os.getenv('CASO_PRUEBA', '450014145888-PRUEBA').strip("'\"")

# Override del numero de contrato para OnBase. Cuando esta definido, el test
# de documentos lo usa en lugar del numero derivado del nombre del proceso.
# Permite testear la descarga con un contrato real sin cambiar CASO_PRUEBA.
NUMERO_CONTRATO_ONBASE = os.getenv('NUMERO_CONTRATO_ONBASE', '').strip("'\"")

# HEADLESS_MODE: True → Chrome sin interfaz grafica (compatible desde que se elimino pyautogui).
HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'False').strip("'\"").lower() == 'true'

# PUBLICAR_SIN_DOCUMENTOS:
#   True  (default) → si OnBase no retorna documentos, publica el proceso igualmente
#                      y registra una advertencia en ExecutionContext.
#   False           → si OnBase no retorna documentos, lanza excepcion y NO publica.
#                     En el orquestador: el registro se marca como error en Google Sheets.
#                     En los tests: el test termina con error detallado.
PUBLICAR_SIN_DOCUMENTOS = os.getenv('PUBLICAR_SIN_DOCUMENTOS', 'True').strip("'\"").lower() == 'true'

# N_PASOS_TEST: numero de pasos del pipeline a ejecutar en test_orquestador.py (1-5).
#   1 = Solo Creacion del proceso
#   2 = Hasta Informacion general
#   3 = Hasta Configuracion del proceso
#   4 = Hasta Cuestionario
#   5 = Pipeline completo — Documentos y publicacion (default)
N_PASOS_TEST = int(os.getenv('N_PASOS_TEST', '5').strip("'\""))

# --- CHROME FLAGS Y BINARIO (Linux con snap requiere configuracion especial) ---
CHROME_ARGS = "--no-sandbox --disable-dev-shm-usage" if platform.system() == "Linux" else ""
_snap_chrome = "/snap/chromium/current/usr/lib/chromium-browser/chrome"
CHROME_BINARY = _snap_chrome if platform.system() == "Linux" and os.path.exists(_snap_chrome) else ""

# --- GOOGLE SHEETS SCOPES ---
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]
