from seleniumbase import BaseCase
from pages.base_page import BasePage
from datetime import datetime
from utils.logger import log_step as print
from utils.execution_context import ExecutionContext
class ContractPage(BasePage):
    def __init__(self, sb: BaseCase):
        self.sb = sb
    
    # --- SELECTORES PRINCIPALES---- #
    RADIO_TIPO_CONTRATO = "input[name='contractType'][value='1']"
    INPUT_NUMERO_CONTRATO = "input[name='code']"
    BTN_ABRIR_BUSCAR_CONTRATISTA = "button[aria-label='buscar contratista']"
    BTN_ABRIR_BUSCAR_PROYECTO = "button[aria-label='buscar proyecto']"
    LABEL_TIPO_REGISTRO = "//label[contains(., 'Tipo Registro')]"
    LABEL_VISUAL_CONTRATO = "//span[contains(@class, 'MuiTypography') and text()='Contrato']"

    # --- SELECTORES MODAL CONTRATISTA ---
    RADIO_JURIDICA = "input[name='contractorNature'][value='JURIDICA']"
    RADIO_NATURAL  = "input[name='contractorNature'][value='NATURAL']"
    INPUT_BUSCAR_ID_MODAL_CONT = "//div[contains(@role, 'dialog')]//input[contains(@type, 'text') and preceding-sibling::fieldset/legend/span[contains(., 'Identificación')]]"
    INPUT_BUSCAR_GRID_CONTRATISTA = "//div[contains(@role, 'dialog')]//label[contains(., 'Identificación') and not(contains(., 'Tipo'))]/following-sibling::div//input"
    BTN_SELECCIONAR_ROW_CONTRATISTA = "//div[@role='row' and contains(., '{0}')]//button"
    BTN_BUSCAR_MODAL_CONTRATISTA = "//div[contains(@role, 'dialog')]//button[contains(., 'Buscar')]"
    BTN_CANCELAR_MODAL_CONTRATISTA = "//div[contains(@role, 'dialog')]//button[contains(., 'Cancelar')]"

    # --- SELECTORES CREACIÓN CONTRATISTA: ACCIONES ---
    BTN_CREAR_NUEVO_CONTRATISTA = "//div[contains(@role, 'dialog')]//button[contains(., 'Crear Nuevo')]"
    BTN_VALIDAR_CREACION_CONTRATISTA = "//div[contains(@role, 'dialog')]//button[contains(., 'Validar')]"
    BTN_GUARDAR_CREACION_CONTRATISTA = "//div[contains(@role, 'dialog')]//button[contains(., 'Guardar')]"
    
    # --- FORMULARIO CREACIÓN CONTRATISTA: DATOS BÁSICOS (JURÍDICA) ---
    INPUT_TIPO_ID_JURIDICA = "input[id='corpIdType']"
    INPUT_RAZON_SOCIAL_CONTRATISTA = "input[name='legalName']"
    INPUT_NIT_DV_CONTRATISTA = "input[name='corpIdNumber']" # Ojo: Validar si pide el DV separado o junto
    # En el DOM veo que "Identificación" es corpIdNumber. 
    
    # --- FORMULARIO CREACIÓN CONTRATISTA: DATOS BÁSICOS (NATURAL) ---
    INPUT_TIPO_ID_NATURAL = "input[id='idType']"
    INPUT_ID_DV_CONTRATISTA = "input[name='idNumber']"
    INPUT_PRIMER_NOMBRE_CONTRATISTA = "input[name='firstName']"
    INPUT_PRIMER_APELLIDO_CONTRATISTA = "input[name='lastName']"
    INPUT_SEGUNDO_APELLIDO_CONTRATISTA = "input[name='secondLastName']"
    
    # --- FORMULARIO CREACIÓN CONTRATISTA: CONFIGURACIÓN ---
    # Radio 'Otros'
    RADIO_CONFIG_OTROS_CONTRATISTA = "input[name='contractorConfigType'][value='OTROS']" 
    # Autocomplete 'Tipo' (Cuando se selecciona Otros)
    INPUT_AUTO_TIPO_CONFIG_CONTRATISTA = "input[id='contractorType']"

    # --- FORMULARIO CREACIÓN CONTRATISTA: DIRECCIONES ---
    INPUT_DIR_OFICINA_CONTRATISTA = "input[name='addressOfficeLine1']"
    INPUT_AUTO_PAIS_OFICINA_CONTRATISTA = "input[id='addressOfficeCountry']"
    INPUT_AUTO_DEPTO_OFICINA_CONTRATISTA = "input[id='addressOfficeProvince']"
    INPUT_AUTO_CIUDAD_OFICINA_CONTRATISTA = "input[id='addressOfficeCity']"
    
    # Checkbox "Igual a Dirección Oficina"
    CHECK_IGUAL_DIRECCION_CONTRATISTA = "//label[contains(., 'Igual a Dirección Oficina')]//input"

    # --- FORMULARIO CREACIÓN CONTRATISTA: TELÉFONOS ---
    INPUT_TEL_OFICINA_CONTRATISTA = "input[name='phoneOffice']"
    INPUT_AUTO_PAIS_TEL_CONTRATISTA = "input[id='phoneOfficeCountry']"
    INPUT_AUTO_DEPTO_TEL_CONTRATISTA = "input[id='phoneOfficeProvince']"
    INPUT_AUTO_AREA_TEL_CONTRATISTA = "input[id='phoneOfficeCity']"
    
    # --- SELECTORES MODAL PROYECTO ---
    INPUT_CODIGO_PROYECTO_MODAL = "//div[contains(@role, 'dialog')]//input[@name='projectId']"
    INPUT_NOMBRE_PROYECTO_MODAL = "//div[contains(@role, 'dialog')]//input[@name='projectName']"
    BTN_BUSCAR_PROYECTO_MODAL = "//div[contains(@role, 'dialog')]//button[contains(., 'Buscar')]"
    BTN_SELECCIONAR_PROYECTO_ROW = "//div[@role='row' and div[@data-field='PROJECT_IDENTIFIER' and text()='{0}']]//button[@title='Seleccionar']"

    # --- SELECTORES DE INFORMACIÓN GENERAL ---
    BTN_VALIDAR_ENCABEZADO = "//button[contains(., 'Validar') and not(ancestor::div[@role='dialog'])]"
    TOAST_CONTRATO_CREADO = "//div[@role='status' and contains(text(), 'reportado anteriormente')]"

    # Textos y Fechas
    INPUT_OBJETO_CONTRATO = "textarea[name='objectDesc']"
    INPUT_FECHA_SUSCRIPCION = "input[id='signingDate']"
    INPUT_FECHA_INICIO = "input[id='startingDate']"
    INPUT_VALOR_CONTRATO = "input[name='amount']"
    INPUT_PLAZO_ESTIMADO = "input[name='contractTermDays']"
    RADIO_PLAZO_DIAS = "input[name='contractTimeUnit'][value='1']"
    # Autocompletes (Clasificación)
    INPUT_AUTO_MODALIDAD = "input[id='processType']"
    INPUT_AUTO_TIPOLOGIA = "input[id='typology']"
    INPUT_AUTO_TIPO_CONTRATO = "input[id='type']"
    # Moneda Extranjera
    RADIO_MONEDA_SI = "input[name='otherCurrencyFlag'][value='SI']"
    RADIO_MONEDA_NO = "input[name='otherCurrencyFlag'][value='NO']"
    INPUT_OCULTO_TIPO_MONEDA = "input[name='otherCurrency.0.type']"
    DIV_CLICK_TIPO_MONEDA = "//input[@name='otherCurrency.0.type']/preceding-sibling::div[contains(@class, 'MuiSelect-select')]"
    INPUT_VALOR_MONEDA = "//legend[span[text()='Valor']]/ancestor::fieldset/preceding-sibling::input"

    # Presupuesto, Rurbo y Plan de Gobierno
    INPUT_AUTO_PLAN_GOBIERNO = "input[id='budgetDevPlan']"
    INPUT_AUTO_ANIO_RUBRO = "input[id='budgetYear']"
    INPUT_AUTO_RUBRO = "input[id='budgetItem']"
    INPUT_AUTO_SUBSECTOR = "input[id='budgetExpenditureSubSector']"
    BTN_VINCULAR_RUBRO_CONTRATO = "//button[text()='Vincular' and contains(@class, 'MuiButton-containedPrimary')]"
    CELDA_RUBRO_TABLA = "//div[@data-field='BUDGET_ITEM_CODE' and @title='{0}']"

    # SECOP, Lugar de Ejecución y validación
    RADIO_SECOP_SI = "input[name='secopPublication'][value='SI']"
    RADIO_SECOP_NO = "input[name='secopPublication'][value='NO']"
    INPUT_URL_SECOP = "input[name='secopURL']"
    INPUT_AUTO_DEPTO_EJECUCION = "input[id='executionProvince']"
    INPUT_AUTO_MUNI_EJECUCION = "input[id='executionCity']"

    # Validación y guardado de contrato
    BTN_VALIDAR_FORMULARIO_FINAL = "(//button[contains(., 'Validar') and not(ancestor::div[@role='dialog'])])[last()]"
    BTN_GUARDAR_FORMULARIO_FINAL = "(//button[contains(., 'Guardar') and not(ancestor::div[@role='dialog'])])[last()]"
    MSG_EXITO_CREACION = "//p[contains(text(), 'Se ha registrado el contrato exitosamente')]"
    BTN_ACEPTAR_EXITO = "//div[@role='dialog']//button[contains(., 'Aceptar')]"


    def navegar_a_crear_contrato(self):
        """
        Navega al formulario de creación de contratos utilizando 
        la navegación segura de la clase BasePage.
        """
        self.navegar_y_esperar_carga(
            nombre_modulo="Crear Contrato",
            selector_principal=self.LABEL_TIPO_REGISTRO,
            nombre_submenu="Asistente de Contratación"
        )
    
    def llenar_datos_basicos(self, numero_contrato):
        print(f"📝 Llenando datos básicos. Contrato N°: {numero_contrato}")
        self.sb.wait_for_element_visible(self.LABEL_VISUAL_CONTRATO)
        self.sb.js_click(self.RADIO_TIPO_CONTRATO)
        self.sb.type(self.INPUT_NUMERO_CONTRATO, numero_contrato)
    
    def _buscar_y_seleccionar_contratista_en_modal(self, identificacion, es_juridica = True):
        tipo = "Juridica" if es_juridica else "Natural"
        selector_radio = self.RADIO_JURIDICA if es_juridica else self.RADIO_NATURAL

        print(f"🔍 Buscando contratista con ID:{identificacion} como persona {tipo}...")

        self.sb.wait_for_element_present(selector_radio)
        self.sb.js_click(selector_radio)

        self.sb.wait_for_element_visible(self.INPUT_BUSCAR_GRID_CONTRATISTA)
        self.sb.clear(self.INPUT_BUSCAR_GRID_CONTRATISTA)
        self.sb.type(self.INPUT_BUSCAR_GRID_CONTRATISTA, identificacion)

        print("🔍 Click en botón Buscar contratista...")
        self.sb.wait_for_element_clickable(self.BTN_BUSCAR_MODAL_CONTRATISTA)
        self.sb.click(self.BTN_BUSCAR_MODAL_CONTRATISTA)

        xpath_check = self.BTN_SELECCIONAR_ROW_CONTRATISTA.format(identificacion)

        try:
            self.sb.wait_for_element_visible(xpath_check, timeout=10)
            self.sb.double_click(xpath_check)
            print("✅ Registro encontrado y seleccionado...")
            return True
        except Exception:
            return False
        
    def seleccionar_contratista(self, identificacion):
        print(f"👤 Buscando contratista: {identificacion}")

        self.sb.click(self.BTN_ABRIR_BUSCAR_CONTRATISTA)
        self.sb.wait_for_element_visible("//div[contains(@role, 'dialog')]")

        if self._buscar_y_seleccionar_contratista_en_modal(identificacion, es_juridica=True):
            print(f"✅ Contratista encontrado como PJ y seleccionado.")
            return True
            
        print("⚠️ No encontrado como Jurídica. Reseteando formulario para intentar como Natural...")

        self.sb.wait_for_element_clickable(self.BTN_CANCELAR_MODAL_CONTRATISTA)
        self.sb.click(self.BTN_CANCELAR_MODAL_CONTRATISTA)

        if self._buscar_y_seleccionar_contratista_en_modal(identificacion, es_juridica=False):
            print(f"✅ Contratista encontrado como PN y seleccionado.")
            return True
        
        print("❌ Contratista no encontrado ni como PJ ni como PN.")
        return False

    def crear_contratista_nuevo(self, datos):
        """
        :param datos: dict con keys: identificacion, es_juridica, nombre, direccion, departamento, ciudad, telefono.
        """
        print("🆕 Creando NUEVO Contratista...")

        selector_radio = self.RADIO_JURIDICA if datos['es_juridica'] else self.RADIO_NATURAL

        self.sb.wait_for_element_clickable(self.BTN_CREAR_NUEVO_CONTRATISTA)
        self.sb.click(self.BTN_CREAR_NUEVO_CONTRATISTA)
        
        self.sb.wait_for_element_visible(self.INPUT_DIR_OFICINA_CONTRATISTA)
        self.sb.wait_for_element_present(selector_radio)
        self.sb.js_click(selector_radio)
        
        
        if datos['es_juridica']:
            print("🏢 Llenando datos Persona Jurídica...")
            dv_pj = self._calcular_dv(datos['identificacion_juridica'])
            documento_pj_completo = f"{datos['identificacion_juridica']}-{dv_pj}"
            
            print("Ingresando NIT y Razón Social - Persona Jurídica...")
            self._llenar_mui_autocomplete(self.INPUT_TIPO_ID_JURIDICA, datos['tipo_identificacion_juridica'])
            self.sb.type(self.INPUT_NIT_DV_CONTRATISTA, documento_pj_completo)
            self.sb.type(self.INPUT_RAZON_SOCIAL_CONTRATISTA, datos['razon_social'])
            
            self.sb.js_click(self.RADIO_CONFIG_OTROS_CONTRATISTA)
            self._llenar_mui_autocomplete(self.INPUT_AUTO_TIPO_CONFIG_CONTRATISTA, "SAS")
            
        print("👤 Llenando nombres y apellidos contratista o representante...")
        nom, ape1, ape2 = self._extraer_nombres(datos['nombre_cont_o_rep'])
        
        dv_pn = self._calcular_dv(datos['identificacion_natural'])
        documento_pn_completo = f"{datos['identificacion_natural']}-{dv_pn}"
        self._llenar_mui_autocomplete(self.INPUT_TIPO_ID_NATURAL, datos['tipo_identificacion_natural'])
        self.sb.type(self.INPUT_PRIMER_NOMBRE_CONTRATISTA, nom)
        self.sb.type(self.INPUT_PRIMER_APELLIDO_CONTRATISTA, ape1)
        self.sb.type(self.INPUT_SEGUNDO_APELLIDO_CONTRATISTA, ape2)
        self.sb.type(self.INPUT_ID_DV_CONTRATISTA, documento_pn_completo)
            

        print("📍 Llenando dirección...")
        self.sb.type(self.INPUT_DIR_OFICINA_CONTRATISTA, datos['direccion'])
        
        self._llenar_mui_autocomplete(self.INPUT_AUTO_PAIS_OFICINA_CONTRATISTA, "Colombia")
        self._llenar_mui_autocomplete(self.INPUT_AUTO_DEPTO_OFICINA_CONTRATISTA, datos['departamento'])
        self._llenar_mui_autocomplete(self.INPUT_AUTO_CIUDAD_OFICINA_CONTRATISTA, datos['ciudad'])

        self.sb.js_click(self.CHECK_IGUAL_DIRECCION_CONTRATISTA)

        print("📞 Llenando teléfonos...")
        self.sb.type(self.INPUT_TEL_OFICINA_CONTRATISTA, datos['telefono'])
        
        self._llenar_mui_autocomplete(self.INPUT_AUTO_PAIS_TEL_CONTRATISTA, "Colombia")
        self._llenar_mui_autocomplete(self.INPUT_AUTO_DEPTO_TEL_CONTRATISTA, datos['departamento_telefonos'])
        self._seleccionar_primera_opcion_mui(self.INPUT_AUTO_AREA_TEL_CONTRATISTA)

        print("💾 Validando creación...")
        btn_validar = self.sb.find_element(self.BTN_VALIDAR_CREACION_CONTRATISTA)
        self.sb.execute_script("arguments[0].scrollIntoView();", btn_validar)
        
        self.sb.wait_for_element_clickable(self.BTN_VALIDAR_CREACION_CONTRATISTA)
        self.sb.click(self.BTN_VALIDAR_CREACION_CONTRATISTA)

        print("💾 Confirmando y Guardando...")
        self.sb.wait_for_element_clickable(self.BTN_GUARDAR_CREACION_CONTRATISTA)
        self.sb.click(self.BTN_GUARDAR_CREACION_CONTRATISTA)

        self.sb.wait_for_element_not_visible("//div[contains(@role, 'dialog')]", timeout=15)
        print("✅ Contratista creado.")

        return True
    
    def gestionar_contratista(self, datos_completos):
        """
        Coordina la búsqueda y la creación.
        Usa 'seleccionar_contratista' primero. Si retorna False, usa 'crear_contratista_nuevo'.
        """
        identificacion = datos_completos['identificacion']

        encontrado = self.seleccionar_contratista(identificacion)

        if encontrado:
            return True

        pais = datos_completos['pais']

        if pais != 'CO':
            print(f"⚠️ Bloqueo de seguridad: El contratista {identificacion} es extranjero (País: {pais}).")
            print("❌ La creación automática de extranjeros no está permitida.")
            return False
        
        print(f"⚡ Procediendo a crear el contratista {identificacion}...")
        return self.crear_contratista_nuevo(datos_completos)
    
    def seleccionar_proyecto(self, codigo_proyecto):
        """
        Abre el modal, busca por código y selecciona la coincidencia exacta.
        """
        print(f"🏗️  Buscando proyecto con código: {codigo_proyecto}")

        # 1. Abrir Modal
        self.sb.wait_for_element_clickable(self.BTN_ABRIR_BUSCAR_PROYECTO)
        self.sb.click(self.BTN_ABRIR_BUSCAR_PROYECTO)
        self.sb.wait_for_element_visible("//div[contains(@role, 'dialog')]")

        # 2. Llenar el campo de código
        self.sb.wait_for_element_visible(self.INPUT_CODIGO_PROYECTO_MODAL)
        self.sb.clear(self.INPUT_CODIGO_PROYECTO_MODAL)
        self.sb.type(self.INPUT_CODIGO_PROYECTO_MODAL, codigo_proyecto)

        # 3. Clic en Buscar
        print("   🔍 Filtrando resultados...")
        self.sb.wait_for_element_clickable(self.BTN_BUSCAR_PROYECTO_MODAL)
        self.sb.click(self.BTN_BUSCAR_PROYECTO_MODAL)

        # 4. Encontrar y Seleccionar el registro en la tabla
        xpath_seleccionar = self.BTN_SELECCIONAR_PROYECTO_ROW.format(codigo_proyecto)

        try:
            # Esperamos a que la fila exacta aparezca
            self.sb.wait_for_element_visible(xpath_seleccionar, timeout=8)
            print("✅ Proyecto encontrado. Seleccionando...")
            self.sb.double_click(xpath_seleccionar)
            
            # Esperamos a que el modal se cierre confirmando la selección
            self.sb.wait_for_element_not_visible("//div[contains(@role, 'dialog')]", timeout=5)
            return True
            
        except Exception:
            print(f"❌ El proyecto {codigo_proyecto} no se encontró en la tabla.")
            self.sb.press_keys("body", "\ue00c") 
            return False
    
    def verificar_rubro_en_tabla(self, codigo_rubro):
        """
        Verifica si el rubro aparece en la tabla de rubros vinculados del contrato.
        """
        print(f"🧐 Verificando presencia del rubro {codigo_rubro} en la tabla...")
        
        xpath_celda = self.CELDA_RUBRO_TABLA.format(codigo_rubro)
        
        try:
            self.sb.wait_for_element_visible(xpath_celda, timeout=10)
            print(f"✅ Confirmado: El rubro {codigo_rubro} está en la tabla.")
            return True
        except Exception:
            print(f"❌ Error: El rubro {codigo_rubro} no se encontró en la tabla tras vincular.")
            return False
    
    def vincular_rubro_a_contrato(self, codigo_rubro):
        """
        Flujo completo: Diligencia, vincula y verifica en tabla.
        """
        self.sb.click(self.BTN_VINCULAR_RUBRO_CONTRATO)
        
        self.sb.sleep(1) 

        return self.verificar_rubro_en_tabla(codigo_rubro)
    
    def diligenciar_formulario_principal_contrato(self, datos_contrato):
        """
        Llena el formulario grande después de seleccionar Contratista y Proyecto.
        """
        # 1. Validar Encabezado (Para habilitar el resto del formulario)
        self.sb.wait_for_element_clickable(self.BTN_VALIDAR_ENCABEZADO)
        self.sb.click(self.BTN_VALIDAR_ENCABEZADO)
        
        try:
            self.sb.wait_for_element_visible(self.TOAST_CONTRATO_CREADO, timeout=5)
            print(f"❌ El contrato que se trata de crear ya ha sido reportado anteriormente.")
            return False
        except Exception:
            pass
        
        print("\n📝 Diligenciando formulario principal del contrato...")

        # Esperamos a que los campos de texto se habiliten
        self.sb.wait_for_element_visible(self.INPUT_OBJETO_CONTRATO)

        # 2. Textos Básicos
        print("📄 Llenando Objeto y Observaciones...")
        self.sb.type(self.INPUT_OBJETO_CONTRATO, datos_contrato['objeto'])

        # 3. Fechas
        # Se usa Ctrl+A (^a) para limpiar la máscara del react-datepicker antes de escribir
        print("📅 Llenando Fechas...")
        self.sb.press_keys(self.INPUT_FECHA_SUSCRIPCION, "^a") 
        self.sb.type(self.INPUT_FECHA_SUSCRIPCION, datos_contrato['fecha_suscripcion'])
        
        self.sb.press_keys(self.INPUT_FECHA_INICIO, "^a")
        self.sb.type(self.INPUT_FECHA_INICIO, datos_contrato['fecha_inicio'])

        # 4. Valor (Sin puntos ni comas)
        print("💵 Ingresando Valor contrato...")
        self.sb.type(self.INPUT_VALOR_CONTRATO, str(datos_contrato['valor']))

        # 5. Cálculo del Plazo en Días (Fecha Fin - Fecha Inicio + 1)
        f_inicio = datetime.strptime(datos_contrato['fecha_inicio'], "%d/%m/%Y")
        f_fin = datetime.strptime(datos_contrato['fecha_fin'], "%d/%m/%Y")
        plazo_dias = (f_fin - f_inicio).days + 1
        
        print(f"⏱️ Calculado plazo estimado: {plazo_dias} días.")
        self.sb.js_click(self.RADIO_PLAZO_DIAS)
        self.sb.type(self.INPUT_PLAZO_ESTIMADO, str(plazo_dias))

        # 6. Clasificación del Contrato
        print("🏷️ Seleccionando Clasificación del contrato...")
        self._seleccionar_primera_opcion_mui(self.INPUT_AUTO_MODALIDAD)
        self._llenar_mui_autocomplete(self.INPUT_AUTO_TIPOLOGIA, datos_contrato['tipologia'])
        self._llenar_mui_autocomplete(self.INPUT_AUTO_TIPO_CONTRATO, datos_contrato['tipo_contrato'])

        # 7. Moneda Extranjera
        # Mapeamos 'S' a la opción 'SI' que pide tu lógica de negocio
        if datos_contrato.get('moneda_extranjera', 'N').upper() in ['S', 'SI']:
            print("💱 Aplicando Moneda Extranjera...")
            self.sb.js_click(self.RADIO_MONEDA_SI)
            
            # Usamos el helper de <Select> clásico (no autocomplete)
            self._seleccionar_opcion_mui_select(self.DIV_CLICK_TIPO_MONEDA, datos_contrato['tipo_moneda'])
            
            # Limpiamos el valor por defecto ($ 0,00) y escribimos
            self.sb.press_keys(self.INPUT_VALOR_MONEDA, "^a")
            self.sb.type(self.INPUT_VALOR_MONEDA, str(datos_contrato['valor_moneda']))
        else:
            print("💱 Moneda Local (COP).")
            self.sb.js_click(self.RADIO_MONEDA_NO)

        # 8. Presupuesto
        for rubro in datos_contrato['rubros']:
            print(f"🔗 Asociando rubro {rubro['rubro']} al contrato...")
            self._seleccionar_primera_opcion_mui(self.INPUT_AUTO_PLAN_GOBIERNO)
            self._llenar_mui_autocomplete(self.INPUT_AUTO_ANIO_RUBRO, str(rubro['anio_rubro']))
            self._llenar_mui_autocomplete(self.INPUT_AUTO_RUBRO, rubro['rubro'])
            self.sb.sleep(0.4)
            self._llenar_mui_autocomplete(self.INPUT_AUTO_SUBSECTOR, "Fortalecimiento Institucional")
            self.vincular_rubro_a_contrato(rubro['rubro'])

        # 9. SECOP
        if datos_contrato['url_secop']:
            print("🌐 Ingresando enlace de Publicación en SECOP...")
            self.sb.js_click(self.RADIO_SECOP_SI)
            self.sb.type(self.INPUT_URL_SECOP, datos_contrato['url_secop'])
        else:
            print("⚠️ Sin enlace de Publicación en SECOP...")
            ExecutionContext.add_warning("⚠️ No se rinde con enlace de SECOP")
            self.sb.js_click(self.RADIO_SECOP_NO)

        # 10. Ejecución (Siempre Antioquia, Medellín según requerimiento)
        print("📍 Llenando Lugar de Ejecución...")
        self._llenar_mui_autocomplete(self.INPUT_AUTO_DEPTO_EJECUCION, "Antioquia")
        self._llenar_mui_autocomplete(self.INPUT_AUTO_MUNI_EJECUCION, "Medellín")

        # Tiempo de prueba para verificación
        self.sb.sleep(3)
        
        # 11. Validar Final
        print("💾 Validando formulario completo...")
        btn_validar = self.sb.find_element(self.BTN_VALIDAR_FORMULARIO_FINAL)
        self.sb.execute_script("arguments[0].scrollIntoView();", btn_validar)
        
        self.sb.wait_for_element_clickable(self.BTN_VALIDAR_FORMULARIO_FINAL)
        self.sb.click(self.BTN_VALIDAR_FORMULARIO_FINAL)

        print("🚀 Confirmando y GUARDANDO en base de datos...")
        self.sb.wait_for_element_clickable(self.BTN_GUARDAR_FORMULARIO_FINAL, timeout=15)
        self.sb.click(self.BTN_GUARDAR_FORMULARIO_FINAL)
        
        print("⏳ Esperando la confirmación de éxito del sistema...")
        self.sb.wait_for_element_visible(self.MSG_EXITO_CREACION, timeout=20)
        print("✅ Mensaje de éxito detectado en pantalla.")

        print("🖱️ Haciendo clic en 'Aceptar' para finalizar...")
        self.sb.wait_for_element_clickable(self.BTN_ACEPTAR_EXITO)
        self.sb.click(self.BTN_ACEPTAR_EXITO)

        self.sb.wait_for_element_not_visible("//div[contains(@role, 'dialog')]", timeout=10)

        print("✅ Formulario principal diligenciado y validado.")

        return True