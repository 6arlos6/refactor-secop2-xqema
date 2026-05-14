# -*- coding: utf-8 -*-
"""
Page Object: Adjuntar Documentos y Publicar (Proceso 5)
Extraido de: proyecto-original-secob/funciones.py lineas 660-818 (documentos_proceso)

Adjunte de archivos via Selenium:
  SECOP II expone un <input type="file" multiple> en el popup DocumentAlternateUpload.
  Se manipula directamente con send_keys(rutas), sin pyautogui, sin GUI del OS.
  Esto hace el flujo compatible con headless=True y agnostico al sistema operativo.
"""
import os
import time
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
    BTN_DOCUMENTOS   = "//span[@id = 'lnk_stpmStepManager5']"
    BTN_ANEXAR_DOCS  = "incContractDocumentsbtnUploadDocumentGen"
    BTN_UPLOAD_FILES = "btnUploadFilesButtonBottom"
    BTN_CERRAR_MODAL = "btnCancelBottomButtom"
    BTN_IR_PUBLICAR  = "//input[@id = 'btnOption_trRowToolbarTop_tdCell1_tbToolBar_Finish']"
    BTN_PUBLICAR     = "//input[@id = 'tbToolBarPlaceHolder_btnPublishRequest']"
    TABLA_ARCHIVOS   = '//*[@id="tblFilesTable"]/tbody[2]'
    LOADING_INDICATOR = "/html/body/div[2]/div[2]/div[2]/div[1]/table/tbody/tr/td[2]"
    # Selector del file input en el popup DocumentAlternateUpload.
    # El atributo multiple="" permite enviar varias rutas separadas por \n.
    INPUT_ARCHIVOS   = 'input[type="file"]'

    def adjuntar_y_publicar(self, url_proceso_4, numero_contrato):
        """
        Descarga documentos de OnBase, los adjunta al proceso y publica.
        Retorna tupla (url_publicada, datetime_publicacion).

        Original: funciones.py:660-817 — documentos_proceso(params)
        """
        ahora = datetime.now()
        print("Iniciando proceso de documentos y publicacion...")

        # Navegar y click en tab documentos — click_limpio porque vortal-preloader
        # intercepta el click nativo igual que en cuestionario_page.
        # SAVE_TIMEOUT (40 s) en lugar de LONG_TIMEOUT (20 s): en headless la carga
        # completa del proceso puede tardar mas que en modo visible.
        self.driver.get(url_proceso_4)
        self.esperar_y_click_limpio(self.BTN_DOCUMENTOS, timeout=SAVE_TIMEOUT)

        # Descargar documentos de OnBase (linea 682 — usa su propio driver)
        onbase = OnBasePage()
        lista_documentos = onbase.descargar_documentos(numero_contrato)
        if len(lista_documentos) == 0:
            print("ADVERTENCIA: OnBase no retorno documentos para este contrato.")
            print("  Posibles causas: contrato de prueba sin documentos, credenciales incorrectas,")
            print("  o expediente no encontrado. El proceso se publicara SIN adjuntar documentos.")
            url_publicada = self._publicar_sin_documentos()
            return url_publicada, ahora

        # Construir rutas absolutas — onbase.descargar_documentos() retorna solo nombres de archivo
        rutas_docs = [os.path.join(DOWNLOAD_DIR, nombre) for nombre in lista_documentos]
        print(f"  {len(rutas_docs)} documento(s) listos en: {DOWNLOAD_DIR}")

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

        # Cargar archivos directamente via Selenium (reemplaza todo el bloque pyautogui)
        # El popup DocumentAlternateUpload expone input[type="file" multiple].
        self._cargar_archivos_via_input(rutas_docs)

        # Pausa necesaria para que SECOP II procese la seleccion de archivos antes del upload.
        # El original tenia time.sleep(8) tras el paste de portapapeles — mismo proposito.
        time.sleep(5)

        # Click en boton upload (lineas 735-737).
        # Se usa ActionChains directo sobre self.driver (no sb.click) porque estamos en una
        # ventana popup abierta via driver.switch_to.window() y SeleniumBase puede perder
        # el contexto de ventana. ActionChains sobre el driver subyacente siempre sigue el
        # contexto activo del driver.
        from selenium.webdriver.common.action_chains import ActionChains
        btn_upload = self._wait(LONG_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, self.BTN_UPLOAD_FILES))
        )
        ActionChains(self.driver).move_to_element(btn_upload).click().perform()
        time.sleep(3)  # pausa tras click de upload (igual que el original, linea 738)

        # Esperar que todos los documentos se clasifiquen como "Documento anexo" (lineas 740-757).
        # Timeout extendido a 120 s: 22 archivos en headless puede tardar mas que en modo visible.
        tbody = self.esperar_presente(self.TABLA_ARCHIVOS)
        tr_elements = tbody.find_elements(By.TAG_NAME, 'tr')
        num_tr = len(tr_elements)
        print(f"  Popup: {num_tr} fila(s) en tabla. Esperando clasificacion 'Documento anexo'...")

        self._wait(120).until(
            lambda d: len(d.find_elements(By.XPATH, '//span[text()="Documento anexo"]')) >= num_tr
        )

        # Cerrar modal (lineas 760-763) — driver directo por mismo motivo que btn_upload
        btn_cerrar = self._wait(LONG_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, self.BTN_CERRAR_MODAL))
        )
        ActionChains(self.driver).move_to_element(btn_cerrar).click().perform()
        self.driver.switch_to.window(self.driver.window_handles[0])

        # Esperar carga de documentos anexados (lineas 765-767).
        # LOADING_INDICATOR es un XPath absoluto fragil: no siempre aparece
        # (el servidor puede procesar los docs antes de que el spinner sea visible).
        # Se hace opcional — si no aparece en 10s, se da una pausa fija y se sigue.
        try:
            self.esperar_presente(self.LOADING_INDICATOR, timeout=10)
            self.esperar_invisible(self.LOADING_INDICATOR, timeout=60)
        except Exception:
            time.sleep(5)

        # Ir a publicar (lineas 769-776).
        # Si el proceso ya esta en la etapa de publicacion, este boton puede no existir.
        # En ese caso se salta directamente a BTN_PUBLICAR.
        try:
            self.esperar_y_click(self.BTN_IR_PUBLICAR, timeout=LONG_TIMEOUT)
            try:
                self.esperar_invisible(self.LOADING_INDICATOR, timeout=60)
            except Exception:
                time.sleep(3)
        except Exception:
            print("  [INFO] Boton 'Ir a publicar' no encontrado — saltando directo a Publicar.")

        # Publicar (lineas 778-782)
        self.esperar_y_click(self.BTN_PUBLICAR, timeout=LONG_TIMEOUT)

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

    # -------------------------------------------------------------------------
    # METODOS PRIVADOS
    # -------------------------------------------------------------------------

    def _cargar_archivos_via_input(self, rutas_docs):
        """
        Carga archivos en el popup de upload de SECOP II via Selenium, sin GUI ni pyautogui.

        El popup DocumentAlternateUpload expone <input type="file" multiple>.
        Selenium puede enviar las rutas absolutas directamente con send_keys(),
        separadas por \\n para seleccion multiple. Funciona en headless y en
        cualquier sistema operativo donde los archivos existan en disco.

        Reemplaza el bloque pyautogui original (funciones.py lineas 706-734).
        """
        print(f"  Cargando {len(rutas_docs)} archivo(s) via Selenium file input...")

        # Esperar a que el input de archivos aparezca en el popup
        input_file = self._wait(LONG_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.INPUT_ARCHIVOS))
        )

        # Hacer visible el input si el framework lo ocultó con display:none o visibility:hidden
        # (SECOP II usa un div decorativo encima del input nativo — hay que exponerlo)
        self.driver.execute_script(
            "arguments[0].style.display='block'; arguments[0].style.visibility='visible';",
            input_file
        )

        # Enviar todas las rutas de una vez (\n como separador para multiple files)
        input_file.send_keys("\n".join(rutas_docs))

        # Disparar evento 'change' explicitamente para que el framework de SECOP II
        # registre la seleccion de archivos. Se usa querySelector dentro del script
        # (no arguments[0]) porque send_keys puede hacer que SECOP II reconstruya el
        # input en el DOM, dejando la referencia Python stale antes de execute_script.
        try:
            self.driver.execute_script(
                "var el = document.querySelector('input[type=\"file\"]');"
                "if (el) el.dispatchEvent(new Event('change', {bubbles: true}));"
            )
        except Exception:
            pass  # Si falla el dispatchEvent, continuar — send_keys ya disparó change internamente
        print("  Archivos enviados al input de carga.")

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
