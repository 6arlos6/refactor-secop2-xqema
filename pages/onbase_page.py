# -*- coding: utf-8 -*-
"""
Page Object: Integracion con OnBase (descarga de documentos)
Extraido de: proyecto-original-secob/funciones.py lineas 820-973 (descargar_onbase)

NOTA: Este page object maneja su PROPIO driver Chrome independiente
porque OnBase requiere una sesion separada con configuracion de descarga.
"""
import os
import time
import zipfile
import unidecode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.logger import log_step as print
from utils.mappers import TIPOLOGIAS_EXCLUIDAS, NOMBRES_EXCLUIDOS
from config.settings import URL_ONBASE, USER_ONBASE, PASS_ONBASE, DOWNLOAD_DIR


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
        options = Options()
        options.add_experimental_option('prefs', {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
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
            self.driver.execute_script("document.body.style.zoom='97%'")

            self._wait().until(EC.element_to_be_clickable((By.ID, "username"))).send_keys(USER_ONBASE)
            self._wait().until(EC.element_to_be_clickable((By.ID, "password"))).send_keys(PASS_ONBASE)
            self._wait().until(EC.element_to_be_clickable((By.ID, "loginButton"))).click()

            # Cerrar bloqueo si aparece (lineas 848-852)
            try:
                self._wait(5).until(EC.element_to_be_clickable((By.CLASS_NAME, "dialog-close"))).click()
            except Exception:
                pass

            # === NAVEGAR A CONSULTA PERSONALIZADA (lineas 853-860) ===
            self._wait().until(EC.element_to_be_clickable((By.XPATH, "/html/body/header/section[1]/div[1]"))).click()
            self._wait().until(EC.element_to_be_clickable((By.XPATH, '//*[@id="customquery"]'))).click()

            # Frame de navegacion (lineas 857-861)
            self._wait().until(EC.frame_to_be_available_and_switch_to_it((By.ID, "NavPanelIFrame")))
            self._wait().until(EC.element_to_be_clickable((By.ID, 'itemLabel133'))).click()
            self.driver.switch_to.default_content()

            # === BUSCAR EXPEDIENTE (lineas 862-871) ===
            wait_largo = self._wait(ONBASE_LONG_TIMEOUT)

            frame_viewer = wait_largo.until(EC.presence_of_element_located((By.ID, "frmViewer")))
            self.driver.switch_to.frame(frame_viewer)
            frame_html = wait_largo.until(EC.element_to_be_clickable((By.ID, 'html_form')))
            self.driver.switch_to.frame(frame_html)

            self.driver.find_element(By.ID, 'Nombre expediente').send_keys(numero_contrato)
            wait_largo.until(EC.element_to_be_clickable((By.ID, "save"))).click()
            self.driver.switch_to.default_content()

            # === NAVEGAR A RESULTADOS (lineas 873-879) ===
            frame_resultados = wait_largo.until(EC.presence_of_element_located((By.ID, 'frmViewer')))
            self.driver.switch_to.frame(frame_resultados)
            frame_query = wait_largo.until(EC.element_to_be_clickable((By.ID, 'customQueryResultsFrame')))
            self.driver.switch_to.frame(frame_query)
            frame_docs = wait_largo.until(EC.element_to_be_clickable((By.ID, 'frameDocSelect')))
            self.driver.switch_to.frame(frame_docs)

            # === SELECCIONAR DOCUMENTOS (lineas 879-908) ===
            tabla = wait_largo.until(EC.element_to_be_clickable((By.ID, 'primaryHitlist_grid')))
            filas = tabla.find_elements(By.TAG_NAME, "tr")

            # Deseleccionar primer elemento (lineas 886-889)
            ActionChains(self.driver).key_down(Keys.CONTROL).perform()
            filas[0].click()

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
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", filas[item])
                    self._wait().until(EC.element_to_be_clickable(filas[item]))
                    filas[item].click()
                    last_selected = filas[item]

            # === DESCARGAR COMO ZIP (lineas 910-933) ===
            if not last_selected:
                print("No se encontraron documentos validos para descargar.")
                self.driver.close()
                return lista_documentos_sin_repetidos

            self.driver.execute_script("arguments[0].scrollIntoView(true);", last_selected)
            self._wait().until(EC.element_to_be_clickable(last_selected))
            ActionChains(self.driver).context_click(last_selected).perform()

            self.driver.switch_to.default_content()

            # Menu contextual: Enviar -> Archivo (lineas 923-930)
            menu_enviar = self._wait().until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuControl_25"]')))
            ActionChains(self.driver).click(menu_enviar).perform()
            menu_archivo = self._wait().until(EC.element_to_be_clickable((By.XPATH, '//*[@id="menuControl_13"]')))
            ActionChains(self.driver).click(menu_archivo).perform()

            # Click en Guardar (linea 933)
            self._wait().until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Guardar')]"))).click()

            # === ESPERAR DESCARGA (lineas 934-942) ===
            zip_path = os.path.join(self.download_dir, "SavedDocument.zip")

            # Esperar archivo con timeout (reemplaza while True + time.sleep(2))
            descarga_timeout = 120  # 2 minutos max
            inicio = time.time()
            while not os.path.exists(zip_path):
                if time.time() - inicio > descarga_timeout:
                    print("Timeout esperando descarga del ZIP.")
                    return lista_documentos_sin_repetidos
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Error')]"))
                    )
                    # Si aparece texto "Error", abortar
                    return lista_documentos_sin_repetidos
                except Exception:
                    pass

            # === PROCESAR ZIP (lineas 944-972) ===
            if os.path.isfile(zip_path):
                self.driver.close()
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
                    self.driver.close()
                except Exception:
                    pass
            return lista_documentos_sin_repetidos
