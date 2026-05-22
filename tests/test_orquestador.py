# -*- coding: utf-8 -*-
"""
Test del Orquestador — ejecuta los N primeros pasos del pipeline para CASO_PRUEBA.

Permite validar el pipeline completo o parcial de forma aislada, leyendo y
escribiendo en Google Sheets igual que el orquestador de produccion.

Configuracion via env:
  CASO_PRUEBA    → nombre/prefijo del proceso a procesar (definido en settings.py)
  N_PASOS_TEST   → numero de pasos a ejecutar:
                     1 = Solo Creacion del proceso
                     2 = Hasta Informacion general
                     3 = Hasta Configuracion del proceso
                     4 = Hasta Cuestionario
                     5 = Pipeline completo (default)
  HEADLESS_MODE  → True/False (definido en settings.py)

Ejecucion:
    cd automatizacionsecop2-main

    # Pipeline completo (5 pasos):
    venv\\Scripts\\python tests\\test_orquestador.py

    # Solo los primeros 2 pasos (editar env: N_PASOS_TEST=2):
    venv\\Scripts\\python tests\\test_orquestador.py

Prerequisito: el registro de CASO_PRUEBA debe existir en Google Sheets.
El test usa el State Valve del orquestador: solo ejecuta un paso si la columna
correspondiente esta vacia. Permite reanudar desde cualquier punto sin duplicar trabajo.
"""
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, 'env'))

from seleniumbase import SB
from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository, ConfigRepository
from utils.mappers import extraer_datos_fila
from utils.execution_context import ExecutionContext
from pages.login_page import LoginPage
from pages.creacion_proceso_page import CreacionProcesoPage
from pages.informacion_general_page import InformacionGeneralPage
from pages.configuracion_page import ConfiguracionPage
from pages.cuestionario_page import CuestionarioPage
from pages.documentos_page import DocumentosPage
from pages.publicacion_page import PublicacionPage
from config.settings import (
    CASO_PRUEBA, BD_NAME, WORKSHEET_NAME,
    CREDENCIALES_JSON, GOOGLE_SCOPES, HEADLESS_MODE
)

# Numero de pasos a ejecutar (1-5). Configurable via env: N_PASOS_TEST=3
N_PASOS_TEST = int(os.getenv('N_PASOS_TEST', '5'))


# ---------------------------------------------------------------------------
# HELPER: conexion Google Sheets
# ---------------------------------------------------------------------------

def init_repo():
    conn = GoogleSheetsConnection(CREDENCIALES_JSON, BD_NAME, GOOGLE_SCOPES)
    repo = ContratosRepository(conn.document, WORKSHEET_NAME)
    config_repo = ConfigRepository(conn.document)
    return repo, config_repo


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

