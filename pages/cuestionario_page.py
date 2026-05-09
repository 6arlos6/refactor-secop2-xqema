# -*- coding: utf-8 -*-
"""
Page Object: Cuestionario del Proceso (Proceso 4)
Extraido de: proyecto-original-secob/funciones.py lineas 599-657 (completar_cuestionario)
"""
from pages.base_page import BasePage, DEFAULT_TIMEOUT, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.logger import log_step as print


class CuestionarioPage(BasePage):
    """Gestiona el completado del cuestionario del proceso en SECOP II."""

    # === SELECTORES ===
    BTN_CUESTIONARIO = "//span[@id = 'lnk_stpmStepManager4']"
    BTN_EXPANDIR = "//div[@class = 'FtlExpandAll']"
    INPUT_UNSPSC = "//input[contains(@id,'CategoryCode_LookupText')]"
    INPUT_DESCRIPCION = "//input[contains(@id,'_Description')]"
    INPUT_PRECIO_UNITARIO = "//input[contains(@id,'_CeilingPrice')]"
    INPUT_CANTIDAD = "//input[contains(@id,'_Quantity')]"
    BTN_GUARDAR = "//input[@id = 'tbToolBarPlaceHolder_btnSaveProcedureTop']"

    def completar(self, url_proceso_3, codigo, descripcion, valor):
        """
        Completa el cuestionario del proceso.
        Retorna la URL del proceso guardado. SIN escrituras a Google Sheets.

        Original: funciones.py:600-657 — completar_cuestionario(params)
        """
        print("Completando cuestionario...")
        self.driver.get(url_proceso_3)

        # Navegar al tab de cuestionario — usa click_limpio porque vortal-preloader
        # intercepta el click nativo inmediatamente tras la navegacion
        self.esperar_y_click_limpio(self.BTN_CUESTIONARIO, timeout=LONG_TIMEOUT)

        # Expandir campos (reemplaza time.sleep(5) + click)
        self.esperar_y_click(self.BTN_EXPANDIR, timeout=LONG_TIMEOUT)

        # UNSPSC: campo autocomplete jQuery UI — DEBE usar send_keys, no sb.type().
        # sb.type() establece el valor vía JS y no dispara keydown/keyup/input,
        # eventos que jQuery UI Autocomplete necesita para lanzar su petición AJAX.
        # enviar_teclas() hace click + clear + send_keys() reales.
        self.enviar_teclas(self.INPUT_UNSPSC, codigo)

        # Seleccionar del dropdown: dos VortalSpan se superponen y el click nativo
        # es interceptado. JS click lo resuelve igual que ActionChains en el original.
        xpath_lista = f"//span[contains(text(), '{codigo}')]"
        self.esperar_y_click_js_xpath(xpath_lista)

        # Descripcion, precio y cantidad son VortalTextBox/VortalNumericBox con
        # onchange="updateViewModel(..., $.getDecimalValue(...))" — necesitan
        # send_keys reales para que el onchange actualice el ViewModel de SECOP II.
        self.enviar_teclas(self.INPUT_DESCRIPCION, descripcion)
        self.enviar_teclas(self.INPUT_PRECIO_UNITARIO, valor)
        self.enviar_teclas(self.INPUT_CANTIDAD, "1")

        # Guardar (lineas 641-648)
        self.esperar_y_click(self.BTN_GUARDAR)
        self.esperar_exito()

        url = self.url_actual
        print(f"Cuestionario completado: {url}")
        return url
