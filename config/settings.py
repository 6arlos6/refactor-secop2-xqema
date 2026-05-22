# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv

# El archivo de entorno se llama 'env' (sin punto), no '.env'.
# Buscamos primero relativo a este archivo (config/../env), luego en CWD como fallback.
_env_path = os.path.join(os.path.dirname(__file__), '..', 'env')
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

# --- GOOGLE SHEETS SCOPES ---
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]
