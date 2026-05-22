"""
Test de integracion: Creacion de proceso en SECOP II (Paso 1 del pipeline)
Cubre: LoginPage.iniciar_sesion() + CreacionProcesoPage.crear_proceso()

Ejecucion:
    cd automatizacionsecop2-main
    venv\\Scripts\\python tests\\test_creacion_proceso.py

Prerequisito: el registro de CASO_PRUEBA debe existir en la hoja BASE_DATOS_BYS
con 'Proceso 1' vacio (o se sobreescribira con la URL nueva).
"""
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, '.env'))

from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository
from utils.mappers import extraer_datos_fila
from seleniumbase import SB
from pages.login_page import LoginPage
from pages.creacion_proceso_page import CreacionProcesoPage
from config.settings import CASO_PRUEBA, HEADLESS_MODE


# ---------------------------------------------------------------------------
# HELPER: conexion Google Sheets
# ---------------------------------------------------------------------------

def init_repo():
    db_name = os.getenv("HOJA_DATOS", "DATOS_SECOP_II").strip("'")
    ws_name  = os.getenv("WORKSHEET",  "BASE_DATOS_BYS").strip("'")
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    conn = GoogleSheetsConnection("client_sheet.json", db_name, scopes)
    repo = ContratosRepository(conn.document, ws_name)
    return repo, ws_name


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

def test_creador_proceso():
    print("=== INICIANDO TEST CREACION PROCESO (PASO 1) ===\n")
    try:
        # 1. Datos desde Google Sheets
        repo, ws_name = init_repo()
        print(f"Buscando '{CASO_PRUEBA}' en '{ws_name}'...")

        datos_crudos = repo.sheet.get_all_records()
        target = None
        fila_excel = 0

        for i, row in enumerate(datos_crudos, start=2):
            nombre = row.get("Nombre", "")
            if isinstance(nombre, str) and nombre.startswith(CASO_PRUEBA):
                target = row
                fila_excel = i
                break

        if not target:
            print(f"ERROR: No se encontro el registro '{CASO_PRUEBA}'.")
            return

        datos = extraer_datos_fila(target)
        print(f"Fila {fila_excel}")
        print(f"  Nombre  : '{datos['nombre_proceso']}'")
        print(f"  Unidad  : '{datos['unidad_contratacion']}'")

        # 2. Navegador + login
        headless_mode = HEADLESS_MODE
        print("\nIniciando Chrome...")
        if headless_mode:
            print("Ejecutando en modo sin ventana (Headless)")
        else:
            print("Ejecutando con interfaz grafica visible")

        with SB(headless=headless_mode) as sb:
            sb.set_window_size(1920, 1080)
            login_page = LoginPage(sb)
            login_page.iniciar_sesion()
            print(f"Login OK — URL: {sb.get_current_url()}\n")

            # 3. Paso 1: creacion del proceso
            print(">> PASO 1: Creacion del proceso")

            url_p1 = CreacionProcesoPage(sb).crear_proceso(
                datos['nombre_proceso'],
                datos['unidad_contratacion']
            )

            # 4. Persistir en Google Sheets
            print(f"\nActualizando 'Proceso 1' en fila {fila_excel}...")
            repo.actualizar_celda_por_nombre(fila_excel, 'Proceso 1', url_p1)
            print(f"Google Sheets actualizado.")
            print(f"URL guardada: {url_p1}")

            input("\nPresiona ENTER para cerrar el navegador...")

    except Exception as e:
        import traceback
        print(f"\nERROR durante el test: {e}")
        traceback.print_exc()

    print("\n=== FIN TEST CREACION PROCESO ===")


if __name__ == '__main__':
    test_creador_proceso()
