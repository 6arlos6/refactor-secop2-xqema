# -*- coding: utf-8 -*-
"""
Page Object: Obtener Enlace Publico del Proceso
Extraido de: proyecto-original-secob/funciones.py lineas 1019-1062 (obtener_enlace)

NOTA: Este page object maneja su PROPIO driver Chrome independiente
porque necesita una sesion limpia para obtener el enlace publico.
"""
from selenium.webdriver.common.by import By
from seleniumbase import Driver
from pages.login_page import LoginPage
from pages.base_page import BasePage
from utils.logger import log_step as print
from config.settings import HEADLESS_MODE


# Timeouts para la obtencion de enlace
ENLACE_TIMEOUT = 30
ENLACE_LONG_TIMEOUT = 100  # 50 tries * 2s en el original


class PublicacionPage:
    """
    Obtiene el enlace publico de un proceso publicado.
    Maneja su propio driver Chrome (sesion independiente).

    Original: funciones.py:1019-1062 — obtener_enlace(url, sheet, indice)
    """

    # === SELECTORES ===
    LINK_EXPEDIENTE = "//*[@id='breadcrumb']/a[4]"
    BTN_VER_ENLACE = "//input[@id = 'btnSeePublicContractNoticeLink']"
    SPAN_ENLACE = "//span[@id = 'spnPublicContractNoticeLink']"
    LABEL_ENLACE_FINAL = "//label[@id = 'lblDisplayPhaseLink_0']"

    def obtener_enlace(self, url):
        """
        Obtiene el enlace publico del proceso publicado.
        Retorna el texto del enlace o cadena vacia si falla.
        SIN escrituras a Google Sheets.
        """
        print("Obteniendo enlace publico del proceso...")

        driver = Driver(incognito=True, headless=HEADLESS_MODE)
        if not HEADLESS_MODE:
            driver.maximize_window()

        try:
            # Login con driver independiente (lineas 1027)
            login_page = LoginPage(driver)
            login_page.iniciar_sesion()

            driver.get(url)
            base = BasePage(driver)

            # Buscar link del expediente (lineas 1031-1038)
            # not_exist_element con timeout=100s reemplaza notExistElement(driver, 50, ...)
            if base.not_exist_element(self.LINK_EXPEDIENTE, timeout=ENLACE_LONG_TIMEOUT):
                print("Link de expediente no encontrado.")
                return ''

            base.esperar_y_click(self.LINK_EXPEDIENTE)

            # Buscar boton "Ver enlace" (lineas 1041-1048)
            if base.not_exist_element(self.BTN_VER_ENLACE, timeout=ENLACE_TIMEOUT):
                print("Boton ver enlace no encontrado.")
                return ''

            base.esperar_y_click(self.BTN_VER_ENLACE)

            # Obtener texto del enlace (lineas 1051-1062)
            if base.not_exist_element(self.SPAN_ENLACE, timeout=ENLACE_TIMEOUT):
                print("Span de enlace no encontrado.")
                return ''

            texto_enlace = driver.find_element(By.XPATH, self.SPAN_ENLACE).text

            # Navegar al enlace y obtener el texto final (lineas 1057-1060)
            driver.get(texto_enlace)
            base.esperar_visible(self.LABEL_ENLACE_FINAL, timeout=ENLACE_TIMEOUT)
            texto_enlace_real = driver.find_element(By.XPATH, self.LABEL_ENLACE_FINAL).text

            print(f"Enlace publico obtenido: {texto_enlace_real}")
            return texto_enlace_real

        except Exception as e:
            print(f"Error obteniendo enlace: {e}")
            return ''

        finally:
            try:
                driver.quit()
            except Exception:
                pass
