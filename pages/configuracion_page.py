# -*- coding: utf-8 -*-
"""
Page Object: Configuracion del Proceso (Proceso 3)
Extraido de: proyecto-original-secob/funciones.py lineas 384-597 (configuracion_proceso)

Notas de robustez (basadas en ensayo y error del script original):
  - Todos los botones y radio buttons SECOP II usan ActionChains en el original
    porque tienen onclick handlers → equivalente a js_click en SeleniumBase.
  - El modal de acuerdo marco (ActiveFrameworkAgreementModal_iframe) requiere una
    espera larga tras cerrarse (~7s en el original) antes de interactuar con radios.
  - Los radio buttons regulatorios (Decreto 248, Sentencia T302, Acuerdos Paz)
    necesitan js_click porque están interceptados por la estructura del formulario.
  - El flujo de avance tiene 3 caminos posibles:
      A) btnApproveDossier → btnNoPAAPublishedCurrentYearConfirmDialogModal
      B) lnk_stpmStepManager3 (flecha continuar — proceso ya aprobado)
      C) Modal de acuerdo marco disponible (se cierra y continúa)
"""
from seleniumbase import Driver
from pages.base_page import BasePage, DEFAULT_TIMEOUT, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.logger import log_step as print


class ConfiguracionPage(BasePage):
    """Gestiona la configuracion del proceso en SECOP II (fechas, presupuesto, CDPs)."""

    def __init__(self, sb: Driver):
        self.sb = sb

    # === SELECTORES DE AVANCE (lineas 403-422) ===
    BTN_CONTINUAR             = "btnApproveDossier"
    BTN_ACEPTAR_CONTINUAR     = "btnNoPAAPublishedCurrentYearConfirmDialogModal"
    FLECHA_CONTINUAR          = "lnk_stpmStepManager3"
    FRAME_ACUERDO_MARCO       = "ActiveFrameworkAgreementModal_iframe"
    BTN_CERRAR_ACUERDO_MARCO  = "btnCloseAndContinue"

    # === SELECTORES OPCIONES REGULATORIAS (lineas 436-446) ===
    # Todos "NO" — el original usa ActionChains para los 3
    RADIO_DECRETO_248_NO      = "rdbgComplyWithMinimalPurchaseValue_1"
    RADIO_SENTENCIA_T302_NO   = "rdbgProcessAssociatedWithSentenceT302Value_1"
    RADIO_ACUERDOS_PAZ_NO     = "rdbgFrameworkAgreementValue_1"

    # === SELECTORES FECHAS Y VALOR (lineas 448-459) ===
    INPUT_FIRMA_CONTRATO  = "dtmbContractSignatureDate_txt"
    INPUT_FECHA_INICIO    = "dtmbStartDateExecutionOfContract_txt"
    INPUT_PLAZO_EJECUCION = "dtmbExecutionOfContractTerm_txt"
    INPUT_VALOR_ESTIMADO  = "cbxBasePrice"

    # === SELECTORES DESTINACION GASTO (lineas 461-527) ===
    SELECT_DEST_GASTO     = "selExpenseTypeSelect"
    RADIO_PNG_NO          = "rdbgBudgetOriginGNBCheckValueP2Gen_1"
    RADIO_SGP_NO          = "rdbgBudgetOriginGSPCheckValueP2Gen_1"
    RADIO_SGR_NO          = "rdbgBudgetOriginGRSCheckValueP2Gen_1"
    RADIO_SGR_SI          = "rdbgBudgetOriginGRSCheckValueP2Gen_0"
    RADIO_REC_PROPIOS_NO  = "rdbgBudgetOriginOwnResourcesAGRICheckValueP2Gen_1"
    RADIO_REC_CREDITO_NO  = "rdbgBudgetOriginCreditResourcesCheckValueP2Gen_1"
    RADIO_OTROS_REC_SI    = "rdbgBudgetOriginOwnResourcesCheckValueP2Gen_0"
    RADIO_OTROS_REC_NO    = "rdbgBudgetOriginOwnResourcesCheckValueP2Gen_1"
    INPUT_OTROS_RECURSOS  = "cbxBudgetOriginOwnResourcesValue"
    INPUT_SGR             = "cbxBudgetOriginGRSValue"

    # === SIIF (linea 529-531) ===
    # Original usa ActionChains → js_click
    RADIO_SIIF_NO = "rdbgCompanyRegisteredInSIIFValue_1"

    # === SELECTORES CDP (lineas 536-572) ===
    BTN_AGREGAR_CDP         = "btnAddCode"
    FRAME_CDP               = "SIIFModal_iframe"
    RADIO_CDP               = "rdbgOptionsToSelectRadioButton_0"
    RADIO_VIGENCIAS_FUTURAS = "rdbgOptionsToSelectRadioButton_1"
    INPUT_CODIGO_CDP        = "txtSIIFIntegrationItemTextbox"
    INPUT_SALDO_CDP         = "cbxSIIFIntegrationItemBalanceTextbox"
    INPUT_SALDO_COMPROMETER = "cbxSIIFIntegrationItemUsedValueTextbox"
    INPUT_SUBUNIDAD         = "txtSIIFIntegrationItemPCICodebox"
    BTN_CREAR_CDP           = "btnSIIFIntegrationItemButton"

    # === GUARDAR (lineas 577-584) ===
    # Original usa ActionChains + wait por "Proceso guardado con éxito"
    BTN_GUARDAR = "btnSaveProcedureTop"

    # =========================================================================
    # METODO PRINCIPAL
    # =========================================================================

    def configurar_proceso(self, datos):
        """
        Ejecuta la configuracion completa del proceso.
        Retorna la URL del proceso guardado. SIN escrituras a Google Sheets.

        Original: funciones.py:384-597 — configuracion_proceso(params)
        """
        url_proceso_2     = datos['estado_proceso_2']
        fecha_firma       = datos['fecha_firma_contrato']
        fecha_inicio      = datos['fecha_inicio']
        fecha_fin         = datos['fecha_fin']
        valor_estimado    = datos['valor_estimado']
        destinacion_gasto = datos['destinacion_gasto']
        tipo_cdp          = datos['tipo_cdp']
        codigo_cdp        = datos['codigo_cdp']
        saldo_cdp         = datos['saldo_cdp']

        print("Configurando proceso...")
        self.navegar_a(url_proceso_2)

        # 1. Avanzar a la seccion de configuracion (aprobacion / flecha / modal)
        self._avanzar_a_configuracion()

        # 2. Opciones regulatorias (Decreto 248, T302, Acuerdos Paz — NO)
        self._configurar_opciones_regulatorias()

        # 3. Fechas y valor estimado
        self._llenar_fechas_y_valor(fecha_firma, fecha_inicio, fecha_fin, valor_estimado)

        # 4. Destinacion del gasto (Funcionamiento/Inversion)
        self._configurar_destinacion_gasto(destinacion_gasto, valor_estimado)

        # 5. SIIF = NO (linea 529-531, original usa ActionChains)
        print("Seleccionando SIIF = No...")
        self.esperar_y_click_js(self.RADIO_SIIF_NO)

        # 6. Validar CDPs (lineas 532-534)
        if len(codigo_cdp) != len(saldo_cdp):
            raise Exception("Error de cdps: La cantidad de cdps no coinciden con la cantidad de saldos")

        # 7. Agregar CDPs
        self._agregar_cdps(codigo_cdp, saldo_cdp, tipo_cdp)

        # 8. Guardar
        return self._guardar_y_obtener_url()

    # =========================================================================
    # METODOS PRIVADOS
    # =========================================================================

    def _esperar_desbloqueo_ui(self):
        """
        Espera dinamicamente a que los overlays de carga de SECOP II desaparezcan.
        Reemplaza los time.sleep() estaticos asegurando que la UI este lista.
        """
        self.sb.sleep(0.5) # Pequeña pausa para permitir que el AJAX inicie y muestre el overlay
        try:
            self.sb.wait_for_element_not_visible(".blockUI", timeout=20)
            self.sb.wait_for_element_not_visible(".vortal-preloader", timeout=20)
        except Exception:
            pass

    def _disparar_eventos_input(self, element_id):
        """
        Dispara los eventos 'change' y 'blur' via JS para forzar 
        la actualizacion de totales en SECOP II.
        """
        script = f"""
        var el = document.getElementById('{element_id}');
        if(el) {{
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
        }}
        """
        self.sb.execute_script(script)

    def _escribir_nativo_con_blur(self, element_id, texto):
        """
        Escribe usando send_keys nativo y envia TAB para forzar 
        la actualizacion de totales (blur) en los scripts de SECOP II.
        Maneja dinamicamente StaleElementReferenceException.
        """
        self.esperar_visible(f"#{element_id}", timeout=LONG_TIMEOUT)
        
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.common.keys import Keys
        
        for attempt in range(5):
            try:
                el = self.driver.find_element("id", element_id)
                el.clear()
                self.sb.sleep(0.5)
                el = self.driver.find_element("id", element_id)
                el.send_keys(texto)
                self.sb.sleep(0.5)
                el = self.driver.find_element("id", element_id)
                el.send_keys(Keys.TAB)
                break
            except StaleElementReferenceException:
                self.sb.sleep(1)
        else:
            # Fallback en caso de fallar 5 veces
            self.limpiar_y_escribir_por_id(element_id, texto)
            self.sb.send_keys(f"#{element_id}", "\t")
            
        self.sb.sleep(1) # Pausa para que SECOP II calcule

    def _click_radio_dinamico(self, element_id):
        """
        Hace un click nativo con reintentos para manejar re-renderizados del DOM (StaleElementReference).
        Luego espera dinamicamente a que la UI de SECOP II se desbloquee.
        """
        selector = f"#{element_id}"
        from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
        
        for _ in range(5):
            try:
                self.esperar_visible(selector, timeout=5)
                self.eliminar_overlays()
                el = self.driver.find_element("css selector", selector)
                el.click()
                break # Click exitoso
            except (StaleElementReferenceException, ElementClickInterceptedException):
                self.sb.sleep(1)
        else:
            # Fallback a JS si el nativo falla constantemente
            self.sb.js_click(selector)
            
        self._esperar_desbloqueo_ui()

    def _avanzar_a_configuracion(self):
        """
        Lineas 401-434: Avanza a la seccion de configuracion.

        Flujo del original (ensayo y error):
          try:
            1. Click btnApproveDossier (ActionChains) → js_click
            2. Click btnNoPAAPublishedCurrentYearConfirmDialogModal (ActionChains) → js_click
          except:
            3. Click lnk_stpmStepManager3 (flecha continuar) (ActionChains) → js_click

          try:
            4. Cambiar al frame ActiveFrameworkAgreementModal_iframe
            5. Click btnCloseAndContinue para cerrar modal
          except:
            pass (el modal no siempre aparece)

          6. switch_to.default_content()
          7. Esperar (original: sleep(7) + sleep(1)) — el formulario carga lento

        Nota: El sleep(7) del original indica que SECOP II necesita tiempo para cargar
        el formulario de configuracion tras cerrar el modal. Reemplazado con espera
        dinamica al primer radio button (RADIO_DECRETO_248_NO).
        """
        print("Avanzando a la seccion de configuracion...")

        # Camino A: Aprobar proceso + confirmar PAA
        try:
            self.esperar_y_click_js(self.BTN_CONTINUAR, timeout=DEFAULT_TIMEOUT)
            self.esperar_y_click_js(self.BTN_ACEPTAR_CONTINUAR, timeout=DEFAULT_TIMEOUT)
            print("  Avance via aprobacion de proceso.")
        except Exception:
            # Camino B: Flecha continuar (proceso ya aprobado)
            try:
                self.esperar_y_click_js(self.FLECHA_CONTINUAR, timeout=DEFAULT_TIMEOUT)
                print("  Avance via flecha de continuacion.")
            except Exception:
                print("  [AVISO] No se encontro boton de avance — posiblemente ya estamos en configuracion.")

        # Modal de acuerdo marco (puede o no aparecer)
        try:
            self.cambiar_a_frame(self.FRAME_ACUERDO_MARCO, timeout=8)
            self.esperar_y_click_js(self.BTN_CERRAR_ACUERDO_MARCO, timeout=DEFAULT_TIMEOUT)
            print("  Modal de acuerdo marco cerrado.")
        except Exception:
            pass

        self.volver_contenido_principal()

        # Espera dinamica: el formulario de configuracion tarda en cargar tras el modal.
        # Original usa sleep(7)+sleep(1). Reemplazado con espera al primer radio visible.
        print("  Esperando carga del formulario de configuracion...")
        self.esperar_visible(
            f"#{self.RADIO_DECRETO_248_NO}", timeout=LONG_TIMEOUT
        )

    def _configurar_opciones_regulatorias(self):
        """
        Lineas 436-446: Decreto 248, Sentencia T302, Acuerdos de paz — todos NO.

        Original:
          - Decreto 248 y Sentencia T302: WebDriverWait + .click() directo
          - Acuerdos Paz: ActionChains.move_to_element().click() → js_click

        Por consistencia y robustez, usamos js_click para los tres.
        """
        print("Seleccionando opciones regulatorias (NO)...")
        self.esperar_y_click_js(self.RADIO_DECRETO_248_NO)
        self.esperar_y_click_js(self.RADIO_SENTENCIA_T302_NO)
        self.esperar_y_click_js(self.RADIO_ACUERDOS_PAZ_NO)

    def _llenar_fechas_y_valor(self, fecha_firma, fecha_inicio, fecha_fin, valor_estimado):
        """
        Lineas 448-459: Firma, inicio ejecucion, plazo, valor estimado.

        Original usa driver.find_element + .send_keys() directo (sin clear previo).
        sb.type() hace clear + type, lo cual es equivalente y mas robusto.
        """
        print("Llenando fechas y valor estimado...")
        self.esperar_y_escribir_por_id(self.INPUT_FIRMA_CONTRATO, fecha_firma)
        self.esperar_y_escribir_por_id(self.INPUT_FECHA_INICIO, fecha_inicio)
        self.esperar_y_escribir_por_id(self.INPUT_PLAZO_EJECUCION, fecha_fin)
        self.esperar_y_escribir_por_id(self.INPUT_VALOR_ESTIMADO, valor_estimado)

    def _configurar_destinacion_gasto(self, destinacion_gasto, valor_estimado):
        """
        Lineas 461-527: Configura la destinacion del gasto y origen presupuestal.

        Original tiene time.sleep(2-3) entre cada radio button. En SeleniumBase,
        sb.wait_for_element_visible() + js_click gestionan la espera dinamicamente.
        """
        if str(destinacion_gasto) == "1":
            self._configurar_funcionamiento(valor_estimado)
        elif str(destinacion_gasto) == "2":
            self._configurar_inversion(valor_estimado)
        else:
            print(f"  [AVISO] Destinacion de gasto '{destinacion_gasto}' no reconocida. Saltando.")

    def _configurar_funcionamiento(self, valor_estimado):
        """
        Lineas 461-494: Destinacion = Funcionamiento.

        Radios: PNG=NO, SGP=NO, SGR=NO, RecPropios=NO, RecCredito=NO, OtrosRec=SI
        Campo: cbxBudgetOriginOwnResourcesValue = valor_estimado
        """
        print("  Configurando destinacion: Funcionamiento...")
        self.seleccionar_dropdown(self.SELECT_DEST_GASTO, "Funcionamiento")
        self._esperar_desbloqueo_ui()
        self._click_radio_dinamico(self.RADIO_PNG_NO)
        self._click_radio_dinamico(self.RADIO_SGP_NO)
        self._click_radio_dinamico(self.RADIO_SGR_NO)
        self._click_radio_dinamico(self.RADIO_REC_PROPIOS_NO)
        self._click_radio_dinamico(self.RADIO_REC_CREDITO_NO)
        self._click_radio_dinamico(self.RADIO_OTROS_REC_SI)
        
        self._escribir_nativo_con_blur(self.INPUT_OTROS_RECURSOS, valor_estimado)
        self._disparar_eventos_input(self.INPUT_OTROS_RECURSOS)

    def _configurar_inversion(self, valor_estimado):
        """
        Lineas 495-527: Destinacion = Inversion.

        Radios: PNG=NO, SGP=NO, SGR=SI, RecPropios=NO, RecCredito=NO, OtrosRec=NO
        Campo: cbxBudgetOriginGRSValue = valor_estimado
        """
        print("  Configurando destinacion: Inversion...")
        self.seleccionar_dropdown(self.SELECT_DEST_GASTO, "Inversion")
        self._esperar_desbloqueo_ui()
        self._click_radio_dinamico(self.RADIO_PNG_NO)
        self._click_radio_dinamico(self.RADIO_SGP_NO)
        self._click_radio_dinamico(self.RADIO_SGR_SI)
        self._click_radio_dinamico(self.RADIO_REC_PROPIOS_NO)
        self._click_radio_dinamico(self.RADIO_REC_CREDITO_NO)
        self._click_radio_dinamico(self.RADIO_OTROS_REC_NO)
        
        self._escribir_nativo_con_blur(self.INPUT_SGR, valor_estimado)
        self._disparar_eventos_input(self.INPUT_SGR)

    def _agregar_cdps(self, codigos_cdp, saldos_cdp, tipo_cdp):
        """
        Lineas 536-575: Agrega los CDPs al proceso.

        Original envuelve el bucle completo en try/except y lanza
        "Error de cdps: No fue posible agregar CDP" si falla cualquier iteracion.
        """
        print(f"Agregando {len(codigos_cdp)} CDP(s)...")
        try:
            for i in range(len(codigos_cdp)):
                codigo = codigos_cdp[i].replace(" ", "")
                saldo = saldos_cdp[i]
                print(f"  CDP {i+1}/{len(codigos_cdp)}: codigo={codigo}, saldo={saldo}")
                self._agregar_un_cdp(codigo, saldo, tipo_cdp)
        except Exception as e:
            raise Exception(f"Error de cdps: No fue posible agregar CDP — {str(e)}")

    def _agregar_un_cdp(self, codigo, saldo, tipo_cdp):
        """
        Lineas 540-572: Agrega un CDP individual.

        Original:
          - BTN_AGREGAR_CDP: ActionChains → js_click
          - Radios (CDP/Vigencias): ActionChains → js_click
          - Campos: WebDriverWait + .send_keys() → sb.type()
          - BTN_CREAR_CDP: ActionChains → js_click
          - switch_to.default_content() al final de cada iteracion
        """
        # Abrir modal CDP (ActionChains en original → js_click)
        self.esperar_y_click_js(self.BTN_AGREGAR_CDP)
        self.cambiar_a_frame(self.FRAME_CDP)

        # Seleccionar tipo CDP (ActionChains en original → js_click)
        if str(tipo_cdp) == "1":
            self.esperar_y_click_js(self.RADIO_CDP)
        elif str(tipo_cdp) == "2":
            self.esperar_y_click_js(self.RADIO_VIGENCIAS_FUTURAS)
            
        self._esperar_desbloqueo_ui()

        # Llenar datos usando el metodo nativo con blur para simular al usuario
        self._escribir_nativo_con_blur(self.INPUT_CODIGO_CDP, codigo)
        self._escribir_nativo_con_blur(self.INPUT_SALDO_CDP, saldo)
        self._escribir_nativo_con_blur(self.INPUT_SALDO_COMPROMETER, saldo)
        self._escribir_nativo_con_blur(self.INPUT_SUBUNIDAD, "00-00-00")

        # Crear y volver al contenido principal (ActionChains en original → js_click)
        self.esperar_y_click_js(self.BTN_CREAR_CDP)
        self.volver_contenido_principal()

    def _guardar_y_obtener_url(self):
        """
        Lineas 577-584: Guarda la configuracion y retorna la URL.

        Original:
          1. ActionChains.move_to_element(btnSaveProcedureTop).click() → js_click
          2. WebDriverWait(40) por "Proceso guardado con éxito"
          3. driver.current_url

        Se usa js_click porque btnSaveProcedureTop tiene onclick=postForm()
        (mismo patrón que InformacionGeneralPage).
        """
        print("Guardando configuracion del proceso...")
        self.sb.sleep(3) # Pausa crucial para que termine de procesar los CDPs o animaciones
        
        self.esperar_visible(f"#{self.BTN_GUARDAR}")
        btn_guardar = self.driver.find_element("id", self.BTN_GUARDAR)
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).move_to_element(btn_guardar).click().perform()
        
        self.esperar_exito(timeout=SAVE_TIMEOUT)
        url = self.url_actual
        print(f"Configuracion guardada: {url}")
        return url
