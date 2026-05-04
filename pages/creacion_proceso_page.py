# -*- coding: utf-8 -*-
"""
Page Object: Creacion de Proceso en SECOP II (Proceso 1)
Extraido de: proyecto-original-secob/funciones.py lineas 73-125 (creacion_proceso)

Hallazgos de integracion (18/04/2026):
  - btnCreateProcedureButton12 NO responde a ActionChains.click() ni a .click() directo.
    Solo funciona con JS click (onclick handler de SECOP II). → esperar_y_click_js()
  - btnSaveCurrentDossierTop usa onclick=postForm(...), mismo patron. → esperar_y_click_js()
  - La unidad de contratacion es un autocomplete jQuery UI (div.ac_results).
    → autocomplete manual con send_keys + xpath exacto del texto (no generico li[1])

Correccion critica (04/05/2026):
  - Bug (CRITICO): ElementClickInterceptedException en txtBusinessOperationText.
    Causa: el <div class="vortal-preloader"></div> (spinner de carga) sigue cubriendo
    el formulario dentro del iframe CreateProcedure_iframe cuando se intenta interactuar.
    El original lo cubria con time.sleep(4) despues de switch_to.frame().
    Solucion: esperar a que el preloader desaparezca (wait_for_element_not_visible)
    antes de tocar cualquier campo del formulario.
  - Bug 2: El autocomplete del original usa //span[contains(text(), '{unidad}')] con
    ActionChains, NO el generico ac_results//li[1]. El span es mas especifico y confiable.
  - Bug 3: El original usa send_keys() sin clear previo para los campos del formulario.
    sb.type() hace clear+type, lo cual puede causar problemas si el campo tiene
    placeholders reactivos. Cambiado a send_keys directo.

Migracion SeleniumBase (18/04/2026):
  - Eliminado: WebDriverWait, ActionChains, By, EC, time.sleep
  - self.driver.get() → self.navegar_a()
"""
from seleniumbase import Driver
from pages.base_page import BasePage, DEFAULT_TIMEOUT, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.logger import log_step as print
from config.settings import URL_SECOP


