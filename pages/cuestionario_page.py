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

        # Navegar al tab de cuestionario (reemplaza time.sleep(10) + find_element)
        self.click_cuando_estable(self.BTN_CUESTIONARIO, timeout=LONG_TIMEOUT)

        # Expandir campos (reemplaza time.sleep(5) + click)
        self.esperar_y_click(self.BTN_EXPANDIR, timeout=LONG_TIMEOUT)

        # Llenar codigo UNSPSC con autocomplete (reemplaza clear + sleep(1) + send_keys + sleep(1))
        self.limpiar_y_escribir(self.INPUT_UNSPSC, codigo)

        # Seleccionar del autocomplete (reemplaza find_element + sleep(2) + ActionChains)
        xpath_lista = f"//span[contains(text(), '{codigo}')]"
        self.esperar_y_click(xpath_lista)

        # Llenar descripcion, precio y cantidad (lineas 635-640)
        self.esperar_y_escribir(self.INPUT_DESCRIPCION, descripcion)
        self.esperar_y_escribir(self.INPUT_PRECIO_UNITARIO, valor)
        self.esperar_y_escribir(self.INPUT_CANTIDAD, "1")

        # Guardar (lineas 641-648)
        self.esperar_y_click(self.BTN_GUARDAR)
        self.esperar_exito()

        url = self.url_actual
        print(f"Cuestionario completado: {url}")
        return url
