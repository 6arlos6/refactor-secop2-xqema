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

# CASO_PRUEBA solo se usa en tests/ (no en produccion). Si no esta definido en .env,
# se usa un valor por defecto pero se avisa explicitamente para evitar que el
# ausente pase inadvertido durante la configuracion de un entorno de pruebas.
_caso_prueba_env = os.getenv('CASO_PRUEBA')
if _caso_prueba_env is None:
    print("ADVERTENCIA: CASO_PRUEBA no esta definido en .env. Usando valor por defecto '450014145888-PRUEBA'.")
CASO_PRUEBA = (_caso_prueba_env or '450014145888-PRUEBA').strip("'\"")

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
CHROME_ARGS = "--no-sandbox --disable-dev-shm-usage --disable-features=IsolateOrigins,site-per-process" if platform.system() == "Linux" else ""
_snap_chrome = "/snap/chromium/current/usr/lib/chromium-browser/chrome"
CHROME_BINARY = _snap_chrome if platform.system() == "Linux" and os.path.exists(_snap_chrome) else ""

# En Linux, "none" evita que Chrome congele el renderer esperando cargas lentas
# de community.secop.gov.co. Los waits de SeleniumBase por elemento siguen funcionando.
PAGE_LOAD_STRATEGY = "normal"  # mismo en Linux y Windows: las paginas SECOP necesitan JS completo

# --- GOOGLE SHEETS SCOPES ---
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

# --- REGLAS DE NEGOCIO DE DOMINIO (centralizadas desde utils/mappers.py) ---

# Tipologias y nombres de documento a excluir al filtrar la descarga de OnBase.
# Extraidas originalmente de globales.py.
TIPOLOGIAS_EXCLUIDAS = [
    'CERTIFICADO DE ANTECEDENTES',
    'DOCUMENTO DE IDENTIDAD',
    'CERTIFICACIÓN BANCARIA',
    'CERTIFICACION BANCARIA'
]

NOMBRES_EXCLUIDOS = [
    'DELITOSSEXUALES',
    'DELITOS_SEXUALES',
    'DELITOS-SEXUALES',
    'DELITOS SEXUALES',
    'REGISTRO-DEUDORES-MOROSOS-ALIMENTARIOS',
    'REGISTRO_DEUDORES_MOROSOS_ALIMENTARIOS',
    'REGISTRO-DEUDORES-MOROSOS-ALIMENTARIOS',
    'REGISTRODEUDORESMOROSOSALIMENTARIOS',
    'DEUDORES-MOROSOS',
    'DEUDORES_MOROSOS',
    'DEUDORES MOROSOS',
    'DEUDORESMOROSOS',
    'REDAM'
]

# Normalizacion de tipo de contrato al valor esperado por el select de SECOP II.
DICCIONARIO_NORMALIZACION_TIPOLOGIA = {
    "Arrendamiento De Inmuebles": "Arrendamiento de muebles",
    "Compraventa": "Compraventa",
    "Prestación De Servicios": "Prestación de servicios",
    "Obra": "Obra",
    "Contrato De Arrendamiento": "Arrendamiento de muebles",
    "Contrato De Compraventa": "Compraventa",
    "Contrato de Prestación de Servicios": "Prestación de servicios",
    "Contrato De Suministro": "Suministro",
    "Suministro": "Suministro"
}

# Caracteres no permitidos en la descripcion del objeto del contrato.
INVALID_CHARS = ['"', "'", "<", ">", "&", "%", "@", "$", "-", "#", "_", "–", "°", "º", "*", "±", "[", "]", "+", "•", "|", "–"]
