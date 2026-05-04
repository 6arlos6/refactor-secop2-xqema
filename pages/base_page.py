# -*- coding: utf-8 -*-
"""
BasePage — Page Object Model para SECOP II
Usa SeleniumBase (self.sb) en lugar de raw Selenium + WebDriverWait.

Por qué SeleniumBase:
  - sb.click(selector)        → espera + retry automático (no necesita ActionChains)
  - sb.js_click(selector)     → JavaScript click para botones onclick/postForm de SECOP II
  - sb.type(selector, texto)  → clear + type con espera integrada
  - sb.wait_for_element_*(selector, timeout) → esperas explicitas sin time.sleep()

Modo de uso en este proyecto:
  - Se usa seleniumbase.Driver  (modo standalone, equivalente a webdriver.Chrome + SB API)
  - El proyecto de referencia (archivos_de_apoyo) usa BaseCase (modo pytest con SB())
  - Ambos modos exponen la misma API de sb.*; Driver es el correcto para nuestro orquestador

Expone self.driver (property) para page objects que aun usen raw driver durante la migracion.

Referencia de arquitectura: archivos_de_apoyo/base_page.py
"""
from seleniumbase import BaseCase
from utils.logger import log_step as print

# =========================================================================
# TIMEOUTS CENTRALIZADOS
# =========================================================================
DEFAULT_TIMEOUT = 10   # Espera estandar para elementos
LONG_TIMEOUT    = 20   # Espera para operaciones lentas (frames, modales, navegacion)
SAVE_TIMEOUT    = 40   # Espera para guardado de procesos (operaciones de red lentas)


# =========================================================================
# BASE PAGE
# =========================================================================

