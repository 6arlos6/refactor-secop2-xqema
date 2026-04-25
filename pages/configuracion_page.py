# -*- coding: utf-8 -*-
"""
Page Object: Configuracion del Proceso (Proceso 3)
Extraido de: proyecto-original-secob/funciones.py lineas 384-597 (configuracion_proceso)
"""
from pages.base_page import BasePage, DEFAULT_TIMEOUT, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.logger import log_step as print


class ConfiguracionPage(BasePage):
    """Gestiona la configuracion del proceso en SECOP II (fechas, presupuesto, CDPs)."""

    # === SELECTORES DE AVANCE (lineas 403-422) ===
    BTN_CONTINUAR = "//input[@id = 'btnApproveDossier']"
    BTN_ACEPTAR_CONTINUAR = "//input[@id = 'btnNoPAAPublishedCurrentYearConfirmDialogModal']"
    FLECHA_CONTINUAR = "//span[@id = 'lnk_stpmStepManager3']"
    FRAME_ACUERDO_MARCO = "ActiveFrameworkAgreementModal_iframe"
    BTN_CERRAR_ACUERDO_MARCO = "//input[@id ='btnCloseAndContinue']"

    # === SELECTORES OPCIONES REGULATORIAS (lineas 436-446) ===
    RADIO_DECRETO_248_NO = "//input[@id = 'rdbgComplyWithMinimalPurchaseValue_1']"
    RADIO_SENTENCIA_T302_NO = "//input[@id = 'rdbgProcessAssociatedWithSentenceT302Value_1']"
    RADIO_ACUERDOS_PAZ_NO = "//input[@id = 'rdbgFrameworkAgreementValue_1']"

    # === SELECTORES FECHAS Y VALOR (lineas 448-459) ===
    INPUT_FIRMA_CONTRATO = "//input[@id = 'dtmbContractSignatureDate_txt']"
    INPUT_FECHA_INICIO = "//input[@id = 'dtmbStartDateExecutionOfContract_txt']"
    INPUT_PLAZO_EJECUCION = "//input[@id = 'dtmbExecutionOfContractTerm_txt']"
    INPUT_VALOR_ESTIMADO = "//input[@id = 'cbxBasePrice']"

    # === SELECTORES DESTINACION GASTO (lineas 461-527) ===
    SELECT_DEST_GASTO = "selExpenseTypeSelect"
    RADIO_PNG_NO = "//input[@id = 'rdbgBudgetOriginGNBCheckValueP2Gen_1']"
    RADIO_SGP_NO = "//input[@id = 'rdbgBudgetOriginGSPCheckValueP2Gen_1']"
    RADIO_SGR_NO = "//input[@id = 'rdbgBudgetOriginGRSCheckValueP2Gen_1']"
    RADIO_SGR_SI = "//input[@id = 'rdbgBudgetOriginGRSCheckValueP2Gen_0']"
    RADIO_REC_PROPIOS_NO = "//input[@id = 'rdbgBudgetOriginOwnResourcesAGRICheckValueP2Gen_1']"
    RADIO_REC_CREDITO_NO = "//input[@id = 'rdbgBudgetOriginCreditResourcesCheckValueP2Gen_1']"
    RADIO_OTROS_REC_SI = "//input[@id = 'rdbgBudgetOriginOwnResourcesCheckValueP2Gen_0']"
    RADIO_OTROS_REC_NO = "//input[@id = 'rdbgBudgetOriginOwnResourcesCheckValueP2Gen_1']"
    INPUT_OTROS_RECURSOS = "cbxBudgetOriginOwnResourcesValue"
    INPUT_SGR = "cbxBudgetOriginGRSValue"

    # === SIIF (linea 529-531) ===
    RADIO_SIIF_NO = "//input[@id = 'rdbgCompanyRegisteredInSIIFValue_1']"

    # === SELECTORES CDP (lineas 536-572) ===
    BTN_AGREGAR_CDP = "btnAddCode"
    FRAME_CDP = "SIIFModal_iframe"
    RADIO_CDP = "rdbgOptionsToSelectRadioButton_0"
    RADIO_VIGENCIAS_FUTURAS = "rdbgOptionsToSelectRadioButton_1"
    INPUT_CODIGO_CDP = "//input[@id = 'txtSIIFIntegrationItemTextbox']"
    INPUT_SALDO_CDP = "//input[@id = 'cbxSIIFIntegrationItemBalanceTextbox']"
    INPUT_SALDO_COMPROMETER = "//input[@id = 'cbxSIIFIntegrationItemUsedValueTextbox']"
    INPUT_SUBUNIDAD = "//input[@id = 'txtSIIFIntegrationItemPCICodebox']"
    BTN_CREAR_CDP = "btnSIIFIntegrationItemButton"

    # === GUARDAR (lineas 577-584) ===
    BTN_GUARDAR = "//input[@id = 'btnSaveProcedureTop']"

    def configurar_proceso(self, datos):
        """
        Ejecuta la configuracion completa del proceso.
        Retorna la URL del proceso guardado. SIN escrituras a Google Sheets.

        Original: funciones.py:384-597 — configuracion_proceso(params)
        """
        url_proceso_2 = datos['estado_proceso_2']
        fecha_firma = datos['fecha_firma_contrato']
        fecha_inicio = datos['fecha_inicio']
        fecha_fin = datos['fecha_fin']
        valor_estimado = datos['valor_estimado']
        destinacion_gasto = datos['destinacion_gasto']
        tipo_cdp = datos['tipo_cdp']
        codigo_cdp = datos['codigo_cdp']
        saldo_cdp = datos['saldo_cdp']

        print("Configurando proceso...")
        self.driver.get(url_proceso_2)

        self._avanzar_a_configuracion()
        self._configurar_opciones_regulatorias()
        self._llenar_fechas_y_valor(fecha_firma, fecha_inicio, fecha_fin, valor_estimado)
        self._configurar_destinacion_gasto(destinacion_gasto, valor_estimado)

        # SIIF (linea 529-531)
        self.esperar_y_click(self.RADIO_SIIF_NO)

        # Validar CDPs (lineas 532-534)
        if len(codigo_cdp) != len(saldo_cdp):
            raise Exception("Error de cdps: La cantidad de cdps no coinciden con la cantidad de saldos")

        self._agregar_cdps(codigo_cdp, saldo_cdp, tipo_cdp)
        return self._guardar_y_obtener_url()

    # =========================================================================
    # METODOS PRIVADOS
    # =========================================================================

    def _avanzar_a_configuracion(self):
        """Lineas 401-434: Avanza a la seccion de configuracion."""
        # Intentar flujo principal: Continuar -> Aceptar
        try:
            self.esperar_y_click(self.BTN_CONTINUAR)
            self.esperar_y_click(self.BTN_ACEPTAR_CONTINUAR)
        except Exception:
            # Flujo alternativo: click en flecha (lineas 417-422)
            self.esperar_y_click(self.FLECHA_CONTINUAR)

        # Cerrar modal de acuerdo marco si aparece (lineas 423-432)
        try:
            self.cambiar_a_frame(self.FRAME_ACUERDO_MARCO)
            self.esperar_y_click(self.BTN_CERRAR_ACUERDO_MARCO)
        except Exception:
            pass

        self.volver_contenido_principal()

    def _configurar_opciones_regulatorias(self):
        """Lineas 436-446: Decreto 248, Sentencia T302, Acuerdos de paz — todos NO."""
        self.esperar_y_click(self.RADIO_DECRETO_248_NO)
        self.esperar_y_click(self.RADIO_SENTENCIA_T302_NO)
        self.esperar_y_click(self.RADIO_ACUERDOS_PAZ_NO)

    def _llenar_fechas_y_valor(self, fecha_firma, fecha_inicio, fecha_fin, valor_estimado):
        """Lineas 448-459: Firma, inicio ejecucion, plazo, valor estimado."""
        self.esperar_y_escribir(self.INPUT_FIRMA_CONTRATO, fecha_firma)
        self.esperar_y_escribir(self.INPUT_FECHA_INICIO, fecha_inicio)
        self.esperar_y_escribir(self.INPUT_PLAZO_EJECUCION, fecha_fin)
        self.esperar_y_escribir(self.INPUT_VALOR_ESTIMADO, valor_estimado)

    def _configurar_destinacion_gasto(self, destinacion_gasto, valor_estimado):
        """Lineas 461-527: Configura la destinacion del gasto y origen presupuestal."""
        if str(destinacion_gasto) == "1":
            self._configurar_funcionamiento(valor_estimado)
        elif str(destinacion_gasto) == "2":
            self._configurar_inversion(valor_estimado)

    def _configurar_funcionamiento(self, valor_estimado):
        """Lineas 461-494: Destinacion = Funcionamiento."""
        self.seleccionar_dropdown(self.SELECT_DEST_GASTO, "Funcionamiento")
        self.esperar_y_click(self.RADIO_PNG_NO)
        self.esperar_y_click(self.RADIO_SGP_NO)
        self.esperar_y_click(self.RADIO_SGR_NO)
        self.esperar_y_click(self.RADIO_REC_PROPIOS_NO)
        self.esperar_y_click(self.RADIO_REC_CREDITO_NO)
        self.esperar_y_click(self.RADIO_OTROS_REC_SI)
        self.esperar_y_escribir_por_id(self.INPUT_OTROS_RECURSOS, valor_estimado)

    def _configurar_inversion(self, valor_estimado):
        """Lineas 495-527: Destinacion = Inversion."""
        self.seleccionar_dropdown(self.SELECT_DEST_GASTO, "Inversion")
        self.esperar_y_click(self.RADIO_PNG_NO)
        self.esperar_y_click(self.RADIO_SGP_NO)
        self.esperar_y_click(self.RADIO_SGR_SI)
        self.esperar_y_click(self.RADIO_REC_PROPIOS_NO)
        self.esperar_y_click(self.RADIO_REC_CREDITO_NO)
        self.esperar_y_click(self.RADIO_OTROS_REC_NO)
        self.esperar_y_escribir_por_id(self.INPUT_SGR, valor_estimado)

    def _agregar_cdps(self, codigos_cdp, saldos_cdp, tipo_cdp):
        """Lineas 536-575: Agrega los CDPs al proceso."""
        print(f"Agregando {len(codigos_cdp)} CDP(s)...")
        try:
            for i in range(len(codigos_cdp)):
                self._agregar_un_cdp(
                    codigos_cdp[i].replace(" ", ""),
                    saldos_cdp[i],
                    tipo_cdp
                )
        except Exception:
            raise Exception("Error de cdps: No fue posible agregar CDP")

    def _agregar_un_cdp(self, codigo, saldo, tipo_cdp):
        """Lineas 540-572: Agrega un CDP individual."""
        self.esperar_y_click_por_id(self.BTN_AGREGAR_CDP)
        self.cambiar_a_frame(self.FRAME_CDP)

        # Seleccionar tipo CDP (lineas 548-555)
        if str(tipo_cdp) == "1":
            self.esperar_y_click_por_id(self.RADIO_CDP)
        elif str(tipo_cdp) == "2":
            self.esperar_y_click_por_id(self.RADIO_VIGENCIAS_FUTURAS)

        # Llenar datos (lineas 557-568)
        self.esperar_y_escribir(self.INPUT_CODIGO_CDP, codigo)
        self.esperar_y_escribir(self.INPUT_SALDO_CDP, saldo)
        self.esperar_y_escribir(self.INPUT_SALDO_COMPROMETER, saldo)
        self.esperar_y_escribir(self.INPUT_SUBUNIDAD, "00-00-00")

        # Crear y volver (lineas 569-572)
        self.esperar_y_click_por_id(self.BTN_CREAR_CDP)
        self.volver_contenido_principal()

    def _guardar_y_obtener_url(self):
        """Lineas 577-584: Guarda la configuracion y retorna la URL."""
        self.esperar_y_click(self.BTN_GUARDAR)
        self.esperar_exito()
        url = self.url_actual
        print(f"Configuracion guardada: {url}")
        return url
