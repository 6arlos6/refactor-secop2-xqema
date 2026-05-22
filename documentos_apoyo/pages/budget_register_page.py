from seleniumbase import BaseCase
from pages.base_page import BasePage
from utils.logger import log_step as print

class BudgetRegisterPage(BasePage):
    def __init__(self, sb: BaseCase):
        self.sb = sb

    # =========================================================================
    #  1. NAVEGACIÓN Y METADATOS DEL MÓDULO
    # =========================================================================
    TITULO_MODULO_RP = "//p[contains(text(), 'RETIRAR REGISTRO PRESUPUESTAL') or contains(text(), 'Budget register')]"

    # =========================================================================
    #  2. FORMULARIO BÚSQUEDA DE CONTRATO
    # =========================================================================
    INPUT_CONTRATO_NO = "//label[contains(., 'Contrato No.')]/following-sibling::div//input"
    BTN_CONSULTAR_CONTRATO = "//button[contains(., 'Consultar')]"
    BTN_CONTINUAR_CONTRATO = "//button[contains(., 'Continuar')]"
    
    # =========================================================================
    #  3. FORMULARIO DE REGISTRO PRESUPUESTAL (RP)
    # =========================================================================
    INPUT_NUM_RP = "//label[contains(., 'No. Registro Presupuestal')]/following-sibling::div//input"
    INPUT_FECHA_RP = "//label[contains(., 'Fecha Registro Presupuestal')]/following-sibling::div//input"
    
    # Combobox de Disponibilidad (CDP) y su lista de opciones
    COMBOBOX_DISPONIBILIDAD = "//label[contains(., 'Disponibilidad Presupuestal')]/following-sibling::div//div[@role='combobox']"
    OPCION_DISPONIBILIDAD = "//li[@role='option' and contains(., '{0}') and contains(., '{1}')]"
    
    INPUT_TOTAL_BRUTO = "//label[contains(., 'Total Bruto')]/following-sibling::div//input"
    BTN_VALIDAR_RP = "//button[contains(., 'Validar') and contains(@class, 'MuiButton-containedPrimary')]"
    BTN_VINCULAR_RP = "//button[contains(., 'Vincular')]"

    # =========================================================================
    #  4. DIÁLOGO DE CONFIRMACIÓN (MODAL)
    # =========================================================================
    MSG_EXITO_VINCULACION_RP = "//p[contains(text(), 'Se ha vinculado el registro presupuestal al contrato exitosamente')]"
    BTN_ACEPTAR_MODAL = "//button[contains(., 'Aceptar')]"

    # =========================================================================
    #  5. TABLA DE RPs YA VINCULADOS
    # =========================================================================
    FILA_RP_VALIDADA = (
        "//div[@role='row' and "
        ".//div[@data-field='BUDGET_REGISTER_IDENTIFIER' and @title='{0}'] and "
        ".//div[@data-field='BUDGET_AVAILABILITY_IDENTIFIER' and @title='{1}'] and "
        ".//div[@data-field='BUDGET_AVAILABILITY_DIVISION' and @title='{2}']"
        "]"
    )
    CONTENEDOR_TABLA_RP = "//div[contains(@class, 'MuiDataGrid-main')]"

    # =========================================================================
    #  MÉTODOS DE ACCIÓN
    # =========================================================================
    def navegar_a_vincular_rp(self):
        """
        Navega al módulo de vinculación de CDP al contrato asegurando que la página cargue por completo.
        """
        self.navegar_y_esperar_carga(
            nombre_modulo="Vinculación de RP",
            selector_principal=self.TITULO_MODULO_RP,
            nombre_submenu="Vincular Registro"
        )

    def verificar_rp_vinculado(self, num_rp, cdp_asociado, rubro):
        """
        Verifica si el RP ya aparece en la grilla de registros vinculados.
        """
        print(f"🧐 Verificando en tabla si el RP '{num_rp}' con CDP '{cdp_asociado}' y Rubro '{rubro}' ya existe...")

        if not self.sb.is_element_visible(self.CONTENEDOR_TABLA_RP):
            print("ℹ️ No hay tabla visible. Este será el primer RP del contrato.")
            return False
        
        xpath_rp = self.FILA_RP_VALIDADA.format(num_rp, cdp_asociado, rubro)
        
        if self.sb.is_element_visible(xpath_rp):
            print(f"ℹ️ El RP {num_rp} con CDP {cdp_asociado} y Rubro {rubro} YA ESTÁ VINCULADO. Se omite el llenado.")
            return True
        
        print("✔️ El RP es nuevo para este contrato. Procediendo a registrarlo...")
        return False
    
    def vincular_registro_presupuestal(self, num_contrato, num_rp, fecha_rp, cdp_asociado, total_bruto, rubro):
        """
        Ejecuta el flujo completo para registrar un RP a un contrato.
        """
        print(f"🔍 Consultando contrato No. {num_contrato} para RP {num_rp}...")
        
        # 1. Buscar Contrato
        self.sb.wait_for_element_visible(self.INPUT_CONTRATO_NO)
        self.sb.clear(self.INPUT_CONTRATO_NO)
        self.sb.type(self.INPUT_CONTRATO_NO, num_contrato)
        
        self.sb.wait_for_element_clickable(self.BTN_CONSULTAR_CONTRATO)
        self.sb.click(self.BTN_CONSULTAR_CONTRATO)
        
        try:
            self.sb.wait_for_element_visible(self.BTN_CONTINUAR_CONTRATO, timeout=10)
            self.sb.click(self.BTN_CONTINUAR_CONTRATO)
        except Exception:
            print(f"❌ El contrato {num_contrato} no existe o no habilitó el botón Continuar.")
            return False
        
        print("⏳ Esperando que se renderice el formulario...")
        self.sb.wait_for_element_visible(self.INPUT_NUM_RP, timeout=5)

        if self.verificar_rp_vinculado(num_rp, cdp_asociado, rubro):
            return True
        
        print("📝 Diligenciando formulario del Registro Presupuestal...")
        
        # 2. Llenar Número de RP
        self.sb.wait_for_element_visible(self.INPUT_NUM_RP)
        self.sb.click(self.INPUT_NUM_RP)
        self.sb.press_keys(self.INPUT_NUM_RP, "^a")
        self.sb.type(self.INPUT_NUM_RP, num_rp)

        # 3. Llenar Fecha (Los campos de fecha de MUI suelen requerir este truco para no romper el formato)
        print(f"📝 Ingresando la fecha {fecha_rp} para el Registro Presupuestal...")

        self.sb.click(self.INPUT_FECHA_RP)
        self.sb.press_keys(self.INPUT_FECHA_RP, "^a")
        elemento_input = self.sb.wait_for_element(self.INPUT_FECHA_RP)

        script_react = """
            var input = arguments[0];
            var valor = arguments[1];
            
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            nativeInputValueSetter.call(input, valor);
            
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));
        """
        self.sb.execute_script(script_react, elemento_input, fecha_rp)
        
        # 4. Seleccionar Disponibilidad Presupuestal (Combobox)
        # Hacemos clic en el desplegable para abrir la lista
        self.sb.click(self.COMBOBOX_DISPONIBILIDAD)
        # Buscamos la opción dinámica y le damos clic
        xpath_opcion = self.OPCION_DISPONIBILIDAD.format(cdp_asociado, rubro)
        self.sb.wait_for_element_visible(xpath_opcion, timeout=5)
        self.sb.click(xpath_opcion)

        # 5. Llenar Total Bruto
        self.sb.click(self.INPUT_TOTAL_BRUTO)
        self.sb.press_keys(self.INPUT_TOTAL_BRUTO, "^a")
        self.sb.type(self.INPUT_TOTAL_BRUTO, total_bruto)
        

        # 7. Intento de vinculación
        try:
            print("🔘 Enviando formulario de vinculación...")
            self.sb.wait_for_element_clickable(self.BTN_VALIDAR_RP)
            self.sb.click(self.BTN_VALIDAR_RP)
            self.sb.wait_for_element_clickable(self.BTN_VINCULAR_RP)
            self.sb.click(self.BTN_VINCULAR_RP)
            print("⏳ Esperando diálogo de confirmación de éxito...")
            self.sb.wait_for_element_visible(self.MSG_EXITO_VINCULACION_RP, timeout=15)
            
            # Es buena práctica cerrar el modal haciendo clic en Aceptar
            self.sb.wait_for_element_clickable(self.BTN_ACEPTAR_MODAL)
            self.sb.click(self.BTN_ACEPTAR_MODAL)
            
            print("✅ Registro Presupuestal vinculado exitosamente.")
            return True
        except Exception as e:
            print(f"❌ Error crítico: No se mostró el mensaje de éxito del RP. Detalle: {e}")
            return False