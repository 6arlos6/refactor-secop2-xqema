# -*- coding: utf-8 -*-
"""
Page Object: Adjuntar Documentos y Publicar (Proceso 5)
Extraido de: proyecto-original-secob/funciones.py lineas 660-818 (documentos_proceso)

DEUDA TECNICA: El adjunte de archivos usa pyautogui (lineas 706-734)
porque SECOP II abre una ventana nativa de Windows para upload.
Esto debe reemplazarse por Selenium file input cuando sea posible.
"""
import os
import time
import pyautogui
from selenium.webdriver.common.by import By
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

        # Navegar y click en tab documentos — click_limpio porque vortal-preloader
        # intercepta el click nativo igual que en cuestionario_page
        self.driver.get(url_proceso_4)
        self.esperar_y_click_limpio(self.BTN_DOCUMENTOS, timeout=LONG_TIMEOUT)

        # Descargar documentos de OnBase (linea 682 — usa su propio driver)
        onbase = OnBasePage()
        lista_documentos = onbase.descargar_documentos(numero_contrato)
        if len(lista_documentos) == 0:
            print("ADVERTENCIA: OnBase no retorno documentos para este contrato.")
            print("  Posibles causas: contrato de prueba sin documentos, credenciales incorrectas,")
            print("  o expediente no encontrado. El proceso se publicara SIN adjuntar documentos.")
            url_publicada = self._publicar_sin_documentos()
            return url_publicada, ahora

        # Click en boton anexar documentos (linea 685)
        # JS click: el overlay vortal-preloader reaparece tras los minutos en OnBase
        # y bloquea el click nativo. esperar_y_click_js elimina overlays + usa JS click.
        ventanas_antes = set(self.driver.window_handles)
        self.esperar_y_click_js(self.BTN_ANEXAR_DOCS, timeout=LONG_TIMEOUT)

        # Esperar a que $.popupWindow abra la nueva ventana de upload (linea 686: sleep(5))
        # El popup se abre de forma asincronica — hay que esperar antes de capturar handles.
        self._wait(LONG_TIMEOUT).until(
            lambda d: len(d.window_handles) > len(ventanas_antes)
        )
        nueva_ventana = (set(self.driver.window_handles) - ventanas_antes).pop()
        self.driver.switch_to.window(nueva_ventana)
        self.driver.maximize_window()
        time.sleep(6)  # popup DocumentAlternateUpload necesita tiempo para cargar (linea 690)

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
        # os.sep garantiza el separador correcto por OS (\\ en Windows, / en Unix)
        path_docs = DOWNLOAD_DIR + os.sep

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

    def _publicar_sin_documentos(self):
        """
        Publica el proceso saltando el adjunte de documentos.
        Se usa cuando OnBase no retorna documentos (contrato de prueba o error).
        Retorna la URL publicada.
        """
        print("Publicando proceso sin adjuntar documentos...")

        self.esperar_y_click(self.BTN_IR_PUBLICAR, timeout=LONG_TIMEOUT)

        # LOADING_INDICATOR puede no existir si no hubo carga de documentos — es opcional
        try:
            self.esperar_invisible(self.LOADING_INDICATOR, timeout=30)
        except Exception:
            pass

        self.esperar_y_click(self.BTN_PUBLICAR, timeout=LONG_TIMEOUT)
        self.aceptar_alerta_si_existe(timeout=5)

        try:
            url_antes = self.url_actual
            self._wait(50).until(EC.url_changes(url_antes))
        except Exception:
            print("Advertencia: la URL no cambio durante la publicacion sin documentos")

        url_publicada = self.url_actual
        print("Proceso publicado (sin documentos adjuntos).")
        return url_publicada
