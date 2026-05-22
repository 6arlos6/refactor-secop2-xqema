from seleniumbase import BaseCase
from config.settings import URL_LOGIN, URL_DASHBOARD
from utils.logger import log_step as print

class LoginPage:

    def __init__(self, sb: BaseCase):
        self.sb = sb

    INPUT_USER = "//label[contains(., 'Nombre de Usuario')]/following-sibling::div//input"
    INPUT_PASS = "#auth-login-v2-password"
    BTN_LOGIN = "button:contains('Ingresar')"
    LOADING_BACKDROP = "//div[contains(@class, 'MuiBackdrop-root')]"
    INDICADOR_EXITO = "//span[contains(text(), 'Contratación')]"

    def verificar_o_iniciar_sesion(self, usuario, password):
        print(f"\n🔍 Verificando estado de la sesión en Gestion Transparente para {usuario}...")
        
        self.sb.open(URL_DASHBOARD)
        
        try:
            self.sb.wait_for_element_visible(self.INDICADOR_EXITO, timeout=3)
            print("✅ La sesión ya estaba activa. Saltando autenticación.")
            return
        except Exception:
            print("🔒 Sesión inactiva o caducada. Procediendo con el Login...")

        # ==========================================
        # FLUJO NORMAL DE LOGIN
        # ==========================================
        self.sb.open(URL_LOGIN)

        self.sb.clear(self.INPUT_USER)
        self.sb.type(self.INPUT_USER, usuario)
        self.sb.clear(self.INPUT_PASS)
        self.sb.type(self.INPUT_PASS, password)

        self.sb.click(self.BTN_LOGIN)

        # 1. ESPERA DINÁMICA DEL LOGIN
        try:
            self.sb.wait_for_element_visible(self.LOADING_BACKDROP, timeout=2)
            print("⏳ Cargador detectado. Esperando que el servidor responda...")
            self.sb.wait_for_element_not_visible(self.LOADING_BACKDROP, timeout=30)
        except Exception:
            print("⚡ Petición instantánea: El cargador no apareció o duró milisegundos.")

        # 2. ESPERA DE TRANSICIÓN AL DASHBOARD
        print("⏳ Esperando transición y carga de la estructura del Dashboard...")
        self.sb.wait_for_element_visible(self.INDICADOR_EXITO, timeout=20)
        print("✅ Redirección exitosa: Dashboard visible.")

        # 3. ESPERA DE RENDERIZADO FINAL
        if self.sb.is_element_visible(self.LOADING_BACKDROP):
            print("⏳ Verificando carga final de widgets del dashboard...")
            self.sb.wait_for_element_not_visible(self.LOADING_BACKDROP, timeout=30)

        print("✅ Dashboard cargado completamente y listo para operar.")

    def cerrar_sesion_si_existe(self):  
        BTN_AVATAR = "//div[contains(@class, 'MuiAvatar-root')]"
        BTN_SALIR = "//li[contains(., 'Salir')]"

        print("Intentando cerrar cesión...")

        try:
            if self.sb.is_element_visible(BTN_AVATAR):
                self.sb.click(BTN_AVATAR)
                self.sb.wait_for_element_visible(BTN_SALIR, timeout=5)
                self.sb.click(BTN_SALIR)
                print("✅ Sesión cerrada.")
            else:
                print("ℹ️ No se encontró el Avatar (probablemente ya cerraste sesión).")

        except Exception as e:
            print(f"⚠️ No se pudo cerrar sesión: {str(e)}")