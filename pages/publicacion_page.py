# -*- coding: utf-8 -*-
"""
Page Object: Obtener Enlace Publico del Proceso
Extraido de: proyecto-original-secob/funciones.py lineas 1019-1062 (obtener_enlace)

NOTA: Este page object maneja su PROPIO driver Chrome independiente
porque necesita una sesion limpia para obtener el enlace publico.
"""
from selenium.webdriver.common.by import By
from pages.login_page import LoginPage
from pages.base_page import BasePage
from utils.logger import log_step as print


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

    # Numero de intentos de login antes de rendirse
    MAX_INTENTOS_LOGIN = 2

    def obtener_enlace(self, url):
        """
        Obtiene el enlace publico del proceso publicado.
        Retorna el texto del enlace o cadena vacia si falla.
        SIN escrituras a Google Sheets.

        Login con reintento: SECOP II usa un STS (Identity Provider) que a veces
        devuelve una pagina de error por "sesion expirada por inactividad" en la primera
        solicitud (token de autenticacion generado con timestamp que puede vencer si el
        proceso tardo varios minutos en los pasos anteriores). Un segundo intento con el
        mismo driver (navegar_a() reinicia el flujo desde URL_LOGIN_SECOP) suele resolver
        el problema sin crear un nuevo driver.
        """
        import time
        print("Obteniendo enlace publico del proceso...")

        driver = BasePage.crear_driver(incognito=True)

        try:
            # Login con driver independiente (lineas 1027) — con reintento
            login_page = LoginPage(driver)
            for intento in range(1, self.MAX_INTENTOS_LOGIN + 1):
                try:
                    login_page.iniciar_sesion()
                    break  # login exitoso
                except Exception as e_login:
                    if intento < self.MAX_INTENTOS_LOGIN:
                        print(f"Login fallido (intento {intento}/{self.MAX_INTENTOS_LOGIN}): {e_login}")
                        print(f"Reintentando login en 5s...")
                        time.sleep(5)
                    else:
                        raise  # ultimo intento fallido — propagar al except externo

            base = BasePage(driver)
            base.navegar_a(url)

            # Buscar link del expediente (lineas 1031-1038)
            # not_exist_element con timeout=100s reemplaza notExistElement(driver, 50, ...)
            if base.not_exist_element(self.LINK_EXPEDIENTE, timeout=ENLACE_LONG_TIMEOUT):
                print("Link de expediente no encontrado.")
                return ''

            # JS click: en headless el vortal-preloader puede interceptar el click nativo.
            # esperar_y_click_js_xpath elimina overlays (.blockUI, .vortal-preloader) via JS
            # antes de hacer el click, igual que en los demas page objects de SECOP II.
            base.esperar_y_click_js_xpath(self.LINK_EXPEDIENTE)

            # Buscar boton "Ver enlace" (lineas 1041-1048)
            # Timeout extendido: algunos tipos de proceso cargan el boton mas lento.
            if base.not_exist_element(self.BTN_VER_ENLACE, timeout=ENLACE_LONG_TIMEOUT):
                # El boton no aparecio. Intentar construir el enlace publico buscando
                # el identificador CO1.NTC en el HTML de la pagina: SECOP siempre lo
                # incluye en el DOM tras publicar, aunque el boton no sea visible.
                import re as _re
                try:
                    match = _re.search(r'CO1\.NTC\.\d+', driver.page_source)
                    if match:
                        ntc_id = match.group(0)
                        public_url = (
                            "https://community.secop.gov.co/Public/Tendering/"
                            f"OpportunityDetail/Index?noticeUID={ntc_id}"
                            "&isFromPublicArea=True&isModal=False"
                        )
                        print(f"Enlace publico construido desde {ntc_id}: {public_url}")
                        return public_url
                except Exception:
                    pass
                url_fallback = driver.current_url
                print(f"Boton ver enlace no encontrado. Guardando URL del expediente: {url_fallback}")
                return url_fallback

            # Mismo patron: JS click para evitar intercepcion por overlay.
            base.esperar_y_click_js_xpath(self.BTN_VER_ENLACE)

            # Obtener texto del enlace (lineas 1051-1062)
            if base.not_exist_element(self.SPAN_ENLACE, timeout=ENLACE_TIMEOUT):
                import re as _re
                try:
                    match = _re.search(r'CO1\.NTC\.\d+', driver.page_source)
                    if match:
                        ntc_id = match.group(0)
                        public_url = (
                            "https://community.secop.gov.co/Public/Tendering/"
                            f"OpportunityDetail/Index?noticeUID={ntc_id}"
                            "&isFromPublicArea=True&isModal=False"
                        )
                        print(f"Enlace publico construido desde {ntc_id}: {public_url}")
                        return public_url
                except Exception:
                    pass
                url_fallback = driver.current_url
                print(f"Span de enlace no encontrado. Guardando URL actual: {url_fallback}")
                return url_fallback

            texto_enlace = driver.find_element(By.XPATH, self.SPAN_ENLACE).text

            # Navegar al enlace y obtener el texto final (lineas 1057-1060)
            base.navegar_a(texto_enlace)
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
