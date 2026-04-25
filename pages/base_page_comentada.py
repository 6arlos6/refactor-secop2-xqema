# -*- coding: utf-8 -*-

# =========================
# IMPORTS SELENIUM
# =========================
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains

# Sobrescribes print con tu logger (buena práctica)
from utils.logger import log_step as print


# =========================================================================
# CONDICIONES PERSONALIZADAS (Custom Expected Conditions)
# =========================================================================

class WaitForURLChange:
    """
    Espera hasta que la URL cambie respecto a una URL inicial.

    Uso típico:
        después de login o submit que redirige
    """
    def __init__(self, current_url):
        self.current_url = current_url

    def __call__(self, driver):
        # Retorna True cuando cambia la URL → condición cumplida
        return driver.current_url != self.current_url


class ElementoEstable:
    """
    Espera que un elemento:
    1. Sea visible
    2. NO cambie de posición ni tamaño durante un tiempo

    🔥 Esto soluciona:
    - Animaciones CSS
    - Render tardío del DOM
    - Elementos "clickeables" pero aún moviéndose

    Reemplaza:
        time.sleep() después de un render
    """

    def __init__(self, locator, estabilidad_ms=300):
        self.locator = locator
        self.estabilidad_ms = estabilidad_ms
        self._ultima_pos = None
        self._ultimo_check = None

    def __call__(self, driver):
        import time
        try:
            # Buscar elemento
            el = driver.find_element(*self.locator)

            # Debe ser visible
            if not el.is_displayed():
                return False

            # Posición + tamaño (firma del elemento)
            pos_actual = (el.location, el.size)
            ahora = time.time()

            # Si cambió → reiniciar contador
            if pos_actual != self._ultima_pos:
                self._ultima_pos = pos_actual
                self._ultimo_check = ahora
                return False

            # Si se mantuvo estable suficiente tiempo → OK
            if self._ultimo_check and (ahora - self._ultimo_check) >= (self.estabilidad_ms / 1000):
                return el

            return False

        except Exception:
            # Si falla (elemento no existe), reinicia estado
            self._ultima_pos = None
            return False


# =========================================================================
# TIMEOUTS CENTRALIZADOS
# =========================================================================

DEFAULT_TIMEOUT = 10     # Espera estándar
LONG_TIMEOUT = 20        # Operaciones más lentas (iframes, modales)
SAVE_TIMEOUT = 40        # Guardados en backend
POLL_FREQUENCY = 0.5     # Cada cuánto Selenium vuelve a intentar
UI_SETTLE_MS = 300       # Tiempo de estabilidad del DOM


# =========================================================================
# BASE PAGE (CORE DEL FRAMEWORK)
# =========================================================================

class BasePage:
    """
    Clase base para TODOS los Page Objects.

    🔥 Responsabilidad:
    Encapsular interacción con Selenium de forma:
    - reutilizable
    - robusta
    - sin time.sleep()

    Todas las páginas heredan de aquí.
    """

    def __init__(self, driver):
        self.driver = driver

    # =========================
    # WAITS INTERNOS
    # =========================

    def _wait(self, timeout=DEFAULT_TIMEOUT):
        """
        Crea un WebDriverWait con polling controlado.
        """
        return WebDriverWait(self.driver, timeout, poll_frequency=POLL_FREQUENCY)

    def _esperar_dom_estable(self, locator, timeout=DEFAULT_TIMEOUT):
        """
        Espera que un elemento esté estable (no moviéndose).
        """
        return self._wait(timeout).until(
            ElementoEstable(locator, UI_SETTLE_MS)
        )

    # =========================
    # CLICK
    # =========================

    def esperar_y_click(self, xpath, timeout=DEFAULT_TIMEOUT):
        """
        Espera a que el elemento sea clickeable y hace click.
        Usa ActionChains para mayor compatibilidad (hover, overlays).
        """
        elemento = self._wait(timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        ActionChains(self.driver).move_to_element(elemento).click().perform()
        return elemento

    def click_cuando_estable(self, xpath, timeout=DEFAULT_TIMEOUT):
        """
        🔥 CLAVE:
        Espera que el elemento deje de moverse antes de hacer click.
        """
        elemento = self._esperar_dom_estable((By.XPATH, xpath), timeout)
        ActionChains(self.driver).move_to_element(elemento).click().perform()
        return elemento

    # =========================
    # INPUTS
    # =========================

    def limpiar_y_escribir(self, xpath, texto, timeout=DEFAULT_TIMEOUT):
        """
        Limpia un input y espera a que quede vacío antes de escribir.
        Evita bugs donde el clear() no se aplica inmediatamente.
        """
        elemento = self._wait(timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        elemento.clear()

        # Esperar que realmente esté vacío
        self._wait(3).until(
            lambda d: elemento.get_attribute('value') == ''
        )

        elemento.send_keys(texto)
        return elemento

    # =========================
    # DROPDOWNS
    # =========================

    def seleccionar_dropdown(self, element_id, texto_visible, timeout=LONG_TIMEOUT):
        """
        Espera que el select cargue sus opciones antes de seleccionar.
        """
        select_element = self._wait(timeout).until(
            EC.presence_of_element_located((By.ID, element_id))
        )

        # Esperar a que haya opciones (evita selects vacíos)
        self._wait(timeout).until(
            lambda d: len(Select(d.find_element(By.ID, element_id)).options) > 1
        )

        Select(select_element).select_by_visible_text(texto_visible)

    # =========================
    # FRAMES
    # =========================

    def cambiar_a_frame(self, frame_id, timeout=LONG_TIMEOUT):
        """
        Espera iframe y cambia el contexto.
        """
        self._wait(timeout).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, frame_id))
        )

    def volver_contenido_principal(self):
        """Sale de cualquier iframe."""
        self.driver.switch_to.default_content()

    # =========================
    # SCROLL
    # =========================

    def scroll_y_click(self, elemento, timeout=DEFAULT_TIMEOUT):
        """
        Hace scroll y luego click seguro.
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            elemento
        )

        self._wait(timeout).until(
            EC.element_to_be_clickable(elemento)
        )

        elemento.click()

    # =========================
    # VALIDACIONES
    # =========================

    def not_exist_element(self, xpath, timeout=DEFAULT_TIMEOUT):
        """
        Retorna True si el elemento NO aparece.
        """
        try:
            self._wait(timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return False
        except Exception:
            return True

    # =========================
    # ALERTAS
    # =========================

    def aceptar_alerta_si_existe(self, timeout=3):
        """
        Maneja alerts JS automáticamente.
        """
        try:
            self._wait(timeout).until(EC.alert_is_present())
            self.driver.switch_to.alert.accept()
            return True
        except Exception:
            return False

    # =========================
    # URL
    # =========================

    def esperar_cambio_url(self, url_actual, timeout=LONG_TIMEOUT):
        """
        Espera redirección de página.
        """
        self._wait(timeout).until(
            WaitForURLChange(url_actual)
        )
        return self.driver.current_url