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
load_dotenv(os.path.join(root_dir, 'env'))   # archivo se llama 'env', no '.env'

from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository
from utils.mappers import extraer_datos_fila
from pages.login_page import LoginPage
from pages.creacion_proceso_page import CreacionProcesoPage
from seleniumbase import Driver
from config.settings import CASO_PRUEBA


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
    driver = None
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
        print("\nIniciando Chrome...")
        driver = Driver(headless=False)
        print("Ejecutando login...")
        login_page = LoginPage(driver)
        login_page.iniciar_sesion()
        print(f"Login OK — URL: {driver.current_url}\n")

        # 3. Paso 1: creacion del proceso
        print(">> PASO 1: Creacion del proceso")
        print("   [1/5] Navegando a pagina de tipos de procesos...")
        print("   [2/5] Esperando boton Crear Contratacion (JS click)...")
        print("   [3/5] Cambiando al iframe del modal...")
        print("   [4/5] Llenando formulario y autocomplete de unidad...")
        print("   [5/5] Confirmando y esperando navegacion al proceso...")

        url_p1 = CreacionProcesoPage(driver).crear_proceso(
            datos['nombre_proceso'],
            datos['unidad_contratacion']
        )

        # 4. Persistir en Google Sheets
        print(f"\nActualizando 'Proceso 1' en fila {fila_excel}...")
        repo.actualizar_celda_por_nombre(fila_excel, 'Proceso 1', url_p1)
        print(f"Google Sheets actualizado.")
        print(f"URL guardada: {url_p1}")

    except Exception as e:
        import traceback
        print(f"\nERROR durante el test: {e}")
        traceback.print_exc()
    finally:
        if driver:
            input("\nPresiona ENTER para cerrar el navegador...")
            try:
                driver.quit()
            except Exception:
                pass

    print("\n=== FIN TEST CREACION PROCESO ===")


if __name__ == '__main__':
    test_creador_proceso()
