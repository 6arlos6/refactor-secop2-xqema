# -*- coding: utf-8 -*-
"""
Page Object: Creacion de Proceso en SECOP II (Proceso 1)
Extraido de: proyecto-original-secob/funciones.py lineas 73-125 (creacion_proceso)

Hallazgos de integracion (18/04/2026):
  - btnCreateProcedureButton12 NO responde a ActionChains.click() ni a .click() directo.
    Solo funciona con JS click (onclick handler de SECOP II). → esperar_y_click_js()
  - btnSaveCurrentDossierTop usa onclick=postForm(...), mismo patron. → esperar_y_click_js()
  - La unidad de contratacion es un autocomplete jQuery UI (div.ac_results).
    → escribir_y_seleccionar_autocomplete() de BasePage (sin time.sleep)
  - Los timeouts largos (>5s) dentro del iframe hacen que SECOP II detecte
    inactividad y mate la sesion. SeleniumBase usa polling activo (no idle).

Migracion SeleniumBase (18/04/2026):
  - Eliminado: WebDriverWait, ActionChains, By, EC, time.sleep
  - Eliminado: _seleccionar_unidad() (reemplazado por BasePage.escribir_y_seleccionar_autocomplete)
  - self.driver.get() → self.navegar_a()
"""
from seleniumbase import Driver
from pages.base_page import BasePage, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.logger import log_step as print
from config.settings import URL_SECOP


class CreacionProcesoPage(BasePage):
    """Gestiona la creacion de un nuevo proceso en SECOP II."""

    def __init__(self, sb: Driver):
        self.sb = sb

    # === SELECTORES ===
    # Nota: los ID se usan sin '#' en esperar_y_click_js (lo agrega internamente)
    BTN_CREAR_CONTRATACION_ID = "btnCreateProcedureButton12"
    FRAME_CREAR_PROCESO       = "CreateProcedure_iframe"
    INPUT_NUMERO_PROCESO      = "#txtProcedureReference"
    INPUT_NOMBRE_PROCESO      = "#txtProcedureName"
    INPUT_UNIDAD_ID           = "txtBusinessOperationText"
    BTN_CONFIRMAR_ID          = "btnSaveCurrentDossierTop"

    def crear_proceso(self, nombre_proceso, unidad_contratacion):
        """
        Crea un nuevo proceso en SECOP II.
        Retorna la URL del proceso creado. SIN escrituras a Google Sheets.

        Original: funciones.py:73-124 — creacion_proceso(params)

        Flujo:
          1. Navegar a la pagina de tipos de procesos
          2. JS click en BTN_CREAR_CONTRATACION_ID  → abre modal CreateProcedure_iframe
          3. Cambiar al iframe del modal
          4. Llenar Numero y Nombre del proceso
          5. Autocompletar unidad de contratacion (BasePage maneja ac_results sin sleep)
          6. JS click en BTN_CONFIRMAR_ID (onclick=postForm)
          7. Salir del iframe y esperar cambio de URL al proceso recien creado
        """
        print(f"Creando proceso: '{nombre_proceso}'...")

        # 1. Navegar a la pagina de tipos de procesos
        self.navegar_a(URL_SECOP)

        # 2. JS click para abrir el modal
        #    ActionChains no dispara el onclick de SECOP II — requiere JS click
        self.esperar_y_click_js(self.BTN_CREAR_CONTRATACION_ID, timeout=LONG_TIMEOUT)

        # 3. Esperar que el iframe este disponible y cambiar a el
        self.cambiar_a_frame(self.FRAME_CREAR_PROCESO)

        # 4. Llenar numero y nombre del proceso
        #    sb.type() incluye espera + clear + type en un solo paso
        self.esperar_y_escribir(self.INPUT_NUMERO_PROCESO, nombre_proceso)
        self.esperar_y_escribir(self.INPUT_NOMBRE_PROCESO, nombre_proceso)

        # 5. Autocompletar unidad de contratacion
        #    BasePage.escribir_y_seleccionar_autocomplete:
        #      - Patron A: espera div.ac_results con timeout=6s y hace click (sin sleep)
        #      - Patron B: ARROW_DOWN + RETURN como fallback de teclado
        self.escribir_y_seleccionar_autocomplete(
            self.INPUT_UNIDAD_ID, unidad_contratacion
        )

        # 6. Capturar URL antes de confirmar
        #    (driver.current_url dentro del iframe devuelve la URL del documento raiz)
        url_antes = self.url_actual

        # 7. JS click en Confirmar
        #    onclick=postForm(...) — mismo patron que BTN_CREAR_CONTRATACION_ID
        self.esperar_y_click_js(self.BTN_CONFIRMAR_ID, timeout=LONG_TIMEOUT)

        # 8. Salir del iframe para que esperar_cambio_url opere sobre el documento raiz
        self.volver_contenido_principal()

        # 9. Esperar navegacion al proceso recien creado
        nueva_url = self.esperar_cambio_url(url_antes, timeout=SAVE_TIMEOUT)

        print(f"Proceso creado exitosamente: {nueva_url}")
        return nueva_url
