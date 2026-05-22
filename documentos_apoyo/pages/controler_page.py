from seleniumbase import BaseCase
from pages.base_page import BasePage
from utils.logger import log_step as print

class ControlerPage(BasePage):
    def __init__(self, sb: BaseCase):
        self.sb = sb

    # --- SELECTORES PRINCIPALES ---
    LABEL_SUBTITULO_PAGINA = "//p[contains(normalize-space(), 'CONTRATO / INICIO') or contains(normalize-space(), 'VINCULAR INTERVENTOR/SUPERVISOR / NUEVO CONTRATO')]"

    # --- SELECTORES DEL FORMULARIO DE BÚSQUEDA ---
    
    # Botón con el icono de lupa
    BTN_ICONO_BUSCAR_CONTRATO = "button[aria-label='buscar contrato']"
    
    # Botón principal de consultar
    BTN_CONSULTAR = "//button[contains(., 'Consultar')]"

    # Botón Continuar
    BTN_CONTINUAR = "//button[contains(., 'Continuar')]"

    # --- SELECTORES BÚSQUEDA INTERVENTOR ---
    BTN_ABRIR_BUSCAR_INTERVENTOR = "button[aria-label='buscar interventor / supervisor']"
    
    # Modal de Interventores
    RADIO_PERSONA_INTERVENTOR = "input[name='controlerNature'][value='PERSON']"
    INPUT_ID_INTERVENTOR_MODAL = "input[name='idNumber']"
    BTN_BUSCAR_INTERVENTOR_MODAL = "//div[contains(@role, 'dialog')]//button[contains(., 'Buscar')]"
    
    # Tabla de resultados (Match exacto por la columna ID)
    BTN_SELECCIONAR_INTERVENTOR_ROW = "//div[@role='row' and div[@data-field='ID' and text()='{0}']]//button[@title='Seleccionar']"

    # --- SELECTORES FORMULARIO Y VINCULACIÓN ---
    DIV_CLICK_TIPO_INTERVENTOR = "//input[@name='controler.0.type']/preceding-sibling::div[contains(@class, 'MuiSelect-select')]"
    
    # Botones de acción principales (Aseguramos no tocar botones dentro de modales)
    BTN_VALIDAR_INTERVENTOR = "(//button[contains(., 'Validar') and not(ancestor::div[@role='dialog'])])[last()]"
    BTN_VINCULAR_INTERVENTOR = "(//button[contains(., 'Vincular') and not(ancestor::div[@role='dialog'])])[last()]"
    
    # Modal de Éxito
    MSG_EXITO_VINCULACION = "//p[contains(text(), 'Se ha vinculado el interventor exitosamente')]"
    BTN_ACEPTAR_EXITO = "//div[@role='dialog']//button[contains(., 'Aceptar')]"

    def navegar_a_vincular_interventor(self):
        self.navegar_y_esperar_carga(
            nombre_modulo="Interventoría",
            selector_principal=self.LABEL_SUBTITULO_PAGINA,
            nombre_submenu="Vincular Interventor / Supervisor"
        )

    def consultar_y_continuar_contrato(self, numero_contrato):
        """
        Ingresa el número de contrato, consulta y, si lo encuentra, 
        hace clic en Continuar para desplegar el formulario.
        """
        print(f"🔍 Consultando contrato No. {numero_contrato}...")
        
        self.sb.wait_for_element_visible(self.INPUT_CONTRATO_NO)
        self.sb.clear(self.INPUT_CONTRATO_NO)
        self.sb.type(self.INPUT_CONTRATO_NO, numero_contrato)
        
        self.sb.wait_for_element_clickable(self.BTN_CONSULTAR)
        self.sb.click(self.BTN_CONSULTAR)

        try:
            print("⏳ Esperando confirmación de búsqueda...")
            # 1. Esperamos que el botón aparezca
            self.sb.wait_for_element_visible(self.BTN_CONTINUAR, timeout=10)
            print("✅ Contrato encontrado exitosamente.")
            
            # 2. Hacemos clic para avanzar
            print("➡️ Haciendo clic en Continuar para desplegar el formulario...")
            self.sb.click(self.BTN_CONTINUAR)
            
            return True
            
        except Exception as e:
            print(f"❌ El contrato {numero_contrato} no existe, o falló al continuar. Error: {e}")
            return False
        
    def asociar_y_vincular_interventor(self, identificacion, tipo_interventor="Interno"):
        """
        Abre el modal, busca al interventor por ID, lo selecciona, 
        llena el tipo y confirma la vinculación.
        """
        print(f"\n👨‍💼 Iniciando vinculación de Interventor (ID: {identificacion})...")

        # 1. Abrir modal de búsqueda
        self.sb.wait_for_element_clickable(self.BTN_ABRIR_BUSCAR_INTERVENTOR)
        self.sb.click(self.BTN_ABRIR_BUSCAR_INTERVENTOR)
        self.sb.wait_for_element_visible("//div[contains(@role, 'dialog')]")

        # 2. Llenar campo de identificación y buscar
        print("🔍 Buscando interventor en el sistema...")
        self.sb.js_click(self.RADIO_PERSONA_INTERVENTOR)
        self.sb.wait_for_element_visible(self.INPUT_ID_INTERVENTOR_MODAL)
        self.sb.clear(self.INPUT_ID_INTERVENTOR_MODAL)
        self.sb.type(self.INPUT_ID_INTERVENTOR_MODAL, identificacion)
        
        self.sb.click(self.BTN_BUSCAR_INTERVENTOR_MODAL)

        # 3. Seleccionar de la tabla
        xpath_seleccionar = self.BTN_SELECCIONAR_INTERVENTOR_ROW.format(identificacion)

        try:
            self.sb.wait_for_element_visible(xpath_seleccionar, timeout=10)
            print("✅ Interventor encontrado. Seleccionando un solo clic...")
        except Exception as e:
            print(f"❌ El interventor {identificacion} no se encontró tabla de resultados.")
            raise e
        
        try:
            self.sb.double_click(xpath_seleccionar)
            self.sb.wait_for_element_not_visible("//div[contains(@role, 'dialog')]", timeout=5)
        except Exception as e:
            print(f"❌ No se completó la selección del interventor {identificacion}.")
            raise e

        # 4. Seleccionar el Tipo
        print(f"🏷️ Asignando tipo de interventor: {tipo_interventor}...")
        self._seleccionar_opcion_mui_select(self.DIV_CLICK_TIPO_INTERVENTOR, tipo_interventor)

        # 5. Validar
        print("💾 Validando datos de vinculación de interventor...")
        self.sb.wait_for_element_clickable(self.BTN_VALIDAR_INTERVENTOR)
        self.sb.click(self.BTN_VALIDAR_INTERVENTOR)

        # 6. Vincular
        print("🚀 Confirmando vinculación final del interventor...")
        self.sb.wait_for_element_clickable(self.BTN_VINCULAR_INTERVENTOR, timeout=10)
        self.sb.click(self.BTN_VINCULAR_INTERVENTOR)

        # 7. Confirmar Éxito
        print("⏳ Esperando la confirmación de éxito del sistema...")
        self.sb.wait_for_element_visible(self.MSG_EXITO_VINCULACION, timeout=15)
        print("✅Mensaje de éxito detectado.")
        
        self.sb.click(self.BTN_ACEPTAR_EXITO)
        self.sb.wait_for_element_not_visible("//div[contains(@role, 'dialog')]", timeout=10)
        
        print("✅ Interventor vinculado correctamente.")
        return True