def test_orquestador():
    print(f"=== TEST ORQUESTADOR — {N_PASOS_TEST} PASO(S) ===\n")
    print(f"Caso de prueba: '{CASO_PRUEBA}'")

    # 1. Datos desde Google Sheets
    repo, config_repo = init_repo()

    datos_crudos = repo.sheet.get_all_records()
    target, fila = None, 0
    for i, row in enumerate(datos_crudos, start=2):
        nombre = row.get("Nombre", "")
        if isinstance(nombre, str) and nombre.startswith(CASO_PRUEBA):
            target, fila = row, i
            break

    if not target:
        print(f"ERROR: No se encontro el registro '{CASO_PRUEBA}' en Google Sheets.")
        return

    datos = extraer_datos_fila(target)
    datos['estado_proceso_1'] = datos['proceso_1']
    datos['estado_proceso_2'] = datos['proceso_2']
    datos['estado_proceso_3'] = datos['proceso_3']
    datos['estado_proceso_4'] = datos['proceso_4']
    datos['estado_proceso_5'] = datos['proceso_5']

    ciudades_codigos = config_repo.obtener_ciudades_codigos()

    print(f"Fila: {fila} | Nombre: '{datos['nombre_proceso']}'")
    print(f"Estado actual: "
          f"P1={'OK' if datos['proceso_1'] else 'pendiente'} | "
          f"P2={'OK' if datos['proceso_2'] else 'pendiente'} | "
          f"P3={'OK' if datos['proceso_3'] else 'pendiente'} | "
          f"P4={'OK' if datos['proceso_4'] else 'pendiente'} | "
          f"P5={'OK' if datos['proceso_5'] else 'pendiente'}")

    # 2. Navegador
    headless_mode = HEADLESS_MODE
    print("\nLevantando motor de automatizacion web...")
    if headless_mode:
        print("Ejecutando en modo sin ventana (Headless)")
    else:
        print("Ejecutando con interfaz grafica visible")

    try:
        with SB(headless=headless_mode) as sb:
            sb.set_window_size(1920, 1080)

            # Inicializar Page Objects inyectando el contexto de SeleniumBase (sb)
            login_page        = LoginPage(sb)
            creacion_page     = CreacionProcesoPage(sb)
            info_page         = InformacionGeneralPage(sb)
            config_page       = ConfiguracionPage(sb)
            cuestionario_page = CuestionarioPage(sb)
            documentos_page   = DocumentosPage(sb)
            publicacion_page  = PublicacionPage()  # driver propio (incognito independiente)

            ExecutionContext.clear()
            login_page.iniciar_sesion()

            # ------------------------------------------------------------------
            # PASO 1: Creacion del proceso
            # ------------------------------------------------------------------
            if N_PASOS_TEST >= 1 and datos['proceso_1'] == "" and not ExecutionContext.has_error():
                print("\n>> PASO 1: Creacion del proceso")
                url = creacion_page.crear_proceso(
                    datos['nombre_proceso'], datos['unidad_contratacion']
                )
                repo.actualizar_celda_por_nombre(fila, 'Proceso 1', url)
                datos['proceso_1'] = datos['estado_proceso_1'] = url
                print(f"  Guardado: {url}")

            # ------------------------------------------------------------------
            # PASO 2: Informacion general
            # ------------------------------------------------------------------
            if N_PASOS_TEST >= 2 and datos['proceso_2'] == "" and not ExecutionContext.has_error():
                print("\n>> PASO 2: Informacion general")
                url = info_page.llenar_informacion_general(datos, ciudades_codigos)
                repo.actualizar_celda_por_nombre(fila, 'Proceso 2', url)
                datos['proceso_2'] = datos['estado_proceso_2'] = url
                print(f"  Guardado: {url}")

            # ------------------------------------------------------------------
            # PASO 3: Configuracion del proceso
            # ------------------------------------------------------------------
            if N_PASOS_TEST >= 3 and datos['proceso_3'] == "" and not ExecutionContext.has_error():
                print("\n>> PASO 3: Configuracion del proceso")
                url = config_page.configurar_proceso(datos)
                repo.actualizar_celda_por_nombre(fila, 'Proceso 3', url)
                datos['proceso_3'] = datos['estado_proceso_3'] = url
                print(f"  Guardado: {url}")

            # ------------------------------------------------------------------
            # PASO 4: Cuestionario
            # ------------------------------------------------------------------
            if N_PASOS_TEST >= 4 and datos['proceso_4'] == "" and not ExecutionContext.has_error():
                print("\n>> PASO 4: Cuestionario")
                url = cuestionario_page.completar(
                    url_proceso_3=datos['estado_proceso_3'],
                    codigo=datos['codigo'],
                    descripcion=datos['objeto_descripcion'],
                    valor=datos['valor_estimado']
                )
                repo.actualizar_celda_por_nombre(fila, 'Proceso 4', url)
                datos['proceso_4'] = datos['estado_proceso_4'] = url
                print(f"  Guardado: {url}")

            # ------------------------------------------------------------------
            # PASO 5: Adjuntar documentos y publicar
            # ------------------------------------------------------------------
            if N_PASOS_TEST >= 5 and datos['proceso_5'] == "" and not ExecutionContext.has_error():
                print("\n>> PASO 5: Documentos y publicacion")
                url_pub, fecha_pub = documentos_page.adjuntar_y_publicar(
                    url_proceso_4=datos['estado_proceso_4'],
                    numero_contrato=datos['nombre_proceso']
                )
                enlace = publicacion_page.obtener_enlace(url_pub) or url_pub
                repo.actualizar_celda_por_nombre(fila, 'Proceso 5', enlace)
                repo.actualizar_celda_por_nombre(fila, 'Fecha Publicacion',
                                                 fecha_pub.strftime("%d/%m/%Y"))
                datos['proceso_5'] = enlace
                print(f"  Guardado: {enlace}")

            # ------------------------------------------------------------------
            # RESULTADO
            # ------------------------------------------------------------------
            alertas = ExecutionContext.get_warnings()
            if ExecutionContext.has_error():
                print(f"\nPIPELINE FINALIZADO CON ERROR en paso: {ExecutionContext.get_step()}")
            elif alertas:
                print(f"\nPIPELINE COMPLETADO CON ADVERTENCIAS: {' | '.join(alertas)}")
            else:
                print(f"\nPIPELINE COMPLETADO EXITOSAMENTE (pasos 1-{N_PASOS_TEST})")

            input("\nPresiona ENTER para cerrar el navegador...")
            # SB cierra el browser automaticamente al salir del with

    except Exception as e:
        import traceback
        print(f"\nERROR durante el test: {e}")
        traceback.print_exc()

    print("\n=== FIN TEST ORQUESTADOR ===")


if __name__ == '__main__':
    test_orquestador()
