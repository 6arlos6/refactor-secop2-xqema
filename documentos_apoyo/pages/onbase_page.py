import os
import shutil
import zipfile
import unidecode
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import BaseCase
from pages.base_page import BasePage
from config.settings import DOWNLOAD_DIR
from utils.logger import log_step as print

class OnBasePage(BasePage):
    def __init__(self, sb: BaseCase, download_dir: str):
        super().__init__(sb)
        self.download_dir = download_dir

    # =========================================================================
    #  SELECTORES CSS / XPATH
    # =========================================================================
    INPUT_USUARIO = "#username"
    INPUT_CONTRASENA = "#password"
    BTN_LOGIN = "#loginButton"
    BTN_DIALOG_CLOSE = ".dialog-close"
    
    BTN_MENU_PRINCIPAL = "/html/body/header/section[1]/div[1]" 
    BTN_CUSTOM_QUERY = "#customquery"
    
    IFRAME_NAV = "#NavPanelIFrame"
    BTN_BUSCAR_DOCS_EXP = "#itemLabel133"
    
    IFRAME_VIEWER = "#frmViewer"
    IFRAME_HTML_FORM = "#html_form"
    INPUT_NOMBRE_EXPEDIENTE = "[id='Nombre expediente']" 
    BTN_SAVE_SEARCH = "#save"
    
    IFRAME_QUERY_RESULTS = "#customQueryResultsFrame"
    IFRAME_DOC_SELECT = "#frameDocSelect"
    TABLA_RESULTADOS = "#primaryHitlist_grid"
    FILAS_TABLA = "#primaryHitlist_grid tr"
    
    MENU_OPCION_8 = "/html/body/div[7]/div/ul/li[8]"
    SUBMENU_OPCION_1 = "/html/body/div[8]/div/ul/li[1]"
    BTN_GUARDAR_ZIP = "//button[contains(text(), 'Guardar')]"
    BTN_CERRAR_DESCARGA = "//button[contains(text(), 'Cerrar')]"
    LBL_ERROR_DESCARGA = "//*[contains(text(), 'Error')]"
    
    LBL_USUARIO_ACTUAL = "//*[@id='realNameDiv']"
    ITEM_CERRAR_CESION = "//li[contains(@onclick, 'DoLogout')]"
    MENSAJE_DESCONEXION = "//div[contains(text(), 'Usted fue desconectado')]"
    # =========================================================================
    #  MÉTODOS DINÁMICOS (SIN SLEEPS)
    # =========================================================================
    def autenticar_y_preparar(self, url, user, password, attempts=3):
        """Inicia sesión usando esperas dinámicas y reintentos."""
        print("🔐 Iniciando autenticación en OnBase...")
        
        for attempt in range(attempts):
            try:
                self.sb.open(url)
                self.sb.type(self.INPUT_USUARIO, user, timeout=10)
                self.sb.type(self.INPUT_CONTRASENA, password, timeout=5)
                self.sb.click(self.BTN_LOGIN)
                
                try:
                    self.sb.wait_for_element_visible(self.BTN_DIALOG_CLOSE, timeout=10)
                    self.sb.click(self.BTN_DIALOG_CLOSE)
                    print("✔️ Modal de bienvenida cerrado.")
                except Exception:
                    pass
                
                print("✅ Autenticación exitosa.")
                break
                
            except Exception as e:
                if attempt == attempts - 1:
                    raise Exception(f"❌ Falló la autenticación en OnBase. Detalle: {str(e)}")
                else:
                    print(f"⚠️ Intento {attempt + 1} fallido. Recargando...")

    def cerrar_cesion(self, attempts = 3):
        print("🔐 Cerrando cesión en OnBase...")

        for attempt in range(attempts):
            try:
                self.sb.wait_for_element_clickable(self.LBL_USUARIO_ACTUAL, timeout=10)
                self.sb.click(self.LBL_USUARIO_ACTUAL)
                self.sb.wait_for_element_clickable(self.ITEM_CERRAR_CESION, timeout=10)
                self.sb.click(self.ITEM_CERRAR_CESION)
                self.sb.wait_for_element_visible(self.MENSAJE_DESCONEXION, timeout=10)
                print("✅ Cesión cerrada correctamente...")
                break
            except Exception as e:
                if attempt == attempts - 1:
                    raise Exception(f"❌ Falló el proceso de cerrar cesión en OnBase. Detalle: {str(e)}")
                else:
                    print(f"⚠️ Intento de cierre de cesión {attempt + 1} fallido. Reintentando...")

    def buscar_expediente(self, contrato):
        """Navega por los iframes y ejecuta la búsqueda esperando a que los DOMs carguen de forma dinámica."""
        print(f"🔍 Buscando expediente del contrato {contrato} en OnBase...")
        contrato_limpio = str(contrato).split('-')[0] if '-' in str(contrato) else str(contrato)

        # 1. Menú principal
        self.sb.wait_for_element_clickable(self.BTN_MENU_PRINCIPAL, timeout=40)
        self.sb.click(self.BTN_MENU_PRINCIPAL)
        
        self.sb.wait_for_element_clickable(self.BTN_CUSTOM_QUERY, timeout=10)
        self.sb.click(self.BTN_CUSTOM_QUERY)

        # 2. Navegación en el primer IFrame
        self.sb.switch_to_frame(self.IFRAME_NAV, timeout=15)
        self.sb.wait_for_element_clickable(self.BTN_BUSCAR_DOCS_EXP, timeout=15)

        self.sb.sleep(2)
        
        self.sb.click(self.BTN_BUSCAR_DOCS_EXP)
        self.sb.switch_to_default_content()

        # 3. Formulario de búsqueda (Doble IFrame anidado)
        self.sb.switch_to_frame(self.IFRAME_VIEWER, timeout=30)
        self.sb.switch_to_frame(self.IFRAME_HTML_FORM, timeout=30)
        self.sb.wait_for_ready_state_complete()
        
        # 3.4. Esperamos dinámicamente el input y ejecutamos la búsqueda
        self.sb.wait_for_element_visible(self.INPUT_NOMBRE_EXPEDIENTE, timeout=20)
        self.sb.type(self.INPUT_NOMBRE_EXPEDIENTE, contrato_limpio)
        
        self.sb.wait_for_element_clickable(self.BTN_SAVE_SEARCH, timeout=10)
        self.sb.click(self.BTN_SAVE_SEARCH)
        
        # 4. Volvemos a la raíz para los siguientes pasos
        self.sb.switch_to_default_content()

    def seleccionar_y_descargar(self):
        """Interactúa con la tabla de resultados y despliega menús contextuales de forma fluida."""
        print("📥 Seleccionando documentos para descarga...")
        
        # 1. Navegación a la grilla de resultados (Triple IFrame)
        self.sb.switch_to_frame(self.IFRAME_VIEWER, timeout=30)
        self.sb.switch_to_frame(self.IFRAME_QUERY_RESULTS, timeout=30)
        self.sb.switch_to_frame(self.IFRAME_DOC_SELECT, timeout=30)
        
        # Esperamos dinámicamente que la tabla cargue
        self.sb.wait_for_element_visible(self.TABLA_RESULTADOS, timeout=40)
        filas = self.sb.find_elements(self.FILAS_TABLA)
        
        if not filas:
            print("⚠️ No se encontraron documentos para este expediente.")
            self.sb.switch_to_default_content()
            return False

        # 2. Selección masiva (Shift + Clic) optimizada
        self.sb.wait_for_element_clickable(self.FILAS_TABLA, timeout=10)
        filas[0].click()
        
        acciones = ActionChains(self.sb.driver)
        ultima_fila = filas[-1]
        
        # Hacemos scroll físico hasta la última fila antes de hacerle clic
        self.sb.execute_script("arguments[0].scrollIntoView(true);", ultima_fila)
        acciones.key_down(Keys.SHIFT).click(ultima_fila).key_up(Keys.SHIFT).perform()
        
        # 3. Menú contextual
        acciones.context_click(ultima_fila).perform()
        self.sb.switch_to_default_content()
        
        # Esperamos dinámicamente a que el menú flotante de OnBase aparezca en el DOM principal
        self.sb.wait_for_element_clickable(self.MENU_OPCION_8, timeout=15)
        self.sb.click(self.MENU_OPCION_8)
        
        self.sb.wait_for_element_clickable(self.SUBMENU_OPCION_1, timeout=15)
        self.sb.click(self.SUBMENU_OPCION_1)
        
        # Cambio de ventana si OnBase la lanza separada
        if len(self.sb.driver.window_handles) > 1:
            self.sb.switch_to_newest_window()

        self.sb.wait_for_element_clickable(self.BTN_GUARDAR_ZIP, timeout=15)
        self.sb.click(self.BTN_GUARDAR_ZIP)
        
        return True

    def limpiar_directorio(self, directorio):
        """Itera sobre la carpeta y elimina todos los archivos/subcarpetas residuales."""
        if os.path.exists(directorio):
            print(f"\n🧹 Limpiando directorio antes de procesar la descarga: {directorio}")
            for nombre_archivo in os.listdir(directorio):
                ruta_completa = os.path.join(directorio, nombre_archivo)
                try:
                    if os.path.isfile(ruta_completa) or os.path.islink(ruta_completa):
                        os.unlink(ruta_completa)
                    elif os.path.isdir(ruta_completa):
                        shutil.rmtree(ruta_completa)
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar {ruta_completa}. Razón: {e}")

    def procesar_descarga(self):
        """Vigila la descarga del archivo a nivel de sistema operativo sin frenar la ejecución."""
        
        self.limpiar_directorio(DOWNLOAD_DIR)

        nombre_zip = "SavedDocument.zip"
        print("⏳ Descargando ZIP desde OnBase...")
        
        try:
            self.sb.assert_downloaded_file(nombre_zip, timeout=60)
        except Exception:
            try:
                self.sb.wait_for_element_visible(self.LBL_ERROR_DESCARGA, timeout=5)
                print("❌ OnBase arrojó un error en pantalla durante la descarga.")
            except Exception:
                print("❌ El archivo nunca llegó a la carpeta de descargas local.")
            return []

        print("📦 Extrayendo y procesando archivos...")
        
        ruta_origen_zip = os.path.join(self.sb.get_downloads_folder(), nombre_zip)
        
        with zipfile.ZipFile(ruta_origen_zip, 'r') as zip_ref:
            zip_ref.extractall(self.download_dir)

        os.remove(ruta_origen_zip) 
        
        archivos_finales = []
        lista_documentos = os.listdir(self.download_dir)
        
        for doc in lista_documentos:
            old_path = os.path.join(self.download_dir, doc)
            if not os.path.isfile(old_path): 
                continue

            # 1. Quitar tildes
            nombre_limpio = unidecode.unidecode(doc)
            nombre_base, extension = os.path.splitext(nombre_limpio)
            
            # 2. Calcular espacio máximo para el nombre (80 menos la extensión ".pdf")
            max_longitud_nombre = 80 - len(extension)
            
            # Recorte inicial
            if len(nombre_base) > max_longitud_nombre:
                nombre_base = nombre_base[:max_longitud_nombre]
                
            nuevo_nombre = f"{nombre_base}{extension}"
            new_path = os.path.join(self.download_dir, nuevo_nombre)
            
            # 3. ANTI-DUPLICADOS (Con protección de longitud)
            contador = 1
            while os.path.exists(new_path) and old_path != new_path:
                sufijo = f"_{contador}"
                
                # Se hace espacio al sufijo para no pasarnos de 80
                espacio_disponible = max_longitud_nombre - len(sufijo)
                nombre_base_ajustado = nombre_base[:espacio_disponible]
                
                nuevo_nombre = f"{nombre_base_ajustado}{sufijo}{extension}"
                new_path = os.path.join(self.download_dir, nuevo_nombre)
                contador += 1
                
            # 4. Renombrar físicamente  
            if old_path != new_path:
                os.rename(old_path, new_path)
                print(f"🔄 Archivo ajustado: '{doc}' -> '{nuevo_nombre}'")
                
            archivos_finales.append(new_path)
        
        return archivos_finales
    
    def cerrar_ventana_descarga(self):
        try:
            self.sb.wait_for_element_clickable(self.BTN_CERRAR_DESCARGA, timeout=15)
            self.sb.click(self.BTN_CERRAR_DESCARGA)
            return True
        except:
            print("❌ No se cerró correctamente la ventana de descargas.")
            return False 