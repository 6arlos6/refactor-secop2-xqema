from seleniumbase import BaseCase
from pages.base_page import BasePage
from utils.logger import log_step as print

class AdditionalDatesPage(BasePage):
    def __init__(self, sb: BaseCase):
        self.sb = sb

    # =========================================================================
    #  1. NAVEGACIÓN Y METADATOS DEL MÓDULO
    # =========================================================================
    TITULO_MODULO_FECHAS = "//p[contains(normalize-space(), 'Additional dates') or contains(normalize-space(), 'VINCULAR FECHAS / NUEVO CONTRATO')]"

    # =========================================================================
    #  2. FORMULARIO BÚSQUEDA DE CONTRATO
    # =========================================================================
    INPUT_CONTRATO_NO = "//label[contains(., 'Contrato No.')]/following-sibling::div//input"
    BTN_CONSULTAR_CONTRATO = "//button[contains(., 'Consultar')]"
    BTN_CONTINUAR_CONTRATO = "//button[contains(., 'Continuar')]"

    # =========================================================================
    #  3. FORMULARIO DE FECHAS ADICIONALES
    # =========================================================================
    INPUT_FECHA_SECOP = "//label[contains(., 'Publicación Secop')]/following-sibling::div//input"
    
    BTN_VALIDAR_FECHAS = "//button[contains(., 'Validar') and contains(@class, 'MuiButton-containedPrimary')]"
    BTN_VINCULAR_FECHAS = "//button[contains(., 'Vincular') and contains(@class, 'MuiButton-containedPrimary')]"

    # =========================================================================
    #  4. DIÁLOGO DE CONFIRMACIÓN (MODAL)
    # =========================================================================
    MSG_EXITO_FECHAS = "//p[contains(text(), 'Se han vinculado las fechas adicionales al contrato exitosamente')]"
    BTN_ACEPTAR_MODAL = "//button[contains(., 'Aceptar')]"
    MSG_FECHA_YA_EXISTE = "//div[@role='status' and contains(., 'ya tiene asociada una Fecha de Publicación')]"

    # =========================================================================
    #  MÉTODOS DE ACCIÓN
    # =========================================================================

    def navegar_a_fechas_adicionales(self):
        """
        Navega al módulo de vinculación de CDP al contrato asegurando que la página cargue por completo.
        """
        self.navegar_y_esperar_carga(
            nombre_modulo="Vinculación de fechas",
            selector_principal=self.TITULO_MODULO_FECHAS,
            nombre_submenu="Reporte de Fechas"
        )

    def vincular_fecha_secop(self, num_contrato, fecha_secop):
        """
        Ejecuta el flujo para buscar el contrato y vincular la fecha de Publicación Secop.
        """
        print(f"🔍 Consultando contrato No. {num_contrato} para fechas adicionales...")
        
        # 1. Buscar Contrato
        self.sb.wait_for_element_visible(self.INPUT_CONTRATO_NO)
        self.sb.clear(self.INPUT_CONTRATO_NO)
        self.sb.type(self.INPUT_CONTRATO_NO, num_contrato)
        
        self.sb.wait_for_element_clickable(self.BTN_CONSULTAR_CONTRATO)
        self.sb.click(self.BTN_CONSULTAR_CONTRATO)
        
        try:
            # Esperamos dinámicamente el botón continuar
            self.sb.wait_for_element_visible(self.BTN_CONTINUAR_CONTRATO, timeout=10)
            self.sb.click(self.BTN_CONTINUAR_CONTRATO)
        except Exception:
            print(f"❌ El contrato {num_contrato} no habilitó el botón Continuar.")
            return False

        # ==========================================
        # DILIGENCIAMIENTO DEL FORMULARIO
        # ==========================================
        print("📝 Diligenciando fecha de Publicación Secop...")
        
        # Esperamos a que el campo de fecha sea visible para confirmar la carga de la vista
        self.sb.wait_for_element_visible(self.INPUT_FECHA_SECOP, timeout=10)
        
        print(f"📝 Ingresando la fecha {fecha_secop} para Publicación en Secop...")

        self.sb.click(self.INPUT_FECHA_SECOP)
        self.sb.press_keys(self.INPUT_FECHA_SECOP, "^a")
        elemento_input = self.sb.wait_for_element(self.INPUT_FECHA_SECOP)

        script_react = """
            var input = arguments[0];
            var valor = arguments[1];
            
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            nativeInputValueSetter.call(input, valor);
            
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));
        """
        self.sb.execute_script(script_react, elemento_input, fecha_secop)

        # ==========================================
        # VINCULACIÓN Y CONFIRMACIÓN
        # ==========================================
        try:
            print("🔘 Validando fecha ingresada...")
            self.sb.wait_for_element_clickable(self.BTN_VALIDAR_FECHAS)
            self.sb.click(self.BTN_VALIDAR_FECHAS)
            
            # 1. EVALUAR EL RESULTADO DE LA VALIDACIÓN
            try:
                self.sb.wait_for_element_visible(self.MSG_FECHA_YA_EXISTE, timeout=5)
                print("ℹ️ Aviso del sistema: El contrato ya tenía esta fecha asociada. Flujo validado.")
                return True
            except Exception:
                print("✔️ Validación exitosa. Procediendo a Vincular...")
                pass
            
            # 2. VINCULAR
            self.sb.wait_for_element_clickable(self.BTN_VINCULAR_FECHAS)
            self.sb.click(self.BTN_VINCULAR_FECHAS)
            
            print("⏳ Esperando diálogo de confirmación de éxito...")
            self.sb.wait_for_element_visible(self.MSG_EXITO_FECHAS, timeout=15)
            
            # 3. CERRAR MODAL
            self.sb.wait_for_element_clickable(self.BTN_ACEPTAR_MODAL)
            self.sb.click(self.BTN_ACEPTAR_MODAL)
            
            print("✅ Fechas adicionales vinculadas exitosamente por primera vez.")
            return True
            
        except Exception as e:
            print(f"❌ Error crítico en el flujo de Fechas Adicionales. Detalle: {e}")
            return False