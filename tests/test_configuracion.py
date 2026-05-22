# -*- coding: utf-8 -*-
"""
Test de integracion: Configuracion del proceso en SECOP II (Paso 3 del pipeline)
Cubre: LoginPage.iniciar_sesion() + ConfiguracionPage.configurar_proceso()

Ejecucion:
    cd automatizacionsecop2-main
    venv\\Scripts\\python tests\\test_configuracion.py

Prerequisito: el registro de CASO_PRUEBA debe existir en la hoja BASE_DATOS_BYS
con 'Proceso 2' completado (con URL) y 'Proceso 3' vacio (o se sobreescribira con la URL nueva).
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
from pages.configuracion_page import ConfiguracionPage
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

def test_configuracion():
    print("=== INICIANDO TEST CONFIGURACION (PASO 3) ===\n")
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

        # Sincronizar estado_proceso_2
        datos['estado_proceso_2'] = datos['proceso_2']

        if not datos['estado_proceso_2']:
            print("ERROR: 'Proceso 2' esta vacio. No se puede navegar al proceso. Debe correr Paso 2 primero.")
            return

        print(f"Fila {fila_excel}")
        print(f"  Nombre  : '{datos['nombre_proceso']}'")
        print(f"  Proceso 2 (URL): '{datos['estado_proceso_2']}'")
        print(f"  --- DATOS DE CONFIGURACION EXTRAIDOS ---")
        print(f"  Fecha firma contrato: '{datos['fecha_firma_contrato']}'")
        print(f"  Fecha inicio: '{datos['fecha_inicio']}'")
        print(f"  Fecha fin: '{datos['fecha_fin']}'")
        print(f"  Valor estimado: '{datos['valor_estimado']}'")
        print(f"  Destinacion gasto: '{datos['destinacion_gasto']}'")
        print(f"  Tipo CDP: '{datos['tipo_cdp']}'")
        print(f"  Codigo(s) CDP: {datos['codigo_cdp']}")
        print(f"  Saldo(s) CDP: {datos['saldo_cdp']}")
        print(f"  -----------------------------------------")

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

            # 3. Paso 3: configuracion del proceso
            print(">> PASO 3: Configuracion del proceso (fechas, presupuesto, CDPs)")

            url_p3 = ConfiguracionPage(sb).configurar_proceso(datos)

            # 4. Persistir en Google Sheets
            print(f"\nActualizando 'Proceso 3' en fila {fila_excel}...")
            repo.actualizar_celda_por_nombre(fila_excel, 'Proceso 3', url_p3)
            print(f"Google Sheets actualizado.")
            print(f"URL guardada: {url_p3}")

            input("\nPresiona ENTER para cerrar el navegador...")

    except Exception as e:
        import traceback
        print(f"\nERROR durante el test: {e}")
        traceback.print_exc()

    print("\n=== FIN TEST CONFIGURACION ===")


if __name__ == '__main__':
    test_configuracion()