class BasePage:
    """
    Clase base para todos los Page Objects.
    Todas las esperas son dinamicas — SeleniumBase gestiona reintentos y
    polling internamente, sin time.sleep() ni WebDriverWait explícitos.
    """

    def __init__(self, sb: BaseCase):
        """
        sb: instancia de seleniumbase.Driver (modo standalone).
        Expone click, type, js_click, wait_for_element_*, open, etc.
        """
        self.sb = sb

    # -----------------------------------------------------------------------
    # PROPIEDAD driver (compatibilidad con page objects en migracion)
    # -----------------------------------------------------------------------

    @property
    def driver(self):
        """
        Acceso al WebDriver subyacente.
        Permite que page objects no migrados aun sigan usando self.driver.get(),
        self.driver.current_url, etc., sin romper el contrato.
        """
        return getattr(self.sb, 'driver', self.sb)

    # -----------------------------------------------------------------------
    # PROPIEDAD url
    # -----------------------------------------------------------------------

    @property
    def url_actual(self):
        return self.driver.current_url

    # -----------------------------------------------------------------------
    # NAVEGACION
    # -----------------------------------------------------------------------

    def navegar_a(self, url):
        self.driver.get(url)

    # -----------------------------------------------------------------------
    # OVERLAYS — Limpieza de overlays SECOP II
    #
    # SECOP II usa jQuery BlockUI y Vortal preloaders como overlays durante
    # operaciones AJAX. Estos tienen z-index:1000, position:fixed, opacity:0
    # (invisibles pero interceptan clicks nativos de Selenium).
    # El codigo original cubria esto con time.sleep() entre operaciones.
    # Nosotros los eliminamos del DOM antes de interactuar.
    # -----------------------------------------------------------------------

    def eliminar_overlays(self):
        """Elimina overlays blockUI y vortal-preloader del DOM via JS."""
        try:
            self.sb.execute_script("""
                document.querySelectorAll('.blockUI, .vortal-preloader').forEach(
                    function(el) { el.remove(); }
                );
            """)
        except Exception:
            pass  # Si falla el JS (ej: iframe sin acceso), seguir adelante

    # -----------------------------------------------------------------------
    # CLICKS
    # Patron SeleniumBase: sb.click() espera clickeable + retry automatico.
    # Para botones SECOP II con onclick/postForm: sb.js_click().
    # -----------------------------------------------------------------------

    def esperar_y_click(self, selector, timeout=DEFAULT_TIMEOUT):
        """Espera clickeable y click con retry automatico (reemplaza ActionChains)."""
        self.sb.click(selector, timeout=timeout)

    def esperar_y_click_por_id(self, element_id, timeout=DEFAULT_TIMEOUT):
        self.sb.click(f"#{element_id}", timeout=timeout)

    def click_cuando_estable(self, selector, timeout=DEFAULT_TIMEOUT):
        """Espera visible + estable y click. SB gestiona la estabilidad internamente."""
        self.sb.click(selector, timeout=timeout)

    def esperar_y_click_js(self, element_id, timeout=DEFAULT_TIMEOUT):
        """
        JavaScript click para botones SECOP II con onclick/postForm handlers.
        Equivale a driver.execute_script("arguments[0].click()") del codigo original.
        sb.js_click() realiza la misma operacion de forma limpia.
        Incluye limpieza de overlays para evitar ElementClickInterceptedException.
        """
        self.sb.wait_for_element_visible(f"#{element_id}", timeout=timeout)
        self.eliminar_overlays()
        self.sb.js_click(f"#{element_id}")

    def esperar_y_click_js_xpath(self, xpath, timeout=DEFAULT_TIMEOUT):
        """JS click por XPATH (para elementos sin ID unico)."""
        self.sb.wait_for_element_visible(xpath, timeout=timeout)
        self.eliminar_overlays()
        self.sb.js_click(xpath)

    def esperar_y_click_limpio(self, selector, timeout=DEFAULT_TIMEOUT):
        """
        Click nativo con limpieza previa de overlays.
        Usar cuando sb.click() falla por blockUI/vortal-preloader.
        """
        self.sb.wait_for_element_visible(selector, timeout=timeout)
        self.eliminar_overlays()
        self.sb.click(selector, timeout=timeout)

    # -----------------------------------------------------------------------
    # ESCRITURA
    # sb.type() incluye espera + clear + type en un solo paso.
    # -----------------------------------------------------------------------

    def esperar_y_escribir(self, selector, texto, timeout=DEFAULT_TIMEOUT):
        """Espera clickeable y escribe texto (sb.type hace clear+type)."""
        self.sb.type(selector, texto, timeout=timeout)

    def esperar_y_escribir_por_id(self, element_id, texto, timeout=DEFAULT_TIMEOUT):
        self.sb.type(f"#{element_id}", texto, timeout=timeout)

    def limpiar_y_escribir(self, selector, texto, timeout=DEFAULT_TIMEOUT):
        """Clear explicito + type. Util cuando se necesita forzar el clear."""
        self.sb.wait_for_element_visible(selector, timeout=timeout)
        self.sb.type(selector, texto, timeout=timeout)

    def limpiar_y_escribir_por_id(self, element_id, texto, timeout=DEFAULT_TIMEOUT):
        self.sb.wait_for_element_visible(f"#{element_id}", timeout=timeout)
        self.sb.type(f"#{element_id}", texto, timeout=timeout)

    # -----------------------------------------------------------------------
    # ESPERAS EXPLICITAS
    # Usadas cuando se necesita esperar un estado especifico antes de actuar.
    # -----------------------------------------------------------------------

    def esperar_elemento(self, selector, timeout=DEFAULT_TIMEOUT):
        return self.sb.wait_for_element_visible(selector, timeout=timeout)

    def esperar_elemento_por_id(self, element_id, timeout=DEFAULT_TIMEOUT):
        return self.sb.wait_for_element_visible(f"#{element_id}", timeout=timeout)

    def esperar_visible(self, selector, timeout=DEFAULT_TIMEOUT):
        return self.sb.wait_for_element_visible(selector, timeout=timeout)

    def esperar_presente(self, selector, timeout=DEFAULT_TIMEOUT):
        return self.sb.wait_for_element_present(selector, timeout=timeout)

    def esperar_invisible(self, selector, timeout=DEFAULT_TIMEOUT):
        return self.sb.wait_for_element_not_visible(selector, timeout=timeout)

    def esperar_texto_en_elemento(self, selector, texto, timeout=DEFAULT_TIMEOUT):
        return self.sb.wait_for_text(texto, selector, timeout=timeout)

    # -----------------------------------------------------------------------
    # DROPDOWNS (<select>)
    # -----------------------------------------------------------------------

    def seleccionar_dropdown(self, element_id, texto_visible, timeout=LONG_TIMEOUT):
        self.sb.wait_for_element_visible(f"#{element_id}", timeout=timeout)
        from selenium.webdriver.support.ui import Select
        select_element = self.driver.find_element("id", element_id)
        Select(select_element).select_by_visible_text(texto_visible)

    # -----------------------------------------------------------------------
    # AUTOCOMPLETE (patron comun en SECOP II — jQuery UI ac_results)
    # -----------------------------------------------------------------------

    def escribir_y_seleccionar_autocomplete(self, element_id, texto,
                                            timeout=DEFAULT_TIMEOUT):
        """
        Escribe en campo autocomplete jQuery UI y selecciona el primer resultado.

        POR QUE send_keys y NO type():
          sb.type() establece el valor via JavaScript (element.value = texto),
          lo que NO dispara los eventos keydown/keyup/input que jQuery UI
          Autocomplete necesita para lanzar su peticion AJAX y mostrar el dropdown.
          sb.send_keys() simula teclas reales y SI dispara esos eventos.

        Patron A : espera div.ac_results > li[1] visible y hace click
        Patron B : ARROW_DOWN + RETURN como fallback de teclado puro
        """
        from selenium.webdriver.common.keys import Keys

        # Enfocar y limpiar el campo antes de escribir
        self.sb.wait_for_element_visible(f"#{element_id}", timeout=timeout)
        self.sb.click(f"#{element_id}")
        self.driver.find_element("id", element_id).clear()

        # Enviar texto caracter a caracter (dispara keydown/keyup/input → jQuery UI AJAX)
        self.sb.send_keys(f"#{element_id}", texto)

        # Patron A: ac_results div (jQuery UI Autocomplete de SECOP II)
        try:
            self.sb.wait_for_element_visible(
                "//div[contains(@class,'ac_results')]//li[1]", timeout=8
            )
            self.sb.click("//div[contains(@class,'ac_results')]//li[1]")
            return
        except Exception:
            pass

        # Patron B: navegacion por teclado (fallback si el DOM no es clickeable)
        self.sb.send_keys(f"#{element_id}", Keys.ARROW_DOWN)
        self.sb.send_keys(f"#{element_id}", Keys.RETURN)

    def escribir_y_seleccionar_primer_li(self, element_id, texto,
                                         timeout=DEFAULT_TIMEOUT):
        """Alias de escribir_y_seleccionar_autocomplete."""
        self.escribir_y_seleccionar_autocomplete(element_id, texto, timeout)

    # -----------------------------------------------------------------------
    # FRAMES / IFRAMES
    # -----------------------------------------------------------------------

    def cambiar_a_frame(self, frame_id, timeout=LONG_TIMEOUT):
        """Espera que el iframe exista en el DOM y cambia al contexto de ese frame."""
        self.sb.wait_for_element_present(
            f"//iframe[@id='{frame_id}']", timeout=timeout
        )
        self.driver.switch_to.frame(frame_id)

    def volver_contenido_principal(self):
        self.driver.switch_to.default_content()

    # -----------------------------------------------------------------------
    # URL
    # -----------------------------------------------------------------------

    def esperar_cambio_url(self, url_actual, timeout=LONG_TIMEOUT):
        """
        Espera que la URL cambie desde url_actual.
        SeleniumBase no tiene wait_for_url_to_change_from() nativo,
        se usa WebDriverWait sobre el driver subyacente (unico punto que lo requiere).
        """
        from selenium.webdriver.support.wait import WebDriverWait
        raw_driver = getattr(self.sb, 'driver', self.sb)
        WebDriverWait(raw_driver, timeout, poll_frequency=0.3).until(
            lambda d: d.current_url != url_actual
        )
        return self.driver.current_url

    def esperar_url_contiene(self, fragmento, timeout=LONG_TIMEOUT):
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        raw_driver = getattr(self.sb, 'driver', self.sb)
        WebDriverWait(raw_driver, timeout, poll_frequency=0.3).until(
            EC.url_contains(fragmento)
        )
        return self.driver.current_url

    # -----------------------------------------------------------------------
    # VERIFICACION DE EXISTENCIA
    # -----------------------------------------------------------------------

    def not_exist_element(self, selector, timeout=DEFAULT_TIMEOUT):
        """Retorna True si el elemento NO existe/aparece dentro del timeout."""
        try:
            self.sb.wait_for_element_visible(selector, timeout=timeout)
            return False   # Existe
        except Exception:
            return True    # No existe

    # -----------------------------------------------------------------------
    # ALERTAS
    # -----------------------------------------------------------------------

    def aceptar_alerta_si_existe(self, timeout=3):
        try:
            from selenium.webdriver.support.wait import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            self.driver.switch_to.alert.accept()
            return True
        except Exception:
            return False

    # -----------------------------------------------------------------------
    # SCROLL
    # -----------------------------------------------------------------------

    def scroll_y_click(self, elemento, timeout=DEFAULT_TIMEOUT):
        """Scroll al elemento y click (SB gestiona scroll automaticamente)."""
        self.sb.execute_script(
            "arguments[0].scrollIntoView({behavior:'auto',block:'center'});", elemento
        )
        elemento.click()

    def scroll_a_elemento(self, elemento):
        self.sb.execute_script(
            "arguments[0].scrollIntoView({behavior:'auto',block:'center'});", elemento
        )

    # -----------------------------------------------------------------------
    # GUARDADO / MENSAJES DE EXITO
    # -----------------------------------------------------------------------

    def esperar_exito(self, texto="Proceso guardado con éxito", timeout=SAVE_TIMEOUT):
        self.sb.wait_for_text(texto, "html", timeout=timeout)

    # -----------------------------------------------------------------------
    # JAVASCRIPT
    # -----------------------------------------------------------------------

    def ejecutar_js(self, script, *args):
        return self.sb.execute_script(script, *args)

    # -----------------------------------------------------------------------
    # WRAPPERS find_element (compatibilidad con page objects en migracion)
    # -----------------------------------------------------------------------

    def find_element(self, by, value):
        return self.driver.find_element(by, value)

    def find_elements(self, by, value):
        return self.driver.find_elements(by, value)
