# -*- coding: utf-8 -*-
"""
Orquestador del Pipeline RPA - SECOP II
Reemplaza: automatizacion.py lineas 78-211 (ejecutar_procesos + loop principal)

Patron: State Valve — cada paso solo se ejecuta si su columna de proceso
esta vacia (no ejecutado) y no hay error previo en el registro.
"""
from seleniumbase import Driver

from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository, ConfigRepository
from utils.execution_context import ExecutionContext
from utils.mappers import extraer_datos_fila
from utils.logger import log_step as print
from config.settings import (
    BD_NAME, WORKSHEET_NAME, NOMBRE_ESTACION,
    CREDENCIALES_JSON, GOOGLE_SCOPES, HEADLESS_MODE
)

from pages.login_page import LoginPage
from pages.creacion_proceso_page import CreacionProcesoPage
from pages.informacion_general_page import InformacionGeneralPage
from pages.configuracion_page import ConfiguracionPage
from pages.cuestionario_page import CuestionarioPage
from pages.documentos_page import DocumentosPage
from pages.publicacion_page import PublicacionPage


class OrquestadorRPA:
    """
    Orquesta el pipeline completo de publicacion de contratos en SECOP II.

    Flujo de 5 pasos con reanudacion automatica:
      1. Creacion del proceso        → columna 'Proceso 1'
      2. Informacion general         → columna 'Proceso 2'
      3. Configuracion del proceso   → columna 'Proceso 3'
      4. Cuestionario                → columna 'Proceso 4'
      5. Documentos y publicacion    → columna 'Proceso 5' + 'Fecha Publicacion'
    """

    def __init__(self):
        print("Inicializando conexiones a Google Sheets...")
        conexion = GoogleSheetsConnection(CREDENCIALES_JSON, BD_NAME, GOOGLE_SCOPES)
        self.repo = ContratosRepository(conexion.document, WORKSHEET_NAME)
        self.config_repo = ConfigRepository(conexion.document)

    # =========================================================================
    # FLUJO MAESTRO
    # =========================================================================

    def ejecutar_flujo_maestro(self):
        """Procesa todos los registros pendientes de la estacion de trabajo."""

        registros = self.repo.obtener_registros_pendientes(NOMBRE_ESTACION)
        print(f"Iniciando lote: {len(registros)} registros pendientes para '{NOMBRE_ESTACION}'")

        if not registros:
            print("No hay tareas pendientes. Finalizando ejecucion.")
            return

        # Cargar ciudades/codigos en cache (se usa en InformacionGeneralPage)
        ciudades_codigos = self.config_repo.obtener_ciudades_codigos()

        # Levantar el navegador con SeleniumBase Driver
        # (expone sb.open, sb.click, sb.type, sb.js_click, etc. — requerido por BasePage)
        print("Levantando Chrome...")
        driver = Driver(headless=HEADLESS_MODE, incognito=True)
        if not HEADLESS_MODE:
            driver.maximize_window()

        # Instanciar page objects (inyeccion de dependencias via driver)
        login_page = LoginPage(driver)
        creacion_page = CreacionProcesoPage(driver)
        info_page = InformacionGeneralPage(driver)
        config_page = ConfiguracionPage(driver)
        cuestionario_page = CuestionarioPage(driver)
        documentos_page = DocumentosPage(driver)
        publicacion_page = PublicacionPage()  # Maneja su propio driver Chrome

        try:
            for registro in registros:
                self._procesar_registro(
                    registro, fila=registro['_fila_excel'],
                    ciudades_codigos=ciudades_codigos,
                    login_page=login_page,
                    creacion_page=creacion_page,
                    info_page=info_page,
                    config_page=config_page,
                    cuestionario_page=cuestionario_page,
                    documentos_page=documentos_page,
                    publicacion_page=publicacion_page,
                )
        finally:
            try:
                driver.quit()
            except Exception:
                pass

        print("\nLote completado.")

    # =========================================================================
    # PROCESAMIENTO DE UN REGISTRO
    # =========================================================================

    def _procesar_registro(
        self, registro, fila,
        ciudades_codigos,
        login_page, creacion_page, info_page,
        config_page, cuestionario_page, documentos_page, publicacion_page,
    ):
        """Ejecuta el pipeline completo para un registro con estado valve."""

        ExecutionContext.clear()
        datos = extraer_datos_fila(registro)

        # Sincronizar claves estado_proceso_x con proceso_x
        # (los page objects usan 'estado_proceso_X' para navegar a URLs ya guardadas)
        datos['estado_proceso_1'] = datos['proceso_1']
        datos['estado_proceso_2'] = datos['proceso_2']
        datos['estado_proceso_3'] = datos['proceso_3']
        datos['estado_proceso_4'] = datos['proceso_4']
        datos['estado_proceso_5'] = datos['proceso_5']

        nombre = datos['nombre_proceso']
        print(f"\n{'='*55}")
        print(f"PROCESANDO: {nombre}  (Fila: {fila})")
        print(f"{'='*55}")

        try:
            # Login (solo si no esta logueado en este ciclo)
            ExecutionContext.set_step("Login SECOP II")
            login_page.verificar_o_iniciar_sesion()

            # -----------------------------------------------------------
            # PASO 1: Creacion del proceso
            # Valve: ejecutar solo si Proceso 1 esta vacio
            # -----------------------------------------------------------
            if datos['proceso_1'] == "" and not ExecutionContext.has_error():
                ExecutionContext.set_step("Proceso 1: Creacion del proceso")
                print(">> PASO 1: Creacion del proceso")

                url_p1 = creacion_page.crear_proceso(
                    datos['nombre_proceso'],
                    datos['unidad_contratacion']
                )
                self.repo.actualizar_celda_por_nombre(fila, 'Proceso 1', url_p1)
                datos['proceso_1'] = url_p1
                datos['estado_proceso_1'] = url_p1

            # -----------------------------------------------------------
            # PASO 2: Informacion general
            # Valve: ejecutar solo si Proceso 2 esta vacio
            # -----------------------------------------------------------
            if datos['proceso_2'] == "" and not ExecutionContext.has_error():
                ExecutionContext.set_step("Proceso 2: Informacion general")
                print(">> PASO 2: Informacion general")

                url_p2 = info_page.llenar_informacion_general(datos, ciudades_codigos)
                self.repo.actualizar_celda_por_nombre(fila, 'Proceso 2', url_p2)
                datos['proceso_2'] = url_p2
                datos['estado_proceso_2'] = url_p2

            # -----------------------------------------------------------
            # PASO 3: Configuracion del proceso
            # Valve: ejecutar solo si Proceso 3 esta vacio
            # -----------------------------------------------------------
            if datos['proceso_3'] == "" and not ExecutionContext.has_error():
                ExecutionContext.set_step("Proceso 3: Configuracion del proceso")
                print(">> PASO 3: Configuracion del proceso")

                url_p3 = config_page.configurar_proceso(datos)
                self.repo.actualizar_celda_por_nombre(fila, 'Proceso 3', url_p3)
                datos['proceso_3'] = url_p3
                datos['estado_proceso_3'] = url_p3

            # -----------------------------------------------------------
            # PASO 4: Cuestionario
            # Valve: ejecutar solo si Proceso 4 esta vacio
            # -----------------------------------------------------------
            if datos['proceso_4'] == "" and not ExecutionContext.has_error():
                ExecutionContext.set_step("Proceso 4: Cuestionario UNSPSC")
                print(">> PASO 4: Cuestionario")

                url_p4 = cuestionario_page.completar(
                    datos['proceso_3'],
                    datos['codigo'],
                    datos['objeto_descripcion'],
                    datos['valor_estimado']
                )
                self.repo.actualizar_celda_por_nombre(fila, 'Proceso 4', url_p4)
                datos['proceso_4'] = url_p4
                datos['estado_proceso_4'] = url_p4

            # -----------------------------------------------------------
            # PASO 5: Adjuntar documentos y publicar
            # Valve: ejecutar solo si Proceso 5 esta vacio
            # -----------------------------------------------------------
            if datos['proceso_5'] == "" and not ExecutionContext.has_error():
                ExecutionContext.set_step("Proceso 5: Documentos y publicacion")
                print(">> PASO 5: Adjuntar documentos y publicar")

                url_publicada, fecha_publicacion = documentos_page.adjuntar_y_publicar(
                    datos['proceso_4'],
                    datos['nombre_proceso']
                )

                # Obtener enlace publico con driver independiente
                ExecutionContext.set_step("Proceso 5: Obteniendo enlace publico")
                enlace_publico = publicacion_page.obtener_enlace(url_publicada)

                self.repo.actualizar_celda_por_nombre(fila, 'Proceso 5', enlace_publico)
                fecha_str = fecha_publicacion.strftime("%d/%m/%Y")
                self.repo.actualizar_celda_por_nombre(fila, 'Fecha Publicacion', fecha_str)
                datos['proceso_5'] = enlace_publico

            # -----------------------------------------------------------
            # CHECKPOINT FINAL
            # -----------------------------------------------------------
            if not ExecutionContext.has_error() and datos['proceso_5'] != "":
                self.repo.actualizar_estado_ejecucion(fila)
                print(f"PROCESO '{nombre}' COMPLETADO EXITOSAMENTE.")

        except Exception as e:
            paso_actual = ExecutionContext.get_step()
            ExecutionContext.set_error(True)
            self.repo.reportar_error(fila, str(e), paso_actual)
            print(f"ERROR en '{nombre}' | Paso: '{paso_actual}' | {e}")
            print("Saltando al siguiente registro...")
