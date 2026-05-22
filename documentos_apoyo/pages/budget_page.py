from seleniumbase import BaseCase
from config.settings import PLAN_GOBIERNO, ANIO_ACTUAL, URL_MODULO_CDP
from pages.base_page import BasePage
from utils.logger import log_step as print

class BudgetPage(BasePage):
    def __init__(self, sb:BaseCase):
        self.sb = sb
    
    # Metadatos módulo disponibilidades
    TITULO_MODULO = "//h5[text()='Registro y Edición de Disponibilidades Presupuestales']"
    SEL_TRIGGER_PLAN = "//label[text()='Plan de Gobierno - Plan de Desarrollo']/following-sibling::div//div[@role='combobox']"
    SEL_TRIGGER_ANIO = "//label[text()='Año']/following-sibling::div//div[@role='combobox']"
    BTN_CARGAR = "//button[contains(text(), 'Cargar')]"
    OPCION_LISTA = "//li[@role='option' and contains(text(), '{0}')]"
    HEADER_CODIGO = "//div[contains(@class, 'MuiDataGrid-columnHeaderTitle') and text()='Código']"
    INPUT_BUSQUEDA = "#search"
    CELDA_CODIGO_TEMPLATE = "//div[@data-field='BUDGET_AVAILABILITY_IDENTIFIER' and text()='{0}']"
    MSG_SIN_RESULTADOS = "//div[contains(text(), 'Sin filas')]"
    BTN_CREAR = "//button[contains(., 'Crear')]"
    HEADER_TABLA_SELECCION = "//div[contains(@class, 'columnHeader') and text()='Código']"
    BTN_SELECCIONAR_ROW = "//div[@role='row' and contains(., '{0}')]//button[contains(., 'Seleccionar')]"
    INPUT_CODIGO_CDP = "//label[contains(., 'Código del CDP')]/following-sibling::div//input"
    INPUT_FECHA_CDP = "//label[contains(., 'Fecha del CDP')]/following-sibling::div//input"
    INPUT_VALOR_CDP = "//label[contains(., 'Valor del CDP')]/following-sibling::div//input"
    BTN_GUARDAR_DISP = "//button[contains(., 'Guardar Disponibilidad')]"
    MSG_EXITO_GUARDADO = "//div[@role='status' and contains(., 'Guardado exitosamente')]"
    BTN_OPCION_EDITAR = "//li[@role='menuitem' and contains(., 'Editar')]"
    BTN_VINCULAR_RUBRO = "//button[contains(., 'Vincular Rubro')]"
    MSG_ERROR_YA_ASOCIADO = "//div[@role='status' and contains(., 'ya se encuentra asociada al Rubro')]"
    MSG_ERROR_PRESUPUESTO = "//div[@role='status' and contains(., 'exceden su apropiación')]"

    def navegar_a_gestion_cdp(self):
        """
        Navega al módulo de Presupuesto / CDP aprovechando 
        el helper universal con autorrecuperación.
        """
        self.navegar_y_esperar_carga(
            url_modulo=URL_MODULO_CDP,
            nombre_modulo="Presupuesto / CDP",
            selector_principal=self.TITULO_MODULO
        )

    def configurar_periodo(self):
        plan_limpio = str(PLAN_GOBIERNO).strip()
        print(f"⚙️ Configurando periodo: Plan '{plan_limpio}' - Año '{ANIO_ACTUAL}'")

        self.sb.wait_for_element_not_visible(self.LOADING_BACKDROP, timeout=30)
        self.sb.sleep(0.5)

        self.sb.wait_for_element_clickable(self.SEL_TRIGGER_PLAN)
        self.sb.sleep(0.5)
        self.sb.click(self.SEL_TRIGGER_PLAN)

        xpath_plan = self.OPCION_LISTA.format(plan_limpio)
        self.sb.wait_for_element_clickable(xpath_plan, timeout=5)

        try:
            self.sb.click(xpath_plan)
        except Exception:
            print("⚠️ Clic físico interceptado. Usando inyección JavaScript...")
            self.sb.js_click(xpath_plan)

        self.sb.sleep(0.5)

        self.sb.click(self.SEL_TRIGGER_ANIO)
        xpath_anio = self.OPCION_LISTA.format(ANIO_ACTUAL)
        self.sb.click(xpath_anio)

        print("🔄 Cargando datos del periodo...")
        self.sb.click(self.BTN_CARGAR)

        print("⏳ Esperando que aparezca la tabla de resultados...")
        self.sb.wait_for_element_visible(self.HEADER_CODIGO, timeout=30)

        self.sb.sleep(0.4)

        if self.sb.is_element_visible("//p[contains(@class, 'displayedRows')]"):
            texto_paginacion = self.sb.get_text("//p[contains(@class, 'displayedRows')]")
            print(f"✅ Tabla cargada exitosamente. Registros encontrados: {texto_paginacion}")
        else:
            print("✅ Tabla cargada (sin información de paginación visible).")
    
    def buscar_cdp(self, numero_cdp):
        print(f"🔎 Buscando CDP: {numero_cdp}")
        self.sb.wait_for_element_visible(self.INPUT_BUSQUEDA)
        self.sb.clear(self.INPUT_BUSQUEDA)
        self.sb.type(self.INPUT_BUSQUEDA, numero_cdp)
        
        self.sb.sleep(2)
        
        xpath_busqueda = self.CELDA_CODIGO_TEMPLATE.format(numero_cdp)

        try:
            self.sb.wait_for_element_visible(xpath_busqueda, timeout=5)
            print(f"✅ El CDP {numero_cdp} YA EXISTE.")
            return True
        except Exception:
            print(f"ℹ️ El CDP {numero_cdp} NO aparece (Timeout de búsqueda).")
            return False

    def iniciar_creacion_cdp(self):
        print("➕ Iniciando creación de nuevo CDP...")
        self.sb.wait_for_element_visible(self.BTN_CREAR)
        self.sb.click(self.BTN_CREAR)
        print("⏳ Esperando tabla de rubros...")
        self.sb.wait_for_element_visible(self.HEADER_TABLA_SELECCION, timeout=10)
        print("✅ Tabla de selección cargada.")
    
    def seleccionar_rubro(self, codigo_rubro):
        print(f"🔎 Buscando rubro para asociar: {codigo_rubro}")
        self.sb.wait_for_element_visible(self.INPUT_BUSQUEDA)
        self.sb.clear(self.INPUT_BUSQUEDA)
        self.sb.type(self.INPUT_BUSQUEDA, codigo_rubro)

        xpath_btn = self.BTN_SELECCIONAR_ROW.format(codigo_rubro)

        try:
            self.sb.wait_for_element_visible(xpath_btn, timeout=10)
            self.sb.click(xpath_btn)
            print(f"✅ Rubro {codigo_rubro} seleccionado correctamente.") 
            return True
        except:
            if self.sb.is_element_visible(self.MSG_SIN_RESULTADOS):
                print(f"⚠️ El rubro {codigo_rubro} no existe (Filtro sin resultados).")
            else:
                print(f"⚠️ El rubro {codigo_rubro} no apareció en el tiempo límite.")
            return False
        
    def llenar_formulario_detalle_cdp(self, codigo_cdp, fecha, valor):
        print(f"📝 Llenando detalle: CDP {codigo_cdp} | Fecha {fecha} | Valor {valor}")
        self.sb.wait_for_element_visible(self.INPUT_CODIGO_CDP)
        self.sb.clear(self.INPUT_CODIGO_CDP)
        self.sb.type(self.INPUT_CODIGO_CDP, codigo_cdp)

        self.sb.clear(self.INPUT_FECHA_CDP)
        self.sb.type(self.INPUT_FECHA_CDP, fecha)

        self.sb.clear(self.INPUT_VALOR_CDP)
        self.sb.type(self.INPUT_VALOR_CDP, valor)

        print("💾 Guardando disponibilidad...")
        self.sb.click(self.BTN_GUARDAR_DISP)

        print("⏳ Esperando confirmación...")

        try:
            self.sb.wait_for_element_visible(self.MSG_EXITO_GUARDADO, timeout=10)
            print("✅ ¡CDP Creado y Guardado Exitosamente!")
            return True
        except Exception:
            print("❌ No apareció el mensaje de 'Guardado exitosamente'. Puede haber un error de validación.")
            return False
        
    def entrar_a_edicion_cdp(self, numero_cdp):
        print(f"📝 Entrando a editar CDP existente: {numero_cdp}")
        xpath_menu = f"//div[@role='row' and contains(., '{numero_cdp}')]//button"

        self.sb.wait_for_element_visible(xpath_menu)
        self.sb.click(xpath_menu)

        self.sb.wait_for_element_visible(self.BTN_OPCION_EDITAR)
        self.sb.click(self.BTN_OPCION_EDITAR)

        print("⏳ Cargando vista de edición...")
        self.sb.wait_for_element_visible(self.HEADER_TABLA_SELECCION, timeout=10)

    def finalizar_vinculacion(self, valor):
        print(f"🔗 Vinculando a rubro con valor de CDP de: {valor}")
        self.sb.wait_for_element_visible(self.INPUT_VALOR_CDP)
        self.sb.click(self.INPUT_VALOR_CDP)
        self.sb.press_keys(self.INPUT_VALOR_CDP, "^a") 
        self.sb.type(self.INPUT_VALOR_CDP, str(valor))

        self.sb.wait_for_element_clickable(self.BTN_VINCULAR_RUBRO)
        self.sb.js_click(self.BTN_VINCULAR_RUBRO)

        print("⏳ Validando respuesta del sistema...")

        SELECTOR_RESPUESTA = (
            f"{self.MSG_EXITO_GUARDADO} | "
            f"{self.MSG_ERROR_YA_ASOCIADO} | "
            f"{self.MSG_ERROR_PRESUPUESTO}"
        )
        
        try:
            elemento = self.sb.wait_for_element_visible(SELECTOR_RESPUESTA, timeout=12)
            texto = elemento.text.lower()
            
            if "exitosamente" in texto:
                print("✅ Éxito: Vínculo creado para el CDP.")
                return True
            elif "ya se encuentra asociada" in texto:
                print("ℹ️ Información: El rubro ya estaba asociado. Se considera exitoso.")
                return True
            elif "exceden su apropiación" in texto:
                print(f"⛔ BLOQUEO DE NEGOCIO: {texto}")
                return False

        except ValueError as ve:
            raise ve
    
        except Exception as e:
            print(f"❌ Error: No se recibió respuesta del sistema. {e}")
            return False
        
        return False