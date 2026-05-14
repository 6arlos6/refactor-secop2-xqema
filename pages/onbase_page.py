# -*- coding: utf-8 -*-
"""
Page Object: Integracion con OnBase (descarga de documentos)
Extraido de: proyecto-original-secob/funciones.py lineas 820-973 (descargar_onbase)

NOTA: Este page object maneja su PROPIO driver Chrome independiente
porque OnBase requiere una sesion separada con configuracion de descarga.

NOTA SOBRE time.sleep():
  OnBase es una aplicacion legacy con menus y frames AJAX que no emiten
  senales DOM confiables de "carga completa". Los time.sleep() en esta
  clase son NECESARIOS en los mismos puntos que el original funciones.py:
  animaciones de menus, transiciones entre iframes, y actualizaciones
  de grid tras seleccion. NO son reemplazables por WebDriverWait aqui
  porque no hay elemento observable que senale el fin de esas transiciones.
"""
import os
import time
import zipfile
import unidecode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from utils.logger import log_step as print
from utils.mappers import TIPOLOGIAS_EXCLUIDAS, NOMBRES_EXCLUIDOS
from config.settings import URL_ONBASE, USER_ONBASE, PASS_ONBASE, DOWNLOAD_DIR, HEADLESS_MODE


# Timeouts para OnBase (aplicacion lenta con iframes anidados)
ONBASE_TIMEOUT = 20
ONBASE_LONG_TIMEOUT = 50


