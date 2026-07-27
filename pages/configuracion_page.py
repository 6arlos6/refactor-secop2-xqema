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

    # === BPIN (destinacion_gasto == "2" = Inversion con Regalias) ===
    # Extraido de proyecto-original-secob-garantias/funciones.py:541-661
    CHK_BPIN_EXISTENTE          = "chkBPINCheckbox_0"
    BTN_ELIMINAR_BPIN           = "btnDeleteBPINButton"
    BTN_AGREGAR_BPIN            = "btnAddBPINButton"
    INPUT_CODIGO_BPIN           = "txtBPINCodeValueTextBox_0"
    SELECT_ANIO_BPIN            = "selBPINYearCombo_0"
    BTN_CONSULTAR_BPIN          = "btnBPINConsultButton_0"
    BTN_ACEPTAR_VALIDACION_BPIN = "btnBPINValidationOkButtonGen"
    LABEL_ESTADO_BPIN           = "lblBPINStateValidLabel_0"

    # === CDP de Regalias / SPGR (destinacion_gasto == "2") ===
    # Extraido de proyecto-original-secob-garantias/funciones.py:663-757
    CHK_INTEGRACION_SPGR = "chkSPGRIntegrationCheckbox_0"  # mismo checkbox: existencia previa e integracion
    BTN_ELIMINAR_CDP_SPGR = "btnSPGRRemoveCDPButton"
    BTN_AGREGAR_CDP_SPGR  = "btnSPGRAddCDPButton"
    FRAME_CDP_SPGR        = "SPGRModal_iframe"
    INPUT_CODIGO_CDP_SPGR = "txtCDPCodeTextbox"
    SELECT_BPIN_EN_CDP    = "selBPINCodeSelect"
    INPUT_VALOR_A_USAR    = "cbxValueToUseTextbox"
    BTN_CREAR_CDP_SPGR    = "btnCreateButton"
    BTN_CONSULTAR_SPGR    = "btnSPGRIntegrationButton"
    BTN_VALIDAR_SPGR      = "btnValidateSPGRIntegrationButton"
    XPATH_SPGR_CONSULTA_EXITOSA = (
        "//table[@id='msgMessagesPanel']//td[@class='Message' and contains(text(), 'Consulta Exitosa')]"
    )
    XPATH_SPGR_VALIDACION_EXITOSA = (
        "//table[@id='msgMessagesPanel']//td[@class='Message' and "
        "contains(text(), 'Información SGR validada con éxito')]"
    )

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

        # Guardar datos en la instancia para que el retry de _guardar_y_obtener_url
        # pueda re-ingresar la fecha si el VortalDatePicker la rechaza.
        self._datos_configuracion = datos

        print("Configurando proceso...")
        self.navegar_a(url_proceso_2)
        # Esperar a que SECOP II inicialice la pagina antes de buscar botones de navegacion.
        # El original tenia time.sleep(4) aqui. En headless la carga puede ser mas lenta:
        # _esperar_desbloqueo_ui() espera a que desaparezcan los overlays blockUI/vortal-preloader.
        self._esperar_desbloqueo_ui()

        # 1. Avanzar a la seccion de configuracion (aprobacion / flecha / modal)
        self._avanzar_a_configuracion()

        # 2. Opciones regulatorias (Decreto 248, T302, Acuerdos Paz — NO)
        self._configurar_opciones_regulatorias()

        # 3. Fechas y valor estimado
        self._llenar_fechas_y_valor(fecha_firma, fecha_inicio, fecha_fin, valor_estimado)

        # 4. Destinacion del gasto (Funcionamiento/Inversion/Regalias)
        self._configurar_destinacion_gasto(destinacion_gasto, valor_estimado, datos)

        # 5. SIIF = NO (linea 529-531, original usa ActionChains)
        print("Seleccionando SIIF = No...")
        self._click_disparando_blur(self.RADIO_SIIF_NO)

        # 6. Validar CDPs (lineas 532-534)
        if len(codigo_cdp) != len(saldo_cdp):
            raise Exception("Error de cdps: La cantidad de cdps no coinciden con la cantidad de saldos")

        # 7. Agregar CDPs
        self._agregar_cdps(codigo_cdp, saldo_cdp, tipo_cdp, valor_estimado)

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

    def _click_disparando_blur(self, element_id):
        """
        Clic en elemento que requiere disparar blur en inputs previamente enfocados.

        Estrategia headless-compatible:
          1. scrollIntoView — mueve el foco del navegador al elemento, disparando
             el evento 'blur' de cualquier input que estuviera activo (mismo efecto
             que move_to_element de ActionChains, pero sin cursor fisico).
          2. JS click — mas confiable que ActionChains en modo headless porque no
             depende de coordenadas del cursor ni del viewport fisico.

        En modo visible funciona exactamente igual que en headless.
        """
        self.esperar_visible(f"#{element_id}", timeout=LONG_TIMEOUT)
        self.sb.sleep(1)
        el = self.driver.find_element("id", element_id)
        # Scroll al elemento para disparar blur en inputs previos
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", el
        )
        self.sb.sleep(0.3)
        self.sb.js_click(f"#{element_id}")
        self._esperar_desbloqueo_ui()

    def _escribir_fecha(self, element_id, texto):
        """
        Escribe una fecha en un campo VortalDatePicker disparando eventos reales.
        El picker solo registra la fecha si recibe blur tras la escritura;
        sin Tab al final, SECOP II rechaza el campo como vacio al guardar.
        """
        from selenium.webdriver.common.keys import Keys
        from selenium.common.exceptions import StaleElementReferenceException

        self.esperar_visible(f"#{element_id}", timeout=LONG_TIMEOUT)
        self.sb.sleep(0.5)

        for attempt in range(5):
            try:
                el = self.driver.find_element("id", element_id)
                el.send_keys(Keys.CONTROL + "a")
                el.send_keys(Keys.DELETE)
                self.sb.sleep(0.3)
                el = self.driver.find_element("id", element_id)
                el.send_keys(texto)
                el.send_keys(Keys.TAB)  # dispara blur → VortalDatePicker registra la fecha
                self.sb.sleep(0.5)
                break
            except StaleElementReferenceException:
                self.sb.sleep(1)

    def _escribir_como_humano(self, element_id, texto):
        """
        Simula la escritura humana limpiando cuidadosamente con Ctrl+A + Delete
        y luego usando send_keys. Previene bugs del framework Vortal.
        """
        self.esperar_visible(f"#{element_id}", timeout=LONG_TIMEOUT)
        self.sb.sleep(1) # Espera a que el DOM asiente el elemento
        
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.common.keys import Keys
        
        for attempt in range(5):
            try:
                el = self.driver.find_element("id", element_id)
                # Seleccionar todo y borrar es mas seguro que .clear() en SECOP
                el.send_keys(Keys.CONTROL + "a")
                el.send_keys(Keys.DELETE)
                self.sb.sleep(0.5)
                
                el = self.driver.find_element("id", element_id)
                el.send_keys(texto)
                self.sb.sleep(1)
                break
            except StaleElementReferenceException:
                self.sb.sleep(1)
        else:
            self.sb.type(f"#{element_id}", texto)
            
        self.sb.sleep(1)

    def _click_radio_dinamico(self, element_id):
        """
        Click con reintentos para manejar re-renderizados del DOM (StaleElementReference).
        Luego espera dinamicamente a que la UI de SECOP II se desbloquee.

        Estrategia:
          - Usa JS click como metodo principal: es confiable tanto en modo visible
            como en headless (ActionChains falla silenciosamente en headless porque
            no tiene cursor fisico, sin lanzar ninguna excepcion).
          - Si js_click falla (StaleElement/ClickIntercepted), reintenta hasta 5 veces.
          - scrollIntoView garantiza que el elemento sea visible antes del click.
        """
        selector = f"#{element_id}"
        from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException

        for _ in range(5):
            try:
                self.esperar_visible(selector, timeout=5)
                self.eliminar_overlays()
                el = self.driver.find_element("css selector", selector)

                # Desplazar al centro para evitar que cabeceras o footers tapen el click
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                self.sb.sleep(0.5)

                # JS click: headless-compatible, no depende del cursor fisico
                self.sb.js_click(selector)
                break  # Click exitoso
            except (StaleElementReferenceException, ElementClickInterceptedException):
                self.sb.sleep(1)

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

        # Camino A: Aprobar proceso + confirmar PAA.
        # LONG_TIMEOUT (20 s) en lugar de DEFAULT_TIMEOUT (10 s): primer elemento tras
        # navegacion necesita mas tiempo en headless para que el JS de SECOP II inicialice.
        try:
            self.esperar_y_click_js(self.BTN_CONTINUAR, timeout=LONG_TIMEOUT)
            self.esperar_y_click_js(self.BTN_ACEPTAR_CONTINUAR, timeout=LONG_TIMEOUT)
            print("  Avance via aprobacion de proceso.")
        except Exception:
            # Camino B: Flecha continuar (proceso ya aprobado).
            # wait_for_element_present en lugar de wait_for_element_visible:
            # el flecha lnk_stpmStepManager3 puede existir en el DOM antes de ser
            # estrictamente "visible" para SeleniumBase (SECOP II lo renderiza con
            # animaciones CSS). JS click funciona con presencia, sin requerir visibilidad.
            try:
                self.sb.wait_for_element_present(f"#{self.FLECHA_CONTINUAR}", timeout=LONG_TIMEOUT)
                self.sb.js_click(f"#{self.FLECHA_CONTINUAR}")
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
        # SAVE_TIMEOUT (40s) en lugar de LONG_TIMEOUT (20s): en headless con servidor lento
        # el formulario puede tardar mas de 20s en renderizarse tras la navegacion.
        print("  Esperando carga del formulario de configuracion...")
        self.esperar_visible(
            f"#{self.RADIO_DECRETO_248_NO}", timeout=SAVE_TIMEOUT
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

        Original usa driver.find_element + .send_keys() directo.
        sb.type() falla para campos VortalDatePicker porque establece el valor
        via JavaScript (element.value=...) sin disparar los eventos blur/change
        que el picker necesita para registrar la fecha. Se usa _escribir_fecha()
        que simula escritura real + Tab para forzar el evento blur del picker.
        """
        print("Llenando fechas y valor estimado...")
        self._escribir_fecha(self.INPUT_FIRMA_CONTRATO, fecha_firma)
        self._escribir_fecha(self.INPUT_FECHA_INICIO, fecha_inicio)
        self._escribir_fecha(self.INPUT_PLAZO_EJECUCION, fecha_fin)
        self._escribir_como_humano(self.INPUT_VALOR_ESTIMADO, valor_estimado)

    def _configurar_destinacion_gasto(self, destinacion_gasto, valor_estimado, datos):
        """
        Lineas 461-527: Configura la destinacion del gasto y origen presupuestal.

        Original tiene time.sleep(2-3) entre cada radio button. En SeleniumBase,
        sb.wait_for_element_visible() + js_click gestionan la espera dinamicamente.

        destinacion_gasto == "2" significa "Inversion financiada con Regalias (SGR)":
        exige BPIN y ejecuta el flujo completo de BPIN + CDP de regalias via SPGR
        (proyecto-original-secob-garantias/funciones.py:541-758) ademas de los
        radios base de Inversion.
        """
        if str(destinacion_gasto) == "1":
            self._configurar_funcionamiento(valor_estimado)
        elif str(destinacion_gasto) == "2":
            self._configurar_regalias(valor_estimado, datos)
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
        self.sb.sleep(2) # Pausa crucial para asentar re-render tras el select
        self._esperar_desbloqueo_ui()
        self._click_radio_dinamico(self.RADIO_PNG_NO)
        self._click_radio_dinamico(self.RADIO_SGP_NO)
        self._click_radio_dinamico(self.RADIO_SGR_NO)
        self._click_radio_dinamico(self.RADIO_REC_PROPIOS_NO)
        self._click_radio_dinamico(self.RADIO_REC_CREDITO_NO)
        self._click_radio_dinamico(self.RADIO_OTROS_REC_SI)
        
        self._escribir_como_humano(self.INPUT_OTROS_RECURSOS, valor_estimado)

    def _configurar_inversion(self, valor_estimado):
        """
        Lineas 495-527: Destinacion = Inversion.

        Radios: PNG=NO, SGP=NO, SGR=SI, RecPropios=NO, RecCredito=NO, OtrosRec=NO
        Campo: cbxBudgetOriginGRSValue = valor_estimado
        """
        print("  Configurando destinacion: Inversion...")
        self.seleccionar_dropdown(self.SELECT_DEST_GASTO, "Inversion")
        self.sb.sleep(2) # Pausa crucial para asentar re-render tras el select
        self._esperar_desbloqueo_ui()
        self._click_radio_dinamico(self.RADIO_PNG_NO)
        self._click_radio_dinamico(self.RADIO_SGP_NO)
        self._click_radio_dinamico(self.RADIO_SGR_SI)
        self._click_radio_dinamico(self.RADIO_REC_PROPIOS_NO)
        self._click_radio_dinamico(self.RADIO_REC_CREDITO_NO)
        self._click_radio_dinamico(self.RADIO_OTROS_REC_NO)
        
        self._escribir_como_humano(self.INPUT_SGR, valor_estimado)

    def _configurar_regalias(self, valor_estimado, datos):
        """
        Destinacion = Inversion financiada con Regalias (SGR).

        Original: proyecto-original-secob-garantias/funciones.py:541-758 — bloque
        "AQUI INICIA LA LOGICA PARA DESTINACION DE GASTO 2 (REGALIAS)".
        Requiere BPIN obligatoriamente (si no viene en la fila, se corta el
        proceso con un error claro en vez de intentar continuar sin el).

        Los radios base (PNG/SGP/SGR/RecPropios/RecCredito/OtrosRec) y el valor
        SGR son identicos a _configurar_inversion() — se reutiliza en vez de
        duplicar esa logica.
        """
        bpin = str(datos.get('bpin', '') or '').strip()
        cdp_regalias = str(datos.get('cdp_regalias', '') or '').strip()
        anio_bpin = str(datos.get('anio_bpin', '') or '').strip()
        saldo_cdp = datos.get('saldo_cdp') or []

        if not bpin:
            raise Exception("No se cuenta con BPIN para rendir (destinacion de gasto = 2 requiere BPIN)")

        print("  Configurando destinacion: Inversion con Regalias (BPIN/SPGR)...")
        self._configurar_inversion(valor_estimado)

        # Disparar change/blur en el campo SGR para que SECOP II habilite el
        # formulario de BPIN (no se dispara solo con send_keys, se necesita Tab).
        from selenium.webdriver.common.keys import Keys
        campo_sgr = self.driver.find_element("id", self.INPUT_SGR)
        campo_sgr.send_keys(Keys.TAB)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));",
            campo_sgr
        )
        self._esperar_desbloqueo_ui()

        self._configurar_bpin(bpin, anio_bpin)
        self._configurar_cdp_regalias(bpin, cdp_regalias, saldo_cdp)

    def _configurar_bpin(self, bpin, anio_bpin):
        """
        Elimina un BPIN previo si existe, agrega uno nuevo, escribe el codigo,
        selecciona la vigencia (año actual si no viene en la hoja) y consulta/
        valida que quede en estado "Validado".

        Todo ocurre en la pagina principal (fuera de iframes) — se reutilizan
        los helpers sb.*-based ya existentes (_click_radio_dinamico, esperar_*).
        """
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import Select
        from datetime import datetime
        import unicodedata

        # Si ya existe un BPIN agregado, seleccionarlo y eliminarlo antes del nuevo.
        try:
            chk = self.driver.find_element("id", self.CHK_BPIN_EXISTENTE)
            if not chk.is_selected():
                chk.click()
                self.sb.sleep(2)  # espera re-render del DOM por el checkbox
            self._click_radio_dinamico(self.BTN_ELIMINAR_BPIN)
        except Exception:
            pass  # no habia BPIN previo

        self._click_radio_dinamico(self.BTN_AGREGAR_BPIN)

        self.esperar_visible(f"#{self.INPUT_CODIGO_BPIN}", timeout=DEFAULT_TIMEOUT)
        campo_bpin = self.driver.find_element("id", self.INPUT_CODIGO_BPIN)
        campo_bpin.send_keys(bpin)
        campo_bpin.send_keys(Keys.TAB)  # dispara change/blur para habilitar el combo de año
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('blur', {bubbles: true}));",
            campo_bpin
        )
        self._esperar_desbloqueo_ui()

        anio = anio_bpin if anio_bpin and anio_bpin != 'None' else str(datetime.now().year)
        self.esperar_presente(f"#{self.SELECT_ANIO_BPIN}", timeout=DEFAULT_TIMEOUT)
        elemento_combo = self.driver.find_element("id", self.SELECT_ANIO_BPIN)
        combo_anio = Select(elemento_combo)
        opciones_anio = [o.get_attribute("value") for o in combo_anio.options]
        if anio not in opciones_anio:
            raise Exception(
                f"La vigencia del BPIN '{anio}' no esta disponible en el combo. Opciones: {opciones_anio}"
            )
        combo_anio.select_by_value(anio)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", elemento_combo
        )

        self._click_radio_dinamico(self.BTN_CONSULTAR_BPIN)
        try:
            self._click_radio_dinamico(self.BTN_ACEPTAR_VALIDACION_BPIN)
            self.esperar_presente(f"#{self.LABEL_ESTADO_BPIN}", timeout=DEFAULT_TIMEOUT)
            label = self.driver.find_element("id", self.LABEL_ESTADO_BPIN)
            texto_estado = (label.get_attribute("value") or label.text or "").strip()
        except Exception:
            raise Exception("No se ha podido validar el BPIN especificado. Favor verificar")

        # Normaliza acentos sin agregar dependencia nueva (unicodedata es stdlib)
        texto_normalizado = ''.join(
            c for c in unicodedata.normalize('NFD', texto_estado) if unicodedata.category(c) != 'Mn'
        )
        if "validado" not in texto_normalizado.lower():
            raise Exception("El BPIN no pudo pasar a 'Validado'. Favor revisar que sea un valor valido")

    def _configurar_cdp_regalias(self, bpin, cdp_regalias, saldo_cdp):
        """
        Elimina un CDP de regalias previo si existe, abre el modal SPGR, lo
        diligencia y luego consulta/valida la integracion.

        El modal (SPGRModal_iframe) usa Selenium raw en vez de sb.* — mismo
        motivo documentado en _agregar_un_cdp(): self.sb.* reinicia el
        contexto de frame y rompe las esperas dentro del iframe.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC

        # Si ya existe un CDP de regalias agregado, seleccionarlo y eliminarlo.
        try:
            chk = self.driver.find_element("id", self.CHK_INTEGRACION_SPGR)
            if not chk.is_selected():
                chk.click()
                self.sb.sleep(2)
            self._click_radio_dinamico(self.BTN_ELIMINAR_CDP_SPGR)
        except Exception:
            pass  # no habia CDP de regalias previo

        self._click_radio_dinamico(self.BTN_AGREGAR_CDP_SPGR)

        # --- Dentro del iframe SPGRModal_iframe: Selenium raw ---
        WebDriverWait(self.driver, LONG_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, self.FRAME_CDP_SPGR))
        )
        wait = WebDriverWait(self.driver, 20)

        campo_codigo = wait.until(EC.element_to_be_clickable((By.ID, self.INPUT_CODIGO_CDP_SPGR)))
        campo_codigo.send_keys(cdp_regalias)

        combo_bpin = Select(wait.until(EC.presence_of_element_located((By.ID, self.SELECT_BPIN_EN_CDP))))
        combo_bpin.select_by_value(str(bpin))

        valor_a_usar = saldo_cdp[0] if saldo_cdp else ""
        campo_valor = wait.until(EC.element_to_be_clickable((By.ID, self.INPUT_VALOR_A_USAR)))
        campo_valor.send_keys(str(valor_a_usar))

        btn_crear = wait.until(EC.element_to_be_clickable((By.ID, self.BTN_CREAR_CDP_SPGR)))
        btn_crear.click()

        self.driver.switch_to.default_content()
        self.sb.sleep(2)
        # --- Fin del bloque dentro del iframe ---

        self._consultar_y_validar_spgr()

    def _consultar_y_validar_spgr(self):
        """
        Marca el checkbox de integracion SPGR, consulta y valida contra el
        sistema de regalias.

        Fix de robustez (solicitado explicitamente): en el original, el click
        de "Validar integracion SPGR" (y su precursor "Consultar SPGR") NO
        estaban envueltos en try/except — solo los mensajes posteriores lo
        estaban. Si alguno de esos dos botones no llegaba a generarse a tiempo
        en el DOM, se propagaba una excepcion cruda de Selenium en vez de un
        mensaje claro. Aqui ambos clicks quedan protegidos.
        """
        try:
            chk = self.driver.find_element("id", self.CHK_INTEGRACION_SPGR)
            if not chk.is_selected():
                chk.click()
            self.sb.sleep(1)
        except Exception as e:
            raise Exception(f"No se pudo marcar el checkbox de integracion SPGR (puede no haberse generado): {e}")

        try:
            self._click_radio_dinamico(self.BTN_CONSULTAR_SPGR)
        except Exception as e:
            raise Exception(f"No se pudo hacer click en 'Consultar SPGR' (el boton puede no haberse generado a tiempo): {e}")

        try:
            self.sb.wait_for_element_present(self.XPATH_SPGR_CONSULTA_EXITOSA, timeout=15)
        except Exception:
            raise Exception("No se valido el CDP: no aparecio el mensaje 'Consulta Exitosa' al consultar SPGR.")

        try:
            self._click_radio_dinamico(self.BTN_VALIDAR_SPGR)
        except Exception as e:
            raise Exception(f"No se pudo hacer click en 'Validar integracion SPGR' (el boton puede no haberse generado a tiempo): {e}")

        try:
            self.sb.wait_for_element_present(self.XPATH_SPGR_VALIDACION_EXITOSA, timeout=15)
        except Exception:
            raise Exception("No se valido la informacion SGR: no aparecio el mensaje 'Informacion SGR validada con exito'.")

    def _agregar_cdps(self, codigos_cdp, saldos_cdp, tipo_cdp, valor_estimado):
        """
        Lineas 536-575: Agrega los CDPs al proceso.

        Original envuelve el bucle completo en try/except y lanza
        "Error de cdps: No fue posible agregar CDP" si falla cualquier iteracion.

        Calculo de saldo_comprometer:
          SECOP II requiere que la suma de todos los "Saldo a comprometer" sea igual
          al valor_estimado del proceso (campo "Valor total de Fuente de los recursos").
          - Para 1 CDP:   saldo_comprometer = valor_estimado (completo).
          - Para N CDPs:  distribucion proporcional al saldo disponible de cada CDP.
                          El ultimo CDP absorbe el residuo del redondeo.
          El campo "Saldo CDP" (INPUT_SALDO_CDP) sigue usando el saldo disponible del
          certificado CDP tal como lo proporciona la hoja de Google Sheets.
        """
        print(f"Agregando {len(codigos_cdp)} CDP(s)...")

        # Calcular saldo a comprometer por CDP (suma debe = valor_estimado)
        valor_total = float(str(valor_estimado).replace(",", "").replace(".", "").strip() or 0)
        total_saldo = sum(
            float(str(s).replace(",", "").replace(".", "").strip() or 0)
            for s in saldos_cdp
        )

        saldos_comprometer = []
        acumulado = 0
        for i, s in enumerate(saldos_cdp):
            if i == len(saldos_cdp) - 1:
                # Ultimo CDP absorbe el residuo del redondeo
                comprometer = round(valor_total - acumulado)
            else:
                saldo_f = float(str(s).replace(",", "").replace(".", "").strip() or 0)
                proporcion = saldo_f / total_saldo if total_saldo else (1 / len(saldos_cdp))
                comprometer = round(valor_total * proporcion)
                acumulado += comprometer
            saldos_comprometer.append(str(int(comprometer)))

        try:
            for i in range(len(codigos_cdp)):
                codigo = codigos_cdp[i].replace(" ", "")
                saldo = saldos_cdp[i]
                comprometer = saldos_comprometer[i]
                print(f"  CDP {i+1}/{len(codigos_cdp)}: codigo={codigo}, saldo={saldo}, comprometer={comprometer}")
                self._agregar_un_cdp(codigo, saldo, comprometer, tipo_cdp)
        except Exception as e:
            raise Exception(f"Error de cdps: No fue posible agregar CDP — {str(e)}")

    def _agregar_un_cdp(self, codigo, saldo, saldo_comprometer, tipo_cdp):
        """
        Lineas 540-572: Agrega un CDP individual.

        IMPORTANTE — por que raw Selenium dentro del iframe:
          Los metodos self.sb.* (SeleniumBase) restablecen internamente el contexto
          de frame cuando se usan tras un driver.switch_to.frame() raw.
          El resultado es que wait_for_element_visible() busca el elemento en el
          contenido principal en lugar del iframe, fallando siempre.
          Solucion: usar solo WebDriverWait/ActionChains raw dentro del iframe,
          exactamente como hacia el original con funciones.py.

        Parametros:
          codigo           — codigo del CDP (ej: "1001408511")
          saldo            — saldo disponible del certificado CDP
          saldo_comprometer — monto a comprometer (calculado en _agregar_cdps)
          tipo_cdp         — "1"=CDP, "2"=Vigencias Futuras
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys

        # 1. Abrir modal CDP (fuera del iframe — sb.* permitido aqui)
        self.esperar_y_click_js(self.BTN_AGREGAR_CDP)
        self.sb.sleep(1)

        # 2. Entrar al iframe usando raw Selenium con espera de disponibilidad
        # frame_to_be_available_and_switch_to_it garantiza que el iframe exista
        # y hace el switch en un solo paso, sin usar sb.* que resetean el contexto.
        WebDriverWait(self.driver, LONG_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, self.FRAME_CDP))
        )
        self.sb.sleep(3)  # El original usa sleep(3) aqui — el iframe carga lento

        # 3. Seleccionar tipo CDP (ActionChains como en el original)
        radio_id = self.RADIO_CDP if str(tipo_cdp) == "1" else self.RADIO_VIGENCIAS_FUTURAS
        radio = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, radio_id))
        )
        ActionChains(self.driver).move_to_element(radio).click().perform()
        self.sb.sleep(1)

        # 4. Llenar campos con raw WebDriverWait (sin sb.* para preservar frame context)
        wait = WebDriverWait(self.driver, 20)

        def _rellenar(field_id, valor):
            el = wait.until(EC.element_to_be_clickable((By.ID, field_id)))
            el.click()
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.DELETE)
            el.send_keys(str(valor))

        _rellenar(self.INPUT_CODIGO_CDP, codigo)
        _rellenar(self.INPUT_SALDO_CDP, saldo)
        _rellenar(self.INPUT_SALDO_COMPROMETER, saldo_comprometer)
        _rellenar(self.INPUT_SUBUNIDAD, "00-00-00")

        # 5. Confirmar CDP y salir del iframe
        btn = wait.until(EC.element_to_be_clickable((By.ID, self.BTN_CREAR_CDP)))
        ActionChains(self.driver).move_to_element(btn).click().perform()

        self.driver.switch_to.default_content()
        self.sb.sleep(1)  # Pausa equivalente al sleep(1) del original entre iteraciones

    def _verificar_errores_validacion(self):
        """
        Lee div#validationSummary y retorna la lista de mensajes de error.
        Retorna lista vacia si no hay errores o el div no existe.
        """
        try:
            from selenium.webdriver.common.by import By
            el = self.driver.find_element(By.ID, "validationSummary")
            texto = el.text.strip()
            if not texto:
                return []
            return [linea.strip() for linea in texto.splitlines() if linea.strip()]
        except Exception:
            return []

    def _click_guardar(self):
        """
        Click en el boton guardar.

        Usa JS click (sb.js_click) en lugar de ActionChains porque:
        - ActionChains requiere mover el cursor fisico, lo que falla silenciosamente
          en modo headless (el elemento existe pero el click nunca se registra).
        - esperar_y_click_js llama a sb.js_click que dispara el handler onclick/postForm
          directamente via JavaScript — compatible con headless y modo visible.
        """
        self.esperar_y_click_js(self.BTN_GUARDAR, timeout=LONG_TIMEOUT)

    def _guardar_y_obtener_url(self):
        """
        Lineas 577-584: Guarda la configuracion y retorna la URL.

        Flujo:
          1. ActionChains click en btnSaveProcedureTop (onclick=postForm())
          2. Esperar "Proceso guardado con exito" o div#validationSummary
          3. Si aparece error de fecha: re-ingresar fechas con Tab y reintentar (1 vez)
          4. Si aparece otro error de validacion: lanzar excepcion con el texto

        El error "Fecha de Firma del Contrato es obligatorio" ocurre cuando
        sb.type() (JS) se uso en lugar de send_keys reales — el VortalDatePicker
        necesita el evento blur para registrar la fecha. Con _escribir_fecha()
        esto no deberia ocurrir, pero el retry sirve como red de seguridad.
        """
        print("Guardando configuracion del proceso...")
        self.sb.sleep(3)

        self._click_guardar()

        # Esperar hasta que aparezca exito O validationSummary (lo que ocurra primero)
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        SELECTOR_EXITO = "//td[contains(text(), 'Proceso guardado con')]"
        SELECTOR_VALIDACION = "//*[@id='validationSummary']"

        def exito_o_error(driver):
            try:
                driver.find_element(By.XPATH, SELECTOR_EXITO)
                return "exito"
            except Exception:
                pass
            try:
                el = driver.find_element(By.ID, "validationSummary")
                if el.text.strip():
                    return "error"
            except Exception:
                pass
            return None

        resultado = self._wait(SAVE_TIMEOUT).until(exito_o_error)

        if resultado == "error":
            errores = self._verificar_errores_validacion()
            print(f"  [VALIDACION] Errores detectados: {errores}")

            errores_fecha = [e for e in errores if "Fecha de Firma" in e or "Firma del Contrato" in e]

            if errores_fecha:
                # El VortalDatePicker no recibio el blur — re-ingresar la fecha con Tab explícito
                print("  [RETRY] Re-ingresando campo de fecha de firma y guardando de nuevo...")
                datos = getattr(self, '_datos_configuracion', None)
                if datos:
                    self._escribir_fecha(self.INPUT_FIRMA_CONTRATO, datos['fecha_firma_contrato'])
                    self.sb.sleep(2)
                else:
                    # Fallback: enfocar el campo y sacarle el foco para disparar blur
                    from selenium.webdriver.common.keys import Keys
                    el = self.driver.find_element("id", self.INPUT_FIRMA_CONTRATO)
                    el.send_keys(Keys.TAB)
                    self.sb.sleep(2)

                self._click_guardar()
                resultado2 = self._wait(SAVE_TIMEOUT).until(exito_o_error)
                if resultado2 == "error":
                    errores2 = self._verificar_errores_validacion()
                    raise Exception(f"Validacion fallida tras retry: {errores2}")
            else:
                raise Exception(f"Error de validacion al guardar: {errores}")

        url = self.url_actual
        print(f"Configuracion guardada: {url}")
        return url
