# -*- coding: utf-8 -*-
"""
Page Object: Login en SECOP II
Extraido de: proyecto-original-secob/funciones.py lineas 52-71 (loguearse_secop)

Migracion SeleniumBase (18/04/2026):
  - self.driver.get()         → self.navegar_a()   (sb.open con retry)
  - self._wait().until(...)   → self.esperar_url_contiene()  (sb.wait_for_url_to_contain)
  - No WebDriverWait explícito, no time.sleep
"""
from seleniumbase import Driver
from pages.base_page import BasePage, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.execution_context import ExecutionContext
from utils.logger import log_step as print
from config.settings import URL_LOGIN_SECOP, USUARIO_SECOP, PASS_SECOP


class LoginPage(BasePage):
    """Gestiona la autenticacion en la plataforma SECOP II."""

    def __init__(self, sb: Driver):
        self.sb = sb

    # === SELECTORES ===
    INPUT_USUARIO  = "txtUserName"
    INPUT_PASSWORD = "txtPassword"
    BTN_LOGIN      = "btnLoginButton"

    # Fragmento de URL presente tras login exitoso en SECOP II
    URL_FRAGMENT_POST_LOGIN = "CO1Marketplace"

    def iniciar_sesion(self):
        """
        Realiza el login en SECOP II.
        Original: funciones.py:52-70 — loguearse_secop(driver)

        SeleniumBase gestiona las esperas internamente:
          - sb.type()   espera que el campo sea clickeable antes de escribir
          - sb.click()  espera que el boton sea clickeable con retry automatico
          - sb.wait_for_url_to_contain() reemplaza WebDriverWait + lambda
        """
        print("Iniciando sesion en SECOP II...")
        self.navegar_a(URL_LOGIN_SECOP)

        # Escribir usuario y contrasena (sb.type incluye espera + clear + type)
        self.esperar_y_escribir_por_id(self.INPUT_USUARIO,  USUARIO_SECOP, timeout=LONG_TIMEOUT)
        self.esperar_y_escribir_por_id(self.INPUT_PASSWORD, PASS_SECOP)

        # Click en boton login (sb.click espera clickeable con retry)
        self.esperar_y_click_por_id(self.BTN_LOGIN)

        # Esperar redireccion post-login.
        # SECOP II tarda entre 5-40 s segun carga del servidor y modo headless/visible.
        # SAVE_TIMEOUT (40 s) da margen suficiente sin esperar indefinidamente.
        self.esperar_url_contiene(self.URL_FRAGMENT_POST_LOGIN, timeout=SAVE_TIMEOUT)

        ExecutionContext.set_logged_in(True)
        print(f"Sesion iniciada correctamente — URL: {self.url_actual}")

    def verificar_o_iniciar_sesion(self):
        """Solo inicia sesion si no esta logueado (patron state-valve)."""
        if not ExecutionContext.is_logged_in():
            try:
                self.iniciar_sesion()
            except Exception as e:
                print(f"Error en login (se reintentara en el siguiente ciclo): {e}")