class OnBasePage:
    """
    Gestiona la descarga de documentos desde OnBase.
    Maneja su propio driver Chrome con configuracion de descarga.
    """

    def __init__(self):
        self.driver = None
        self.download_dir = DOWNLOAD_DIR

    def _inicializar_driver(self):
        """Crea un driver Chrome configurado para descargas automaticas."""
        # webdriver.Chrome() sin Service usa selenium-manager (Selenium 4.10+)
        # para encontrar el chromedriver — evita webdriver_manager y su WinError 193.
        # Las prefs se aplican en tiempo de inicio (mas confiable que CDP en runtime).
        options = Options()
        options.add_experimental_option('prefs', {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })
        if HEADLESS_MODE:
            # --headless=new: modo headless moderno de Chrome (compatible con descargas)
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=options)
        if not HEADLESS_MODE:
            self.driver.maximize_window()

    def _wait(self, timeout=ONBASE_TIMEOUT):
        return WebDriverWait(self.driver, timeout, poll_frequency=0.5)

    def _limpiar_directorio(self):
        """Lineas 980-986: Limpia la carpeta de documentos antes de descargar."""
        for file_name in os.listdir(self.download_dir):
            file_path = os.path.join(self.download_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def _extraer_zip(self, zip_path):
        """Lineas 976-978: Extrae un archivo zip."""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.download_dir)

    def descargar_documentos(self, numero_contrato):
        """
        Descarga documentos desde OnBase para un contrato dado.
        Retorna lista de nombres de documentos descargados.

        Original: funciones.py:820-973 — descargar_onbase(numero_contrato)
        """
        print(f"Descargando documentos de OnBase para: {numero_contrato}...")

        if isinstance(numero_contrato, int):
            numero_contrato = str(numero_contrato)
        if "-" in numero_contrato:
            numero_contrato = numero_contrato.split("-")[0]

        self._limpiar_directorio()
        self._inicializar_driver()

        lista_documentos_sin_repetidos = []

        try:
            # === LOGIN EN ONBASE (lineas 840-847) ===
            self.driver.get(URL_ONBASE)
            self._wait().until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(USER_ONBASE)
            self._wait().until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(PASS_ONBASE)
            self._wait().until(EC.element_to_be_clickable((By.ID, "loginButton"))).click()

            # Cerrar bloqueo si aparece (lineas 848-852)
            try:
                self._wait(5).until(EC.element_to_be_clickable((By.CLASS_NAME, "dialog-close"))).click()
            except Exception:
                pass

            # === NAVEGAR A CONSULTA PERSONALIZADA (lineas 853-860) ===
            print("OnBase: abriendo menu de navegacion...")
            self._wait().until(EC.element_to_be_clickable((By.XPATH, "/html/body/header/section[1]/div[1]"))).click()
            time.sleep(2)  # menu desplegable de OnBase necesita tiempo para animarse
            print("OnBase: abriendo consulta personalizada...")
            self._wait().until(EC.element_to_be_clickable((By.XPATH, '//*[@id="customquery"]'))).click()
            time.sleep(2)  # panel de navegacion lateral necesita tiempo para cargarse

            # Frame de navegacion (lineas 857-861)
            # switch_to.frame(ID_STRING) es mas robusto que switch_to.frame(element):
            # el element ref puede quedar stale si OnBase recarga el iframe.
            print("OnBase: entrando a NavPanelIFrame...")
            self._wait().until(EC.frame_to_be_available_and_switch_to_it((By.ID, "NavPanelIFrame")))
            time.sleep(2)  # contenido del frame necesita tiempo para cargarse

            # En headless, div.js-queryEmptyState puede quedar superpuesto sobre itemLabel133
            # e interceptar el click nativo. Esperar a que desaparezca antes de intentar el click.
            try:
                self._wait(10).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "js-queryEmptyState"))
                )
            except Exception:
                pass  # Si el div no existe o no desaparece, continuar con JS click

            print("OnBase: haciendo click en itemLabel133...")
            el_item = self._wait().until(EC.presence_of_element_located((By.ID, 'itemLabel133')))
            # JS click: bypasea la intercepcion de overlays (necesario en headless donde el
            # layout puede diferir del modo visible y dejar divs superpuestos sobre el target)
            self.driver.execute_script("arguments[0].click();", el_item)
            self.driver.switch_to.default_content()
            time.sleep(5)  # OnBase tarda ~5s en cargar frmViewer tras seleccionar item del menu

            # === BUSCAR EXPEDIENTE (lineas 862-871) ===
            wait_largo = self._wait(ONBASE_LONG_TIMEOUT)

            print("OnBase: esperando frmViewer...")
            wait_largo.until(EC.presence_of_element_located((By.ID, "frmViewer")))
            self.driver.switch_to.frame("frmViewer")  # por ID string — nunca queda stale
            print("OnBase: esperando html_form dentro de frmViewer...")
            wait_largo.until(EC.element_to_be_clickable((By.ID, 'html_form')))
            self.driver.switch_to.frame("html_form")

            print(f"OnBase: escribiendo numero de contrato '{numero_contrato}'...")
            self.driver.find_element(By.ID, 'Nombre expediente').send_keys(numero_contrato)
            wait_largo.until(EC.element_to_be_clickable((By.ID, "save"))).click()
            self.driver.switch_to.default_content()

            # === NAVEGAR A RESULTADOS (lineas 873-879) ===
            # Timeout extendido a 120s: contratos reales con muchos documentos
            # pueden tardar mas de 50s en cargar los resultados de busqueda.
            wait_resultados = self._wait(120)

            print("OnBase: esperando frmViewer con resultados...")
            wait_resultados.until(EC.presence_of_element_located((By.ID, 'frmViewer')))
            self.driver.switch_to.frame("frmViewer")

            print("OnBase: esperando customQueryResultsFrame...")
            wait_resultados.until(EC.presence_of_element_located((By.ID, 'customQueryResultsFrame')))
            self.driver.switch_to.frame("customQueryResultsFrame")

            print("OnBase: esperando frameDocSelect...")
            wait_resultados.until(EC.presence_of_element_located((By.ID, 'frameDocSelect')))
            self.driver.switch_to.frame("frameDocSelect")

            # === SELECCIONAR DOCUMENTOS (lineas 879-908) ===
            print("OnBase: esperando tabla de documentos (primaryHitlist_grid)...")
            tabla = wait_resultados.until(EC.element_to_be_clickable((By.ID, 'primaryHitlist_grid')))
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            print(f"OnBase: tabla encontrada con {len(filas)} filas. Seleccionando documentos...")

            # Deseleccionar primer elemento (lineas 886-889)
            ActionChains(self.driver).key_down(Keys.CONTROL).perform()
            filas[0].click()
            time.sleep(1)  # grid procesa la deseleccion

            last_selected = None

            for item in range(len(filas)):
                tipologia = self.driver.find_element(
                    By.XPATH, f'//*[@id="primaryHitlist_grid"]/tbody/tr[{item + 1}]/td[1]'
                ).get_attribute('textContent')
                nombre_doc = self.driver.find_element(
                    By.XPATH, f'//*[@id="primaryHitlist_grid"]/tbody/tr[{item + 1}]/td[2]'
                ).get_attribute('textContent')

                nombre_excluido = any(n in nombre_doc.strip() for n in NOMBRES_EXCLUIDOS)
                tipologia_excluida = any(t == tipologia.strip() for t in TIPOLOGIAS_EXCLUIDAS)

                if (not tipologia_excluida) or (tipologia.strip() == "CERTIFICADO DE ANTECEDENTES" and not nombre_excluido):
                    ActionChains(self.driver).key_down(Keys.CONTROL).perform()
                    time.sleep(1)  # CTRL debe estar activo antes del scroll/click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", filas[item])
                    self._wait().until(EC.element_to_be_clickable(filas[item]))
                    filas[item].click()
                    time.sleep(1)  # grid procesa la seleccion antes del siguiente item
                    last_selected = filas[item]

            # === DESCARGAR COMO ZIP (lineas 910-933) ===
            if not last_selected:
                print("No se encontraron documentos validos para descargar.")
                self.driver.quit()
                return lista_documentos_sin_repetidos

            print("OnBase: ejecutando clic derecho para descargar ZIP...")
            time.sleep(3)  # pausa antes de context_click (igual que el original)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", last_selected)
            time.sleep(1)  # esperar que el scroll se complete
            self._wait().until(EC.element_to_be_clickable(last_selected))
            ActionChains(self.driver).context_click(last_selected).perform()
            time.sleep(3)  # menu contextual necesita tiempo para aparecer en el DOM

            self.driver.switch_to.default_content()

            # Menu contextual: Enviar -> Archivo (lineas 923-930)
            menu_enviar = self._wait().until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuControl_25"]')))
            ActionChains(self.driver).click(menu_enviar).perform()
            time.sleep(3)  # submenu necesita tiempo para cargarse
            ventanas_antes = set(self.driver.window_handles)
            menu_archivo = self._wait().until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuControl_13"]')))
            ActionChains(self.driver).click(menu_archivo).perform()
            time.sleep(3)  # esperar que aparezca la nueva pestana SendToFile.aspx

            # OnBase WS1 23.1.x abre SendToFile.aspx en una nueva pestana antes del download.
            # Hay que cambiar a esa pestana y hacer click en su "Guardar" para iniciar la descarga.
            ventanas_nuevas = set(self.driver.window_handles) - ventanas_antes
            if ventanas_nuevas:
                print("OnBase: cambiando a pestana SendToFile.aspx...")
                self.driver.switch_to.window(ventanas_nuevas.pop())
            else:
                print("OnBase: SendToFile.aspx no abrio nueva pestana, buscando Guardar en pestana actual...")

            print("OnBase: haciendo click en Guardar de SendToFile...")
            self._wait(30).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Guardar')]"))).click()
            print("OnBase: descarga iniciada, esperando ZIP...")

            # === ESPERAR DESCARGA (lineas 934-942) ===
            zip_path = os.path.join(self.download_dir, "SavedDocument.zip")

            descarga_timeout = 120  # 2 minutos max
            inicio = time.time()
            while not os.path.exists(zip_path):
                if time.time() - inicio > descarga_timeout:
                    print("Timeout esperando descarga del ZIP.")
                    return lista_documentos_sin_repetidos
                try:
                    # Buscar texto "Error" en la ventana activa actual.
                    # Si SendToFile cerro la pestana y el driver quedo sin contexto,
                    # volver a la ventana principal de OnBase antes de buscar.
                    if len(self.driver.window_handles) > 0:
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Error')]"))
                    )
                    return lista_documentos_sin_repetidos
                except Exception:
                    pass
                time.sleep(2)

            # === PROCESAR ZIP (lineas 944-972) ===
            if os.path.isfile(zip_path):
                self.driver.quit()
                self._extraer_zip(zip_path)

                lista_documentos = os.listdir(self.download_dir)
                lista_documentos.remove("SavedDocument.zip")

                # Renombrar duplicados (lineas 952-961)
                for i, v in enumerate(lista_documentos):
                    totalcount = lista_documentos.count(v)
                    count = lista_documentos[:i].count(v)
                    if totalcount > 1:
                        old_name = os.path.join(self.download_dir, v)
                        new_name = os.path.join(self.download_dir, v + str(count + 1))
                        os.rename(old_name, new_name)
                        lista_documentos_sin_repetidos.append(v + str(count + 1))
                    else:
                        lista_documentos_sin_repetidos.append(v)

                # Quitar acentos de nombres (lineas 963-971)
                for i in range(len(lista_documentos_sin_repetidos)):
                    try:
                        item_sin_acentos = unidecode.unidecode(lista_documentos_sin_repetidos[i])
                        old_name = os.path.join(self.download_dir, lista_documentos_sin_repetidos[i])
                        new_name = os.path.join(self.download_dir, item_sin_acentos)
                        os.rename(old_name, new_name)
                        lista_documentos_sin_repetidos[i] = item_sin_acentos
                    except Exception:
                        continue

                os.remove(zip_path)

            print(f"Documentos descargados: {len(lista_documentos_sin_repetidos)}")
            return lista_documentos_sin_repetidos

        except Exception as e:
            print(f"Error en OnBase: {e}")
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            return lista_documentos_sin_repetidos
