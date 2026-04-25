# -*- coding: utf-8 -*-
"""
Módulo base para el patrón Page Object de la automatización en SECOP II.

Este archivo centraliza las operaciones, encapsulando la lógica de 
interacción con la interfaz web de manera robusta y estable mediante 'seleniumbase'.

Clases principales:
    - WaitForURLChange: Condición personalizada que verifica si la URL ha cambiado.
    - ElementoEstable: Condición personalizada que espera a que un elemento web se estabilice en el DOM.
    - BasePage: Clase padre (base) para todos los Page Objects del proyecto, ahora usando BaseCase (sb) de SeleniumBase.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log_step as print

# =========================================================================
# CONDICIONES PERSONALIZADAS (Custom Expected Conditions)
# =========================================================================

class WaitForURLChange:
    """Espera hasta que la URL del navegador cambie respecto a la URL dada."""
    def __init__(self, current_url):
        self.current_url = current_url

    def __call__(self, driver):
        return driver.current_url != self.current_url


class ElementoEstable:
    """
    Espera que un elemento sea visible Y no cambie de posicion/tamaño
    durante un intervalo breve (estabilidad de DOM tras animaciones).
    """
    def __init__(self, locator, estabilidad_ms=300):
        self.locator = locator
        self.estabilidad_ms = estabilidad_ms
        self._ultima_pos = None
        self._ultimo_check = None

    def __call__(self, driver):
        import time
        try:
            el = driver.find_element(*self.locator)
            if not el.is_displayed():
                return False
            pos_actual = (el.location, el.size)
            ahora = time.time()
            if pos_actual != self._ultima_pos:
                self._ultima_pos = pos_actual
                self._ultimo_check = ahora
                return False
            if self._ultimo_check and (ahora - self._ultimo_check) >= (self.estabilidad_ms / 1000):
                return el
            return False
        except Exception:
            self._ultima_pos = None
            return False


# =========================================================================
# DEFAULT TIMEOUTS
# =========================================================================
DEFAULT_TIMEOUT = 10
LONG_TIMEOUT = 20
SAVE_TIMEOUT = 40
POLL_FREQUENCY = 0.5
UI_SETTLE_MS = 300


# =========================================================================
# BASE PAGE
# =========================================================================

class BasePage:
    """
    Clase base para todos los Page Objects usando seleniumbase.
    Las esperas y acciones habituales son manejadas de forma nativa por self.sb
    """

    def __init__(self, sb):
        """
        Inicializa la BasePage con la instancia de SeleniumBase (sb).
        """
        self.sb = sb
        self.driver = sb.driver

    # --- WAITS INTERNOS ---

    def _wait(self, timeout=DEFAULT_TIMEOUT):
        """Crea un WebDriverWait nativo para casos particulares."""
        return WebDriverWait(self.driver, timeout, poll_frequency=POLL_FREQUENCY)

    def _esperar_dom_estable(self, locator, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento sea visible y estable en el DOM."""
        return self._wait(timeout).until(ElementoEstable(locator, UI_SETTLE_MS))

    # --- CLICK ---

    def esperar_y_click(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Espera clickeable y hace click via SeleniumBase."""
        self.sb.click(xpath, by=By.XPATH, timeout=timeout)
        try:
            return self.driver.find_element(By.XPATH, xpath)
        except Exception:
            return None

    def esperar_y_click_por_id(self, element_id, timeout=DEFAULT_TIMEOUT):
        """Espera clickeable por ID y hace click."""
        self.sb.click(f"#{element_id}", by=By.CSS_SELECTOR, timeout=timeout)
        try:
            return self.driver.find_element(By.ID, element_id)
        except Exception:
            return None

    def click_cuando_estable(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Espera que el elemento sea visible y estable, luego hace click."""
        elemento = self._esperar_dom_estable((By.XPATH, xpath), timeout)
        self.sb.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", elemento)
        elemento.click()
        return elemento
    
    # --- ESCRIBIR ---

    def esperar_y_escribir(self, xpath, texto, timeout=DEFAULT_TIMEOUT):
        """Espera clickeable y escribe texto."""
        self.sb.type(xpath, texto, by=By.XPATH, timeout=timeout)
        try:
            return self.driver.find_element(By.XPATH, xpath)
        except Exception:
            return None

    def esperar_y_escribir_por_id(self, element_id, texto, timeout=DEFAULT_TIMEOUT):
        """Espera clickeable por ID y escribe texto."""
        self.sb.type(f"#{element_id}", texto, by=By.CSS_SELECTOR, timeout=timeout)
        try:
            return self.driver.find_element(By.ID, element_id)
        except Exception:
            return None

    def limpiar_y_escribir(self, xpath, texto, timeout=DEFAULT_TIMEOUT):
        """Limpia el campo y escribe texto."""
        self.sb.update_text(xpath, texto, by=By.XPATH, timeout=timeout)
        try:
            return self.driver.find_element(By.XPATH, xpath)
        except Exception:
            return None

    def limpiar_y_escribir_por_id(self, element_id, texto, timeout=DEFAULT_TIMEOUT):
        """Limpia el campo por ID y escribe texto."""
        self.sb.update_text(f"#{element_id}", texto, by=By.CSS_SELECTOR, timeout=timeout)
        try:
            return self.driver.find_element(By.ID, element_id)
        except Exception:
            return None

    # --- ESPERAR ELEMENTOS ---

    def esperar_elemento(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento esté presente/sea interactuable por XPATH."""
        # Se requiere devolver elemento
        self.sb.wait_for_element(xpath, by=By.XPATH, timeout=timeout)
        return self.driver.find_element(By.XPATH, xpath)

    def esperar_elemento_por_id(self, element_id, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento esté presente por ID."""
        self.sb.wait_for_element(f"#{element_id}", by=By.CSS_SELECTOR, timeout=timeout)
        return self.driver.find_element(By.ID, element_id)

    def esperar_visible(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento sea visible."""
        self.sb.wait_for_element_visible(xpath, by=By.XPATH, timeout=timeout)
        return self.driver.find_element(By.XPATH, xpath)

    def esperar_presente(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento este presente en el DOM."""
        self.sb.wait_for_element_present(xpath, by=By.XPATH, timeout=timeout)
        return self.driver.find_element(By.XPATH, xpath)

    def esperar_invisible(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento desaparezca."""
        self.sb.wait_for_element_not_visible(xpath, by=By.XPATH, timeout=timeout)
        return True

    def esperar_texto_en_elemento(self, xpath, texto, timeout=DEFAULT_TIMEOUT):
        """Espera que un elemento contenga cierto texto."""
        self.sb.wait_for_text(texto, xpath, by=By.XPATH, timeout=timeout)
        return self.driver.find_element(By.XPATH, xpath)

    # --- DROPDOWNS ---

    def seleccionar_dropdown(self, element_id, texto_visible, timeout=LONG_TIMEOUT):
        """Selecciona por texto visible."""
        self.sb.select_option_by_text(f"#{element_id}", texto_visible, timeout=timeout)

    # --- FRAMES ---

    def cambiar_a_frame(self, frame_id, timeout=LONG_TIMEOUT):
        """Espera que el iframe este disponible y cambia a el."""
        self.sb.switch_to_frame(f"#{frame_id}", timeout=timeout)

    def volver_contenido_principal(self):
        """Vuelve al contenido principal saliendo de cualquier iframe."""
        self.sb.switch_to_default_content()

    # --- SCROLL ---

    def scroll_y_click(self, elemento, timeout=DEFAULT_TIMEOUT):
        """Scroll al elemento y click."""
        if isinstance(elemento, str):
            self.sb.scroll_to(elemento, by=By.XPATH)
            self.sb.click(elemento, by=By.XPATH, timeout=timeout)
        else:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", elemento)
            self._wait(timeout).until(EC.element_to_be_clickable(elemento))
            elemento.click()

    def scroll_a_elemento(self, elemento):
        """Solo hace scroll al elemento sin click."""
        if isinstance(elemento, str):
            self.sb.scroll_to(elemento, by=By.XPATH)
        else:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", elemento)

    # --- GUARDADO Y EXITO ---

    def esperar_exito(self, texto="Proceso guardado con éxito", timeout=SAVE_TIMEOUT):
        """Espera el mensaje de exito tras guardar un proceso."""
        self.sb.wait_for_element_present(f"//td[contains(text(), '{texto}')]", by=By.XPATH, timeout=timeout)

    # --- URL ---

    def esperar_cambio_url(self, url_actual, timeout=LONG_TIMEOUT):
        """Espera que la URL cambie respecto a la URL actual."""
        self._wait(timeout).until(WaitForURLChange(url_actual))
        return self.sb.get_current_url()

    def esperar_url_contiene(self, fragmento, timeout=LONG_TIMEOUT):
        """Espera que la URL contenga un fragmento especifico."""
        self._wait(timeout).until(EC.url_contains(fragmento))
        return self.sb.get_current_url()

    # --- AUTOCOMPLETE ---

    def escribir_y_seleccionar_autocomplete(self, element_id, texto, timeout=DEFAULT_TIMEOUT):
        """Escribe en un campo con autocomplete, espera resultados y selecciona."""
        self.sb.type(f"#{element_id}", texto, by=By.CSS_SELECTOR, timeout=timeout)
        xpath_resultado = f"//span[contains(text(), '{texto}')]"
        self.sb.click(xpath_resultado, by=By.XPATH, timeout=timeout)
        try:
            return self.driver.find_element(By.XPATH, xpath_resultado)
        except Exception:
            return None

    def escribir_y_seleccionar_primer_li(self, element_id, texto, timeout=DEFAULT_TIMEOUT):
        """Escribe en un campo y selecciona el primer <li>."""
        self.sb.type(f"#{element_id}", texto, by=By.CSS_SELECTOR, timeout=timeout)
        xpath_li = "//div[@class='ac_results']//li[1]//span[1]//span"
        self.sb.click(xpath_li, by=By.XPATH, timeout=timeout)
        try:
            return self.driver.find_element(By.XPATH, xpath_li)
        except Exception:
            return None

    # --- VERIFICACION DE EXISTENCIA ---

    def not_exist_element(self, xpath, timeout=DEFAULT_TIMEOUT):
        """Verifica si un elemento NO existe."""
        try:
            self.sb.wait_for_element_present(xpath, by=By.XPATH, timeout=timeout)
            return False  # Existe
        except Exception:
            return True   # No existe

    # --- ALERTAS ---

    def aceptar_alerta_si_existe(self, timeout=3):
        """Acepta un alert del navegador si aparece."""
        try:
            self._wait(timeout).until(EC.alert_is_present())
            self.sb.accept_alert()
            return True
        except Exception:
            return False

    # --- WRAPPERS DE BAJO NIVEL ---

    def find_element(self, by, value):
        """Wrapper para driver.find_element."""
        return self.driver.find_element(by, value)

    def find_elements(self, by, value):
        """Wrapper para driver.find_elements."""
        return self.driver.find_elements(by, value)

    def ejecutar_js(self, script, *args):
        """Wrapper para ejecutar scripts."""
        return self.sb.execute_script(script, *args)

    @property
    def url_actual(self):
        """Retorna la URL actual del navegador."""
        return self.sb.get_current_url()
