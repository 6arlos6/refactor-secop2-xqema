from seleniumbase import BaseCase
from pages.base_page import BasePage
from utils.logger import log_step as print

class FileReportedPage(BasePage):
    
    def __init__(self, sb: BaseCase):
        super().__init__(sb)

    # =========================================================================
    #  1. SELECTORES DE FORMULARIO Y METADATOS
    # =========================================================================
    TITULO_MODULO = "//p[contains(normalize-space(), 'File reported') or contains(normalize-space(), 'VINCULAR ANEXOS / NUEVO CONTRATO')]"

    INPUT_CONTRATO_NO = "//label[contains(., 'Contrato No.')]/following-sibling::div//input"
    BTN_CONSULTAR_CONTRATO = "//button[contains(., 'Consultar')]"
    BTN_CONTINUAR_CONTRATO = "//button[contains(., 'Continuar')]"

    INPUT_FILE_HIDDEN = "//input[@type='file']"
    
    COMBOBOX_LEGALIDAD = "//label[contains(., 'Documento de Legalidad')]/following-sibling::div//div[@role='combobox']"
    OPCION_LEGALIDAD = "//li[@role='option' and contains(., '{0}')]"
    
    INPUT_PAGINA = "//label[contains(., 'Página')]/following-sibling::div//input"
    BTN_VINCULAR_ARCHIVO = "//button[contains(., 'Vincular Archivo') and contains(@class, 'MuiButton-containedPrimary')]"

    MSG_EXITO_ANEXO = "//p[contains(text(), 'Se ha vinculado el anexo al contrato exitosamente')]"
    BTN_ACEPTAR_MODAL = "//button[contains(., 'Aceptar')]"

    # =========================================================================
    #  MÉTODOS
    # =========================================================================

    def navegar_a_cargue_registros(self):
        """
        Navega al módulo de vinculación de CDP al contrato asegurando que la página cargue por completo.
        """
        self.navegar_y_esperar_carga(
            nombre_modulo="Vinculación de anexos",
            selector_principal=self.TITULO_MODULO,
            nombre_submenu="Vincular Anexos"
        )

    def consultar_contrato(self, num_contrato):
        """Busca el contrato para comenzar a realizar el anexado de archivos"""
        print(f"🔍 Consultando contrato No. {num_contrato} para vincular anexos...")
        
        self.sb.wait_for_element_visible(self.INPUT_CONTRATO_NO)
        self.sb.clear(self.INPUT_CONTRATO_NO)
        self.sb.type(self.INPUT_CONTRATO_NO, num_contrato)
        
        self.sb.click(self.BTN_CONSULTAR_CONTRATO)
        
        try:
            self.sb.wait_for_element_visible(self.BTN_CONTINUAR_CONTRATO, timeout=10)
            self.sb.click(self.BTN_CONTINUAR_CONTRATO)
            return True
        except Exception:
            print(f"❌ El contrato {num_contrato} no habilitó el botón Continuar.")
            return False
        
    def anexar_documento(self, ruta_archivo, tipologia_destino):
        """Adjunta el archivo físico y lo vincula con la tipología."""

        # Eliminación de Toast que obstruyen el funcionamiento
        self.sb.execute_script("document.querySelectorAll('div[role=\"status\"]').forEach(e => e.remove());")

        if self.sb.is_element_visible(self.LOADING_BACKDROP):
            self.sb.wait_for_element_not_visible(self.LOADING_BACKDROP, timeout=15)

        # ==========================================
        # 1. CARGA DEL ARCHIVO (Bypass de ventana OS)
        # ==========================================
        print(f"📁 Adjuntando archivo de forma directa: {ruta_archivo}")
        self.sb.wait_for_element_present(self.INPUT_FILE_HIDDEN, timeout=5)
        self.sb.choose_file(self.INPUT_FILE_HIDDEN, ruta_archivo)
        
        # ==========================================
        # 2. HOMOLOGACIÓN DE TIPOLOGÍA Y PÁGINA
        # ==========================================
        print(f"🏷️ Seleccionando tipología: {tipologia_destino}")
        self.sb.click(self.COMBOBOX_LEGALIDAD)
        xpath_opcion = self.OPCION_LEGALIDAD.format(tipologia_destino)
        self.sb.wait_for_element_visible(xpath_opcion, timeout=5)
        self.sb.click(xpath_opcion)

        self.sb.sleep(0.4)

        elemento_input = self.sb.find_element(self.INPUT_PAGINA)
        self.sb.execute_script("arguments[0].click();", elemento_input)
        self.sb.press_keys(self.INPUT_PAGINA, "^a")
        self.sb.type(self.INPUT_PAGINA, "1")
        self.sb.click(self.TITULO_MODULO)
        self.sb.sleep(0.3)

        # ==========================================
        # 3. CONFIRMACIÓN
        # ==========================================
        try:
            print("🔘 Vinculando Archivo...")
            self.sb.wait_for_element_clickable(self.BTN_VINCULAR_ARCHIVO, timeout=5)
            boton_vincular = self.sb.find_element(self.BTN_VINCULAR_ARCHIVO)
            self.sb.execute_script("arguments[0].click();", boton_vincular)

            print("⏳ Esperando diálogo de éxito...")
            self.sb.wait_for_element_visible(self.MSG_EXITO_ANEXO, timeout=30)
            
            self.sb.wait_for_element_clickable(self.BTN_ACEPTAR_MODAL)
            self.sb.click(self.BTN_ACEPTAR_MODAL)
            
            print("✅ Documento anexado exitosamente.")
            return True
            
        except Exception as e:
            print(f"❌ Error al vincular el anexo: {e}")
            return False