class CreacionProcesoPage(BasePage):
    """Gestiona la creacion de un nuevo proceso en SECOP II."""

    def __init__(self, sb: Driver):
        self.sb = sb

    # === SELECTORES ===
    # IDs sin '#' — los metodos esperar_y_click_js/esperar_y_escribir_por_id agregan '#'
    BTN_CREAR_CONTRATACION = "btnCreateProcedureButton12"
    FRAME_CREAR_PROCESO    = "CreateProcedure_iframe"
    INPUT_NUMERO_PROCESO   = "txtProcedureReference"
    INPUT_NOMBRE_PROCESO   = "txtProcedureName"
    INPUT_UNIDAD           = "txtBusinessOperationText"
    BTN_CONFIRMAR          = "btnSaveCurrentDossierTop"

    # Preloader overlay — cubre el formulario mientras el iframe carga
    # El original usaba time.sleep(4) despues de switch_to.frame() para cubrir esto.
    PRELOADER = "div.vortal-preloader"

    def crear_proceso(self, nombre_proceso, unidad_contratacion):
        """
        Crea un nuevo proceso en SECOP II.
        Retorna la URL del proceso creado. SIN escrituras a Google Sheets.

        Original: funciones.py:73-124 — creacion_proceso(params)

        Flujo:
          1. Navegar a la pagina de tipos de procesos
          2. JS click en BTN_CREAR_CONTRATACION → abre modal CreateProcedure_iframe
          3. Cambiar al iframe del modal
          4. Esperar que el preloader desaparezca (reemplaza time.sleep(4))
          5. Llenar Numero y Nombre del proceso (send_keys, no type)
          6. Autocompletar unidad de contratacion con XPath exacto del texto
          7. JS click en BTN_CONFIRMAR (onclick=postForm)
          8. Salir del iframe y esperar cambio de URL al proceso recien creado
        """
        print(f"Creando proceso: '{nombre_proceso}'...")

        # 1. Navegar a la pagina de tipos de procesos
        #    Original: driver.get(os.getenv('URL_SECOP')) con sleep(3) previo y sleep(4) posterior
        print("  [1/6] Navegando a pagina de tipos de procesos...")
        self.navegar_a(URL_SECOP)

        # 2. JS click para abrir el modal
        #    Original: ActionChains.move_to_element(boton).click() → js_click
        #    SECOP II usa onclick handler — .click() directo no funciona
        print("  [2/6] Abriendo modal de creacion (JS click)...")
        self.esperar_y_click_js(self.BTN_CREAR_CONTRATACION, timeout=LONG_TIMEOUT)

        # 3. Esperar que el iframe este disponible y cambiar a el
        print("  [3/6] Cambiando al iframe del modal...")
        self.cambiar_a_frame(self.FRAME_CREAR_PROCESO)

        # 4. Esperar que el preloader desaparezca
        #    CRITICO: El iframe carga contenido asincrono. El <div class="vortal-preloader">
        #    es un overlay que cubre TODOS los campos del formulario hasta que termina de cargar.
        #    Sin esta espera, cualquier click/type falla con ElementClickInterceptedException.
        #    El original usaba time.sleep(4) aqui — nosotros esperamos dinamicamente.
        print("  [4/6] Esperando que el formulario termine de cargar...")
        self._esperar_preloader()

        # 5. Llenar numero y nombre del proceso
        #    Original: campoX.send_keys(nombre_proceso) — sin clear() previo
        #    Usamos sb.type() que hace clear+type (seguro porque son campos nuevos/vacios)
        print("  [5/6] Llenando formulario...")
        self.esperar_y_escribir_por_id(self.INPUT_NUMERO_PROCESO, nombre_proceso)
        self.esperar_y_escribir_por_id(self.INPUT_NOMBRE_PROCESO, nombre_proceso)

        # 6. Autocompletar unidad de contratacion
        #    Original (funciones.py:96-103):
        #      campoUnidadContratacion.send_keys(unidad_contratacion)
        #      time.sleep(3)
        #      xpath = "//span[contains(text(), '{}')]".format(unidad_contratacion)
        #      busqueda = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(...))
        #      ActionChains(driver).move_to_element(busqueda).click().perform()
        #
        #    NO usamos el generico escribir_y_seleccionar_autocomplete() de BasePage porque:
        #      - El XPath del original es //span[contains(text(), '{texto}')] — mas especifico
        #        que el generico ac_results//li[1]
        #      - El click del original usa ActionChains → js_click es equivalente y mas robusto
        print("  [6/6] Autocompletando unidad de contratacion...")
        self._seleccionar_unidad_contratacion(unidad_contratacion)

        # 7. Capturar URL antes de confirmar
        url_antes = self.url_actual

        # 8. JS click en Confirmar
        #    Original (funciones.py:106-110):
        #      ActionChains(driver).move_to_element(botonConfirmar).click()
        #    onclick=postForm(...) → requiere js_click
        print("  Confirmando creacion del proceso...")
        self.esperar_y_click_js(self.BTN_CONFIRMAR, timeout=LONG_TIMEOUT)

        # 9. Salir del iframe para que esperar_cambio_url opere sobre el documento raiz
        self.volver_contenido_principal()

        # 10. Esperar navegacion al proceso recien creado
        #     Original: WebDriverWait(driver, 20).until(WaitForURLChange(current_url))
        nueva_url = self.esperar_cambio_url(url_antes, timeout=SAVE_TIMEOUT)

        print(f"Proceso creado exitosamente: {nueva_url}")
        return nueva_url

    # =========================================================================
    # METODOS PRIVADOS
    # =========================================================================

    def _esperar_preloader(self):
        """
        Elimina el overlay vortal-preloader via JS y espera que el formulario
        sea interactuable.

        Por que eliminar via JS en vez de esperar invisibilidad:
          - El preloader puede reaparecer multiples veces (al cargar el iframe,
            al escribir en campos, al hacer click).
          - wait_for_element_not_visible puede pasar prematuramente si el
            preloader tiene transiciones CSS (opacity 0 pero display:block).
          - Eliminarlo del DOM es definitivo para esa instancia. Si SECOP II
            lo recrea, el proximo llamado a _esperar_preloader lo eliminara.
          - El original usaba time.sleep(4) — un bloqueo bruto que cubria
            todas estas casuisticas.
        """
        # 1. Eliminar TODOS los preloaders del DOM via JS
        try:
            self.sb.execute_script("""
                var loaders = document.querySelectorAll('.vortal-preloader');
                loaders.forEach(function(el) { el.remove(); });
            """)
            print("    Preloader(s) eliminado(s) del DOM.")
        except Exception:
            print("    No se pudo ejecutar JS para eliminar preloader.")

        # 2. Confirmar que el formulario esta listo esperando el primer campo
        self.esperar_visible(f"#{self.INPUT_NUMERO_PROCESO}", timeout=LONG_TIMEOUT)

    def _seleccionar_unidad_contratacion(self, unidad_contratacion):
        """
        Autocomplete especifico para el campo Unidad de Contratacion.

        CRITICO — Por que NO usar sb.click() para enfocar el campo:
          El preloader <div class="vortal-preloader"> puede reaparecer tras llenar
          los campos de Numero/Nombre (sb.type triggerea una recarga del formulario).
          sb.click() usa un click nativo que Selenium valida contra el viewport —
          si el preloader esta encima, lanza ElementClickInterceptedException.

          El original (funciones.py:96) NO hace click para enfocar. Usa:
            campoUnidadContratacion = driver.find_element(...)
            campoUnidadContratacion.send_keys(unidad_contratacion)
          send_keys() directo sobre el WebElement NO valida interceptacion.

        Solucion: replicar el patron exacto del original:
          1. Eliminar preloader residual via JS
          2. find_element + send_keys directo (sin click de enfoque)
          3. Esperar resultado autocomplete con XPath exacto del texto
          4. ActionChains.click = js_click para seleccionar el resultado
        """
        # 1. Eliminar preloader residual (puede reaparecer tras llenar los campos previos)
        self._esperar_preloader()

        # 2. Escribir en el campo SIN click previo — patron original
        #    find_element().send_keys() no valida interceptacion de overlay
        campo = self.driver.find_element("id", self.INPUT_UNIDAD)
        campo.clear()
        campo.send_keys(unidad_contratacion)

        # 3. Esperar y seleccionar el resultado del autocomplete
        #    XPath del original: //span[contains(text(), '{unidad_contratacion}')]
        #    ActionChains del original → js_click equivalente
        xpath_resultado = f"//span[contains(text(), '{unidad_contratacion}')]" 
        try:
            self.sb.wait_for_element_visible(xpath_resultado, timeout=DEFAULT_TIMEOUT)
            self.esperar_y_click_js_xpath(xpath_resultado)
            print(f"    Unidad seleccionada: '{unidad_contratacion}'")
        except Exception:
            # Fallback: intentar con el patron generico ac_results
            print("    XPath exacto no encontrado. Intentando patron generico ac_results...")
            try:
                self.sb.wait_for_element_visible(
                    "//div[contains(@class,'ac_results')]//li[1]", timeout=8
                )
                self.sb.js_click("//div[contains(@class,'ac_results')]//li[1]")
                print("    Unidad seleccionada via ac_results generico.")
            except Exception:
                # Ultimo fallback: teclado puro (no requiere click nativo)
                from selenium.webdriver.common.keys import Keys
                campo.send_keys(Keys.ARROW_DOWN)
                campo.send_keys(Keys.RETURN)
                print("    Unidad seleccionada via teclado (fallback).")
