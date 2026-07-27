"""
Test de integracion: Informacion general en SECOP II (Paso 2 del pipeline)
Cubre: LoginPage.iniciar_sesion() + InformacionGeneralPage.llenar_informacion_general()

Ejecucion:
    cd automatizacionsecop2-main
    venv\\Scripts\\python tests\\test_informacion_general.py

Prerequisito: el registro de CASO_PRUEBA debe existir en la hoja BASE_DATOS_BYS
con 'Proceso 1' completado (con URL) y 'Proceso 2' vacio (o se sobreescribira con la URL nueva).
"""
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, '.env'))

from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository, ConfigRepository
from utils.mappers import extraer_datos_fila
from seleniumbase import SB
from pages.login_page import LoginPage
from pages.informacion_general_page import InformacionGeneralPage
from config.settings import CASO_PRUEBA, HEADLESS_MODE, CHROME_ARGS, CHROME_BINARY, PAGE_LOAD_STRATEGY


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
    config_repo = ConfigRepository(conn.document)
    return repo, config_repo, ws_name


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

def test_informacion_general():
    print("=== INICIANDO TEST INFORMACION GENERAL (PASO 2) ===\n")
    repo = None
    fila_excel = 0
    try:
        # 1. Datos desde Google Sheets
        repo, config_repo, ws_name = init_repo()
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
        
        # Sincronizar estado_proceso_1
        datos['estado_proceso_1'] = datos['proceso_1']
        
        if not datos['estado_proceso_1']:
            print("ERROR: 'Proceso 1' esta vacio. No se puede navegar al proceso. Debe correr Paso 1 primero.")
            return

        print(f"Fila {fila_excel}")
        print(f"  Nombre  : '{datos['nombre_proceso']}'")
        print(f"  Proceso 1 (URL): '{datos['estado_proceso_1']}'")
        print(f"  --- DATOS DEL PROVEEDOR EXTRAIDOS ---")
        print(f"  Documento: '{datos['documento_proveedor']}'")
        print(f"  Nombre Prov: '{datos['nombre_proveedor']}'")
        print(f"  Email: '{datos['email']}'")
        print(f"  Tipo Prov: '{datos['tipo_proveedor']}'")
        print(f"  Tipo Identificador: '{datos['tipo_identificador']}'")
        print(f"  -------------------------------------")
        
        ciudades_codigos = config_repo.obtener_ciudades_codigos()

        # 2. Navegador + login
        headless_mode = HEADLESS_MODE
        print("\nIniciando Chrome...")
        if headless_mode:
            print("Ejecutando en modo sin ventana (Headless)")
        else:
            print("Ejecutando con interfaz grafica visible")

        with SB(headless=headless_mode, chromium_arg=CHROME_ARGS, binary_location=CHROME_BINARY or None, page_load_strategy=PAGE_LOAD_STRATEGY) as sb:
            sb.set_window_size(1920, 1080)
            login_page = LoginPage(sb)
            login_page.iniciar_sesion()
            print(f"Login OK — URL: {sb.get_current_url()}\n")

            # 3. Paso 2: informacion general
            print(">> PASO 2: Llenar informacion general del proceso")

            url_p2 = InformacionGeneralPage(sb).llenar_informacion_general(
                datos, ciudades_codigos
            )

            # 4. Persistir en Google Sheets
            print(f"\nActualizando 'Proceso 2' en fila {fila_excel}...")
            repo.actualizar_celda_por_nombre(fila_excel, 'Proceso 2', url_p2)
            print(f"Google Sheets actualizado.")
            print(f"URL guardada: {url_p2}")

            input("\nPresiona ENTER para cerrar el navegador...")

    except Exception as e:
        import traceback
        print(f"\nERROR durante el test: {e}")
        traceback.print_exc()
        if repo and fila_excel:
            repo.reportar_error(fila_excel, str(e), "Paso 2: Informacion general")

    print("\n=== FIN TEST INFORMACION GENERAL ===")


if __name__ == '__main__':
    test_informacion_general()
