from seleniumbase import BaseCase
from config.settings import URL_DASHBOARD
from utils.logger import log_step as print

class BasePage:

    # Selectores globales
    LOADING_BACKDROP = "//div[contains(@class, 'MuiBackdrop-root')]"
    INPUT_CONTRATO_NO = "//label[contains(., 'Contrato No.')]/following-sibling::div//input"
    
    def __init__(self, sb: BaseCase):
        self.sb = sb
    # =========================================================================
    #  HELPERS GLOBALES DE MATERIAL UI
    # =========================================================================

    def _seleccionar_opcion_mui_select(self, selector_div_click, texto_opcion):
        """Helper exclusivo para MUI Selects (donde no se puede teclear)"""
        print(f"      [BasePage] Seleccionando en menú clásico: '{texto_opcion}'...")
        self.sb.wait_for_element_clickable(selector_div_click)
        self.sb.click(selector_div_click)
        
        selector_li = f"//li[@role='option' and contains(., '{texto_opcion}')]"
        self.sb.wait_for_element_visible(selector_li, timeout=5)
        self.sb.click(selector_li)

    def _llenar_mui_autocomplete(self, selector_input, texto_buscar):
        """Helper para Autocompletes de Material UI (escribibles) con patrón Fail-Fast"""
        print(f"      [BasePage] Seleccionando '{texto_buscar}'...")
        self.sb.wait_for_element_clickable(selector_input)
        self.sb.clear(selector_input)
        self.sb.type(selector_input, texto_buscar)
        
        selector_opcion_exacta = f"//li[@role='option' and contains(., '{texto_buscar}')]"
        
        try:
            self.sb.wait_for_element_visible(selector_opcion_exacta, timeout=5)
            self.sb.click(selector_opcion_exacta)
            print("✅ Match exacto seleccionado.")
            
        except Exception:
            print(f"⚠️ Opción exacta no encontrada. Confiando en el filtro del sistema...")
            selector_cualquier_opcion = "//li[@role='option']"
            
            try:
                self.sb.wait_for_element_visible(selector_cualquier_opcion, timeout=3)
                self.sb.click(f"{selector_cualquier_opcion}[1]")
                print("✅ Se seleccionó el primer resultado sugerido.")
                
            except Exception:
                mensaje_error = f"El buscador no arrojó ninguna opción válida para el valor: '{texto_buscar}'."
                print(f"❌ {mensaje_error}")
                
                raise ValueError(mensaje_error)

    def _seleccionar_primera_opcion_mui(self, selector_input):
        """Selecciona la primera opción usando flecha abajo + enter"""
        self.sb.wait_for_element_clickable(selector_input)
        self.sb.click(selector_input)
        self.sb.sleep(0.5) 
        self.sb.press_keys(selector_input, "\ue015\ue007")

    def _calcular_dv(self, nit):
        """Cálculo del Dígito de Verificación (Útil para todo el sistema)"""
        nit_limpio = "".join(filter(str.isdigit, str(nit)))
        if not nit_limpio:
            raise ValueError(f"El NIT '{nit}' no contiene números válidos.")
        primos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        suma = sum(int(n) * primos[i] for i, n in enumerate(reversed(nit_limpio)) if i < len(primos))
        resto = suma % 11
        return 11 - resto if resto > 1 else resto

    def _extraer_nombres(self, nombre_completo):
        partes = nombre_completo.split()
        if len(partes) < 2:
            return partes[0], "", ""
        
        nom = partes[0]
        ape1 = partes[1]
        ape2 = " ".join(partes[2:]) if len(partes) > 2 else ""
        return nom, ape1, ape2

    def navegar_y_esperar_carga(self, nombre_modulo, selector_principal, nombre_submenu=None, url_modulo = None):
        """
        Navega a un módulo, espera que desaparezca la carga y valida un elemento clave.
        Si se provee 'nombre_submenu', navega haciendo clics en la interfaz en lugar de usar la URL.
        """
        self.sb.sleep(1)
        self.sb.set_window_size(1920, 1080)
        print(f"🚀 Navegando a {nombre_modulo}...")
        
        if nombre_submenu:
            # --- NAVEGACIÓN INTELIGENTE POR MENÚ ---
            self.sb.open(URL_DASHBOARD)
            
            xpath_contratacion = "//span[text()='Contratación']"
            xpath_ingresar = "//span[text()='Ingresar Contrato']"
            xpath_final = f"//span[contains(text(), '{nombre_submenu}')]"

            if not self.sb.is_element_visible(xpath_final):
                if not self.sb.is_element_visible(xpath_ingresar):
                    print("📂 Abriendo menú Contratación...")
                    try:
                        self.sb.wait_for_element_clickable(xpath_contratacion, timeout=6)
                        self.sb.click(xpath_contratacion)
                    except Exception:
                        print("⚠️ Menú oculto o tapado. Forzando apertura con JS...")
                        self.sb.js_click(xpath_contratacion)

                    self.sb.wait_for_element_visible(xpath_ingresar, timeout=5)
                
                self.sb.click(xpath_ingresar)
                self.sb.wait_for_element_visible(xpath_final, timeout=5)

            self.sb.click(xpath_final)
            
        elif url_modulo:
            self.sb.open(url_modulo)
        else:
            print("❌ Sin parámetros para realizar la navegación")
            return
        
        print(f"⏳ Esperando que el módulo de {nombre_modulo} esté interactuable...")
        
        if self.sb.is_element_visible(self.LOADING_BACKDROP):
            self.sb.wait_for_element_not_visible(self.LOADING_BACKDROP, timeout=30)

        self.sb.sleep(1)
        
        self.sb.wait_for_element_visible(selector_principal, timeout=15)
        print(f"✅ Módulo de {nombre_modulo} cargado correctamente.")