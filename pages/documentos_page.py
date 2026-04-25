# -*- coding: utf-8 -*-
"""
Page Object: Adjuntar Documentos y Publicar (Proceso 5)
Extraido de: proyecto-original-secob/funciones.py lineas 660-818 (documentos_proceso)

DEUDA TECNICA: El adjunte de archivos usa pyautogui (lineas 706-734)
porque SECOP II abre una ventana nativa de Windows para upload.
Esto debe reemplazarse por Selenium file input cuando sea posible.
"""
import time
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pages.base_page import BasePage, DEFAULT_TIMEOUT, LONG_TIMEOUT, SAVE_TIMEOUT
from pages.onbase_page import OnBasePage
from utils.logger import log_step as print
from config.settings import DOWNLOAD_DIR


class DocumentosPage(BasePage):
    """Gestiona el adjunte de documentos y la publicacion del proceso."""

    # === SELECTORES ===
    BTN_DOCUMENTOS = "//span[@id = 'lnk_stpmStepManager5']"
    BTN_ANEXAR_DOCS = "incContractDocumentsbtnUploadDocumentGen"
    BTN_UPLOAD_FILES = "btnUploadFilesButtonBottom"
    BTN_CERRAR_MODAL = "btnCancelBottomButtom"
    BTN_IR_PUBLICAR = "//input[@id = 'btnOption_trRowToolbarTop_tdCell1_tbToolBar_Finish']"
    BTN_PUBLICAR = "//input[@id = 'tbToolBarPlaceHolder_btnPublishRequest']"
    TABLA_ARCHIVOS = '//*[@id="tblFilesTable"]/tbody[2]'
    LOADING_INDICATOR = "/html/body/div[2]/div[2]/div[2]/div[1]/table/tbody/tr/td[2]"
    TITULO_PAGINA = '//*[@id="spnPageTitle"]'

    def adjuntar_y_publicar(self, url_proceso_4, numero_contrato):
        """
        Descarga documentos de OnBase, los adjunta al proceso y publica.
        Retorna tupla (url_publicada, datetime_publicacion).

        Original: funciones.py:660-817 — documentos_proceso(params)
        """
        ahora = datetime.now()
        print("Iniciando proceso de documentos y publicacion...")

        # Navegar y click en tab documentos (lineas 677-681)
        self.driver.get(url_proceso_4)
        self.click_cuando_estable(self.BTN_DOCUMENTOS, timeout=LONG_TIMEOUT)

        # Descargar documentos de OnBase (linea 682 — usa su propio driver)
        onbase = OnBasePage()
        lista_documentos = onbase.descargar_documentos(numero_contrato)
        if len(lista_documentos) == 0:
            raise Exception("Parece que hubo un problema en OnBase o no fue posible adjuntar los documentos")

        # Click en boton anexar documentos (linea 685)
        self.esperar_y_click_por_id(self.BTN_ANEXAR_DOCS, timeout=LONG_TIMEOUT)

        # Cambiar a ventana de carga (lineas 687-690)
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[-1])
        self.driver.maximize_window()

        # Click para mantener foco (lineas 692-701)
        try:
            self.esperar_y_click(self.TITULO_PAGINA, timeout=5)
        except Exception:
            pass

        # ================================================================
        # DEUDA TECNICA: Adjunte de archivos con pyautogui (lineas 706-734)
        # SECOP II usa una ventana nativa de Windows para upload.
        # Los time.sleep aqui son NECESARIOS porque pyautogui interactua
        # con el sistema operativo, no con Selenium.
        # ================================================================
        path_docs = DOWNLOAD_DIR + "\\"

        pyautogui.hotkey('win', 'r')
        time.sleep(3)
        pyautogui.write(path_docs)
        pyautogui.press('enter')
        time.sleep(5)
        pyautogui.hotkey('ctrl', 'e')
        time.sleep(3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(5)
        pyautogui.hotkey('alt', 'f4')
        time.sleep(2)

        self.driver.switch_to.window(self.driver.window_handles[-1])

        screen_width, _ = pyautogui.size()
        center_x = screen_width // 2
        pyautogui.click(center_x, 200)
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(8)
        # ================================================================

        # Click en boton upload (lineas 735-737)
        self.esperar_y_click_por_id(self.BTN_UPLOAD_FILES)

        # Esperar que todos los documentos se clasifiquen como "Documento anexo" (lineas 740-757)
        tbody = self.esperar_presente(self.TABLA_ARCHIVOS)
        tr_elements = tbody.find_elements(By.TAG_NAME, 'tr')
        num_tr = len(tr_elements)

        # Esperar clasificacion de todos los docs (con timeout para no quedar en loop infinito)
        self._wait(60).until(
            lambda d: len(d.find_elements(By.XPATH, '//span[text()="Documento anexo"]')) >= num_tr
        )

        # Cerrar modal (lineas 760-763)
        self.esperar_y_click_por_id(self.BTN_CERRAR_MODAL)
        self.driver.switch_to.window(handles[0])

        # Esperar carga de documentos anexados (lineas 765-767)
        self.esperar_presente(self.LOADING_INDICATOR, timeout=60)

        # Ir a publicar (lineas 769-776)
        self.esperar_y_click(self.BTN_IR_PUBLICAR)
        self.esperar_invisible(self.LOADING_INDICATOR, timeout=60)

        # Publicar (lineas 778-782)
        self.esperar_y_click(self.BTN_PUBLICAR)

        # Aceptar alerta si aparece (lineas 784-789)
        self.aceptar_alerta_si_existe(timeout=5)

        # Esperar cambio de URL (lineas 791-798)
        try:
            url_antes = self.url_actual
            self._wait(50).until(EC.url_changes(url_antes))
        except Exception:
            print("Advertencia: la URL no cambio durante el tiempo estipulado")

        url_publicada = self.url_actual
        print("Proceso publicado exitosamente.")

        return url_publicada, ahora
