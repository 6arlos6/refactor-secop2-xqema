# -*- coding: utf-8 -*-
"""
Test de integracion: Cuestionario del proceso en SECOP II (Paso 4 del pipeline)
Cubre: LoginPage.iniciar_sesion() + CuestionarioPage.completar()

Ejecucion:
    cd automatizacionsecop2-main
    venv\\Scripts\\python tests\\test_cuestionario.py

Prerequisito: el registro de CASO_PRUEBA debe existir en la hoja BASE_DATOS_BYS
con 'Proceso 3' completado (con URL) y 'Proceso 4' vacio (o se sobreescribira con la URL nueva).
"""
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, 'env'))

from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository
from utils.mappers import extraer_datos_fila
from pages.login_page import LoginPage
from pages.cuestionario_page import CuestionarioPage
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

def test_cuestionario():
    driver = None
    print("=== INICIANDO TEST CUESTIONARIO (PASO 4) ===\n")
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

        # Sincronizar estado_proceso_3 (URL del paso anterior)
        datos['estado_proceso_3'] = datos['proceso_3']

        if not datos['estado_proceso_3']:
            print("ERROR: 'Proceso 3' esta vacio. No se puede navegar al proceso. Debe correr Paso 3 primero.")
            return

        print(f"Fila {fila_excel}")
        print(f"  Nombre  : '{datos['nombre_proceso']}'")
        print(f"  Proceso 3 (URL): '{datos['estado_proceso_3']}'")
        print(f"  --- DATOS DEL CUESTIONARIO EXTRAIDOS ---")
        print(f"  Codigo UNSPSC: '{datos['codigo']}'")
        print(f"  Descripcion (Objeto): '{datos['objeto_descripcion'][:80]}...'")
        print(f"  Valor estimado: '{datos['valor_estimado']}'")
        print(f"  -------------------------------------------")

        # 2. Navegador + login
        print("\nIniciando Chrome...")
        driver = Driver(headless=False)
        print("Ejecutando login...")
        login_page = LoginPage(driver)
        login_page.iniciar_sesion()
        print(f"Login OK — URL: {driver.current_url}\n")

        # 3. Paso 4: completar cuestionario
        print(">> PASO 4: Completar cuestionario (UNSPSC, descripcion, precio, cantidad)")

        url_p4 = CuestionarioPage(driver).completar(
            url_proceso_3=datos['estado_proceso_3'],
            codigo=datos['codigo'],
            descripcion=datos['objeto_descripcion'],
            valor=datos['valor_estimado']
        )

        # 4. Persistir en Google Sheets
        print(f"\nActualizando 'Proceso 4' en fila {fila_excel}...")
        repo.actualizar_celda_por_nombre(fila_excel, 'Proceso 4', url_p4)
        print(f"Google Sheets actualizado.")
        print(f"URL guardada: {url_p4}")

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

    print("\n=== FIN TEST CUESTIONARIO ===")


if __name__ == '__main__':
    test_cuestionario()
