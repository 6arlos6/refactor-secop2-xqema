# -*- coding: utf-8 -*-
"""
Test de integracion: Carga de documentos y publicacion en SECOP II (Paso 5 del pipeline)
Cubre: LoginPage.iniciar_sesion() + DocumentosPage.adjuntar_y_publicar() + PublicacionPage.obtener_enlace()

Ejecucion:
    cd automatizacionsecop2-main
    venv\\Scripts\\python tests\\test_documentos.py

Prerequisito: el registro de CASO_PRUEBA debe existir en la hoja BASE_DATOS_BYS
con 'Proceso 4' completado (con URL) y 'Proceso 5' vacio (o se sobreescribira con la URL nueva).

NOTA: Este paso usa pyautogui para adjuntar archivos (ventana nativa de Windows).
Asegurese de NO mover el mouse ni cambiar de ventana mientras se ejecuta.
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
from pages.documentos_page import DocumentosPage
from pages.publicacion_page import PublicacionPage
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

def test_documentos():
    driver = None
    print("=== INICIANDO TEST DOCUMENTOS Y PUBLICACION (PASO 5) ===\n")
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

        # Sincronizar estado_proceso_4 (URL del paso anterior)
        datos['estado_proceso_4'] = datos['proceso_4']

        if not datos['estado_proceso_4']:
            print("ERROR: 'Proceso 4' esta vacio. No se puede navegar al proceso. Debe correr Paso 4 primero.")
            return

        # Extraer numero de contrato (nombre del proceso, sin sufijo de prueba)
        numero_contrato = datos['nombre_proceso']
        if "-" in numero_contrato:
            numero_contrato = numero_contrato.split("-")[0]

        print(f"Fila {fila_excel}")
        print(f"  Nombre  : '{datos['nombre_proceso']}'")
        print(f"  Numero contrato (OnBase): '{numero_contrato}'")
        print(f"  Proceso 4 (URL): '{datos['estado_proceso_4']}'")

        # 2. Navegador + login
        print("\nIniciando Chrome...")
        driver = Driver(headless=False)
        print("Ejecutando login...")
        login_page = LoginPage(driver)
        login_page.iniciar_sesion()
        print(f"Login OK — URL: {driver.current_url}\n")

        # 3. Paso 5: adjuntar documentos y publicar
        print(">> PASO 5: Adjuntar documentos (OnBase + pyautogui) y publicar")
        print("   ATENCION: No mueva el mouse ni cambie de ventana durante este paso.\n")

        url_publicada, fecha_publicacion = DocumentosPage(driver).adjuntar_y_publicar(
            url_proceso_4=datos['estado_proceso_4'],
            numero_contrato=numero_contrato
        )

        # 4. Obtener enlace publico del proceso
        print("\n>> Obteniendo enlace publico del proceso...")
        enlace_publico = PublicacionPage().obtener_enlace(url_publicada)

        if not enlace_publico:
            print("ADVERTENCIA: No se pudo obtener el enlace publico. Se guardara la URL interna.")
            enlace_publico = url_publicada

        # 5. Persistir en Google Sheets
        print(f"\nActualizando 'Proceso 5' en fila {fila_excel}...")
        repo.actualizar_celda_por_nombre(fila_excel, 'Proceso 5', enlace_publico)

        # Guardar fecha de publicacion
        fecha_str = fecha_publicacion.strftime("%#d/%m/%Y")
        print(f"Actualizando fecha de publicacion: {fecha_str}...")
        try:
            repo.actualizar_celda_por_nombre(fila_excel, 'Fecha publicación', fecha_str)
        except Exception:
            # Si la columna no existe, intentar con nombre alternativo
            try:
                repo.actualizar_celda_por_nombre(fila_excel, 'Fecha Publicacion', fecha_str)
            except Exception as e_fecha:
                print(f"Advertencia: No se pudo actualizar la fecha de publicacion: {e_fecha}")

        # Marcar como ejecutado
        try:
            repo.actualizar_celda_por_nombre(fila_excel, 'Ejecutado', 'SI')
        except Exception as e_ejec:
            print(f"Advertencia: No se pudo marcar como ejecutado: {e_ejec}")

        print(f"Google Sheets actualizado.")
        print(f"Enlace guardado: {enlace_publico}")

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

    print("\n=== FIN TEST DOCUMENTOS Y PUBLICACION ===")


if __name__ == '__main__':
    test_documentos()
