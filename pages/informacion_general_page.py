# -*- coding: utf-8 -*-
"""
Page Object: Informacion General del Proceso (Proceso 2)
Extraido de: proyecto-original-secob/funciones.py lineas 127-382 (informacion_general)

Bugs corregidos (25/04/2026):
  - Bug 1 (CRÍTICO): XPath del autocomplete de proveedor era //li[1] — SECOP II requiere
    click en el <span> interno (//div[@class='ac_results']//li[1]//span[1]//span).
    El click en el <li> no dispara la seleccion → bot entraba al flujo de creacion.
  - Bug 2 (CRÍTICO): Sin recuperacion ante error "ya existe" al crear contratista.
    Ahora detecta la validacion, cierra el modal y selecciona el contratista existente.
  - Bug 3: _llenar_unspsc tenia time.sleep() — reemplazado con send_keys + wait_for_element.
  - Bug 4: self.driver.get() → self.navegar_a() (consistente con otros page objects).
  - Bug 5: Boton guardar necesita JS click (tiene onclick) → esperar_y_click_js_xpath.
  - Bug 6: Artefactos de debug eliminados (save_screenshot, time.sleep).
  - Bug 7: Import 'By' sin usar eliminado.
"""
from seleniumbase import Driver
from pages.base_page import BasePage, DEFAULT_TIMEOUT, LONG_TIMEOUT, SAVE_TIMEOUT
from utils.logger import log_step as print
from utils.mappers import contains_invalid_chars, normalizar_tipo_contrato, obtener_dias


class InformacionGeneralPage(BasePage):
    """Gestiona el llenado de informacion general del proceso en SECOP II."""

    def __init__(self, sb: Driver):
        self.sb = sb

    # === SELECTORES PRINCIPALES ===
    INPUT_DESCRIPCION     = "//textarea[@id = 'txaDossierDescription']"
    INPUT_UNSPSC_ID       = "divCategorizationRow_incDossierCategorizationUnspscMain_0_Lookup_LookupText"
    RADIO_PUBLICIDAD_SI   = "rdbgOnlyPublicityOptions_0"
    INPUT_PROVEEDOR       = "txtAwardedCompanyText"
    SELECT_TIPO_CONTRATO  = "selTypeOfContractSelect"
    INPUT_DURACION        = "//input[@id = 'nbxDurationGen']"
    INPUT_FECHA_TERMINACION = "//input[@id = 'dtmbContractEndDateGen_txt']"
    # Boton "Siguiente Paso" (>) — navega a Configuracion y guarda implicitamente.
    # NO usar btnSaveProcedureTop ("Guardar") porque solo guarda sin avanzar.
    BTN_SIGUIENTE_PASO    = "tbToolBarPlaceHolder_btnNextStepButton"

    # === SELECTORES CONTRATO MARCO ===
    RADIO_RELACION_OTROS_SI = "rdbgRelatedToAnotherDossierP2Gen_0"
    LINK_AGREGAR_PROCESOS   = "lnkAddRelatedDossiers"
    FRAME_RELACION_PROCESOS = "RelatedDossierModal_iframe"
    INPUT_BUSQUEDA_PROCESO  = "txtInputText"
    BTN_BUSCAR_PROCESO      = "btnSearch"
    CHECK_RESULTADO         = "chkSelCheck3P3Gen_0"
    BTN_CONFIRMAR_PROCESO   = "btnConfirm2Gen"

    # === SELECTORES CREAR CONTRATISTA ===
    BTN_BUSCAR_CONTRATISTA      = "btnAwardedCompanyButton"
    FRAME_SELECCION_CONTRATISTA = "AwardedCompanySelection_iframe"
    BTN_CREAR_CONTRATISTA       = "btnCreateCompanyButton"
    FRAME_CREAR_CONTRATISTA     = "CreateCompanyModal_iframe"
    SELECT_TIPO_DOCUMENTO       = "selTypeOfDocument"
    INPUT_NUMERO_ID             = "txtCompanyVat"
    INPUT_NOMBRE_PROVEEDOR      = "txtCompanyName"
    SELECT_TIPO_PERSONA         = "selCompanyType"
    INPUT_LOCALIZACION          = "txtLocationElement1Text"
    INPUT_EMAIL                 = "txtEmail"
    BTN_CREAR                   = "frmMainForm_tblContent_trButtons_tdCell1_tbToolBarPlaceHolder_btnCreateButton"
    LNK_SELECCIONAR             = "lnkSelectItemP3Gen_0"

    # Busqueda en el frame de seleccion (AwardedCompanySelection_iframe)
    # Usado para buscar proveedor por NIT antes de crear y como recovery tras error
    INPUT_BUSQUEDA_PROVEEDOR = "txtAllWords2SearchGen"
    BTN_BUSCAR_PROVEEDOR     = "btnSearchButton"

    # Boton Cerrar del modal de creacion — ID exacto del HTML de SECOP II
    # onclick="javascript:CloseModalSupportView();" → requiere JS click
    BTN_CERRAR_CREAR = "frmMainForm_tblContent_trToolBar_tdCell1_tbToolBar_btnClosePopUp"

    # XPath del resultado en el autocomplete de proveedor
    # CRITICO: click en <span> interno (funciones.py:228), NO en <li>
    XPATH_AC_PROVEEDOR = "//div[@class='ac_results']//li[1]//span[1]//span"

    # XPath para detectar CUALQUIER error de validacion en el modal de creacion.
    # El label "Errores de validación:" aparece tanto ante "ya existe" como ante
    # campos obligatorios faltantes (email, ubicacion, tipo persona, etc.)
    XPATH_ERRORES_VALIDACION = "//label[contains(text(),'Errores de validación')]"

    # === SELECTORES ACUERDOS COMERCIALES ===
    RADIO_ACUERDOS_SI   = "rdbgCommercialAgreementRadio_0"
    BTN_AGREGAR_ACUERDO = "btnAddCommercialAgreementGen"
    FRAME_ACUERDOS      = "AddCommercialAgreementModal_iframe"
    BTN_CONFIRMAR_ACUERDO = "btnConfirmGen"
    BTN_UPLOAD_DOC      = "btnUploadDocumentGen"

    # === MAPEO TIPO PERSONA ===
    OPCIONES_TIPO_PERSONA = {
        ("persona jurídica", "docu.de identificación extranj"): "Persona Juridica Extranjera Sin Domicilios",
        ("persona natural",  "docu.de identificación extranj"): "Persona Natural Extranjera",
        ("persona jurídica", "nit"):                            "Sociedad por acciones simplificada",
        ("persona natural",  "nit"):                            "Persona Natural colombiana",
        ("persona natural",  "cédula de ciudadanía"):           "Persona Natural colombiana",
    }

    # =========================================================================
    # METODO PRINCIPAL
    # =========================================================================

    def llenar_informacion_general(self, datos, ciudades_codigos=None):
        """
        Orquesta el llenado completo de informacion general.
        Retorna la URL del proceso guardado. SIN escrituras a Google Sheets.

        Original: funciones.py:127-381 — informacion_general(params)
        """
        url_proceso_1         = datos['estado_proceso_1']
        descripcion           = datos['objeto_descripcion']
        codigo                = datos['codigo']
        tipo_contrato         = datos['tipo_contrato']
        acuerdos_comerciales  = datos['acuerdos_comerciales']
        fecha_inicio          = datos['fecha_inicio']
        fecha_fin             = datos['fecha_fin']
        documento_proveedor   = datos['documento_proveedor']
        nombre_proveedor      = datos['nombre_proveedor']
        tipo_proveedor        = datos['tipo_proveedor']
        tipo_identificador    = datos['tipo_identificador']
        localizacion          = datos['localizacion']
        email                 = datos['email']
        contrato_marco        = datos['contrato_marco']

        print("Llenando informacion general del proceso...")

        # Validaciones previas
        if contains_invalid_chars(descripcion):
            raise Exception("El objeto del contrato tiene caracteres especiales")
        if codigo == '':
            raise Exception("El código es incorrecto o no existe")

        tipo_contrato_normalizado = normalizar_tipo_contrato(tipo_contrato)

        # Navegar al proceso (Bug 4 fix: navegar_a en lugar de driver.get)
        self.navegar_a(url_proceso_1)

        # 1. Descripcion
        self._llenar_descripcion(descripcion)

        # 2. Contrato marco si aplica
        if contrato_marco not in ['', 'No Aplica']:
            self._configurar_contrato_marco(contrato_marco)

        # 3. Clasificacion UNSPSC
        self._llenar_unspsc(codigo)

        # 4. Proveedor adjudicado
        self._configurar_proveedor(
            documento_proveedor, nombre_proveedor, tipo_proveedor,
            tipo_identificador, localizacion, email, ciudades_codigos
        )

        # 5. Tipo de contrato y justificacion
        self._seleccionar_tipo_contrato(tipo_contrato_normalizado)

        # 6. Duracion y fechas
        self._configurar_duracion_y_fechas(fecha_inicio, fecha_fin)

        # 7. Acuerdos comerciales si aplica
        if acuerdos_comerciales != "":
            self._configurar_acuerdos_comerciales(acuerdos_comerciales)

        # 8. Guardar
        return self._guardar_y_obtener_url()

    # =========================================================================
    # METODOS PRIVADOS
    # =========================================================================

    def _llenar_descripcion(self, descripcion):
        """Lineas 171-174: Llena el campo de descripcion."""
        self.esperar_y_escribir(self.INPUT_DESCRIPCION, descripcion)

    def _llenar_unspsc(self, codigo):
        """
        Llena y selecciona el codigo UNSPSC.

        Problema resuelto — comportamiento alternado (una vez si / una vez no):
          El XPath //span[contains(text(), '{codigo}')] era demasiado amplio:
          en ejecuciones donde el campo ya tenia el codigo (valor cargado de
          una ejecucion previa), el primer <span> que matcheaba era el texto
          ya visible en la pagina, NO el resultado del dropdown ac_results.
          Hacer click en ese span no disparaba la seleccion del autocomplete,
          dejando el DOM con el valor pero sin la actualizacion visual/funcional.

        Fixes aplicados:
          1. Scroll al campo (puede estar fuera del viewport en la carga inicial).
          2. Skip si el campo ya contiene el codigo correcto (evita doble fill).
          3. XPath acotado a //div[@class='ac_results'] — solo matchea el dropdown.
        """
        # 1. Scroll al campo (evita que wait_for_element_visible falle por viewport)
        self.sb.wait_for_element_present(f"#{self.INPUT_UNSPSC_ID}")
        el = self.driver.find_element("id", self.INPUT_UNSPSC_ID)
        self.scroll_a_elemento(el)

        # 2. Skip si el codigo ya esta correctamente seleccionado
        valor_actual = el.get_attribute("value") or ""
        if codigo in valor_actual:
            print(f"  UNSPSC ya tiene el valor correcto ('{valor_actual}'). Saltando.")
            return

        # 3. Limpiar y disparar el autocomplete con send_keys
        self.sb.wait_for_element_visible(f"#{self.INPUT_UNSPSC_ID}", timeout=DEFAULT_TIMEOUT)
        self.sb.click(f"#{self.INPUT_UNSPSC_ID}")
        self.driver.find_element("id", self.INPUT_UNSPSC_ID).clear()
        self.sb.send_keys(f"#{self.INPUT_UNSPSC_ID}", codigo)

        # 4. XPath acotado al dropdown ac_results (no al texto ya visible en pagina)
        xpath_resultado = f"//div[contains(@class,'ac_results')]//span[contains(text(), '{codigo}')]"
        try:
            self.sb.wait_for_element_visible(xpath_resultado, timeout=15)
            self.sb.click(xpath_resultado)
        except Exception:
            raise Exception("El código es incorrecto o no existe")

    def _configurar_contrato_marco(self, contrato_marco):
        """Lineas 175-201: Configura la relacion con otro proceso (contrato marco)."""
        print(f"Configurando contrato marco: {contrato_marco}...")

        self.esperar_y_click_por_id(self.RADIO_RELACION_OTROS_SI)
        self.esperar_y_click_por_id(self.LINK_AGREGAR_PROCESOS)

        self.cambiar_a_frame(self.FRAME_RELACION_PROCESOS)
        self.esperar_y_escribir_por_id(self.INPUT_BUSQUEDA_PROCESO, contrato_marco, timeout=LONG_TIMEOUT)
        self.esperar_y_click_por_id(self.BTN_BUSCAR_PROCESO,   timeout=LONG_TIMEOUT)
        self.esperar_y_click_por_id(self.CHECK_RESULTADO,      timeout=LONG_TIMEOUT)
        self.esperar_y_click_por_id(self.BTN_CONFIRMAR_PROCESO, timeout=LONG_TIMEOUT)
        self.volver_contenido_principal()

    def _configurar_proveedor(self, documento, nombre, tipo_proveedor,
                               tipo_identificador, localizacion, email,
                               ciudades_codigos):
        """
        Lineas 215-315: Configura el proveedor adjudicado.

        Bug 1 fix: el autocomplete de SECOP II requiere click en el <span> interno
        del resultado (//div[@class='ac_results']//li[1]//span[1]//span).
        Hacer click en el <li> no registra la seleccion.

        Flujo:
          - Intento 1: autocomplete con send_keys + click en span interno
          - Fallback: flujo de creacion/seleccion de contratista en modal
        """
        print("Configurando proveedor adjudicado...")

        self.esperar_y_click_por_id(self.RADIO_PUBLICIDAD_SI)

        # --- Autocomplete proveedor (XPath exacto del original funciones.py:228) ---
        try:
            self.sb.wait_for_element_visible(f"#{self.INPUT_PROVEEDOR}", timeout=DEFAULT_TIMEOUT)
            self.sb.click(f"#{self.INPUT_PROVEEDOR}")
            self.driver.find_element("id", self.INPUT_PROVEEDOR).clear()
            self.sb.send_keys(f"#{self.INPUT_PROVEEDOR}", documento)

            # Esperar el dropdown ac_results y hacer click en el span interno
            self.sb.wait_for_element_visible(self.XPATH_AC_PROVEEDOR, timeout=8)
            self.sb.click(self.XPATH_AC_PROVEEDOR)
            print("Proveedor seleccionado via autocomplete.")
            return
        except Exception:
            pass

        # --- Fallback: abrir modal de busqueda/creacion de contratista ---
        self._crear_contratista_en_modal(
            documento, nombre, tipo_proveedor,
            tipo_identificador, localizacion, email, ciudades_codigos
        )

    def _crear_contratista_en_modal(self, documento, nombre, tipo_proveedor,
                                     tipo_identificador, localizacion, email,
                                     ciudades_codigos):
        """
        Crea o selecciona un contratista dentro del modal iframe.

        Estrategia "Search-First":
          1. Abre AwardedCompanySelection_iframe y busca por NIT.
          2. Si aparece lnkSelectItemP3Gen_0 → selecciona directamente (sin crear).
          3. Si no aparece → abre CreateCompanyModal_iframe y llena el formulario.
          4. Tras hacer click en Crear, verifica si hay errores de validacion
             (label "Errores de validación:" — cubre tanto "ya existe" como campos
             obligatorios faltantes).
          5. Si hay error → JS click en BTN_CERRAR_CREAR (ID exacto del HTML) →
             vuelve al frame de seleccion → busca por NIT → selecciona existente.
          6. Si no hay error → selecciona el contratista recien creado.

        Referencia HTML del boton Cerrar:
          <input id="frmMainForm_...btnClosePopUp" onclick="CloseModalSupportView();">
        Referencia HTML de busqueda:
          <input id="txtAllWords2SearchGen"> + <input id="btnSearchButton">
        """
        print("Entrando al modal de busqueda/creacion de contratista...")
        try:
            # ----------------------------------------------------------------
            # 1. Abrir frame de seleccion y buscar por NIT primero
            # ----------------------------------------------------------------
            self.esperar_y_click_por_id(self.BTN_BUSCAR_CONTRATISTA, timeout=LONG_TIMEOUT)
            self.cambiar_a_frame(self.FRAME_SELECCION_CONTRATISTA)

            print(f"  Buscando proveedor por NIT: {documento}...")
            self.esperar_y_escribir_por_id(
                self.INPUT_BUSQUEDA_PROVEEDOR, documento, timeout=LONG_TIMEOUT
            )
            # btnSearchButton tiene onclick=getAction(...) → requiere JS click
            self.esperar_y_click_js(self.BTN_BUSCAR_PROVEEDOR, timeout=LONG_TIMEOUT)

            # ----------------------------------------------------------------
            # 2. Si hay resultado, seleccionar directamente (sin crear)
            # ----------------------------------------------------------------
            if not self.not_exist_element(f"#{self.LNK_SELECCIONAR}", timeout=LONG_TIMEOUT):
                print("  Proveedor encontrado en busqueda. Seleccionando directamente...")
                self.esperar_y_click_por_id(self.LNK_SELECCIONAR, timeout=LONG_TIMEOUT)
                self.volver_contenido_principal()
                return

            # ----------------------------------------------------------------
            # 3. No encontrado → abrir formulario de creacion
            # ----------------------------------------------------------------
            print("  Proveedor no encontrado. Procediendo a crear nuevo...")
            self.esperar_y_click_js(self.BTN_CREAR_CONTRATISTA, timeout=LONG_TIMEOUT)

            # CreateCompanyModal_iframe es HERMANO de AwardedCompanySelection_iframe
            # (ambos estan bajo default_content, NO anidados)
            self.volver_contenido_principal()
            self.cambiar_a_frame(self.FRAME_CREAR_CONTRATISTA)

            # Tipo de documento
            if tipo_identificador == "Docu.de identificación Extranj":
                self.seleccionar_dropdown(self.SELECT_TIPO_DOCUMENTO, "Otro")
            elif tipo_identificador == "Cédula de Ciudadanía":
                self.seleccionar_dropdown(self.SELECT_TIPO_DOCUMENTO, "Cédula de Ciudadanía")
            else:
                self.seleccionar_dropdown(self.SELECT_TIPO_DOCUMENTO, "NIT")

            # Datos de identificacion
            self.esperar_y_escribir_por_id(self.INPUT_NUMERO_ID,        documento)
            self.esperar_y_escribir_por_id(self.INPUT_NOMBRE_PROVEEDOR, nombre)

            # Tipo de persona
            opcion = self.OPCIONES_TIPO_PERSONA.get(
                (tipo_proveedor.lower(), tipo_identificador.lower())
            )
            if opcion:
                self.seleccionar_dropdown(self.SELECT_TIPO_PERSONA, opcion)

            # Localizacion con autocomplete
            codigo_busqueda = ''
            if ciudades_codigos:
                if tipo_identificador == 'Docu.de identificación Extranj':
                    codigo_busqueda = ciudades_codigos.get('MEDELLIN', '')
                else:
                    codigo_busqueda = ciudades_codigos.get(localizacion, '')
            self.escribir_y_seleccionar_primer_li(self.INPUT_LOCALIZACION, codigo_busqueda)

            # Correo electronico (campo Vortal — requiere inyeccion JS para disparar eventos)
            correo_dummy = "correo_dummy@ejemplo.com"
            try:
                self.sb.wait_for_element_visible(f"#{self.INPUT_EMAIL}", timeout=5)
                self.sb.execute_script(f"""
                    var el = document.getElementById('{self.INPUT_EMAIL}');
                    if(el) {{
                        el.value = '{correo_dummy}';
                        el.dispatchEvent(new Event('input',  {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('blur',   {{ bubbles: true }}));
                    }}
                """)
                print("  [OK] Correo dummy inyectado via JS")
            except Exception as e:
                print(f"  [AVISO] No se pudo inyectar el correo: {e}")

            # ----------------------------------------------------------------
            # 4. Intentar crear
            # ----------------------------------------------------------------
            self.esperar_y_click_js(self.BTN_CREAR, timeout=LONG_TIMEOUT)

            # ----------------------------------------------------------------
            # 5. Verificar errores de validacion
            #    XPATH_ERRORES_VALIDACION detecta el label "Errores de validación:"
            #    que aparece ante CUALQUIER error: "ya existe", campos obligatorios, etc.
            # ----------------------------------------------------------------
            if not self.not_exist_element(self.XPATH_ERRORES_VALIDACION, timeout=5):
                print("  Error de validacion detectado. Cerrando modal de creacion...")
                # Cerrar con el boton exacto del HTML (onclick=CloseModalSupportView)
                self.esperar_y_click_js(self.BTN_CERRAR_CREAR, timeout=LONG_TIMEOUT)

                # Volver al frame de seleccion y buscar por NIT
                self.volver_contenido_principal()
                self.cambiar_a_frame(self.FRAME_SELECCION_CONTRATISTA)
                print(f"  Buscando proveedor existente por NIT: {documento}...")
                self.esperar_y_escribir_por_id(
                    self.INPUT_BUSQUEDA_PROVEEDOR, documento, timeout=LONG_TIMEOUT
                )
                self.esperar_y_click_js(self.BTN_BUSCAR_PROVEEDOR, timeout=LONG_TIMEOUT)
                self.esperar_y_click_por_id(self.LNK_SELECCIONAR, timeout=30)
                self.volver_contenido_principal()
                return

            # ----------------------------------------------------------------
            # 6. Creacion exitosa → seleccionar en el frame de seleccion
            # ----------------------------------------------------------------
            self.volver_contenido_principal()
            self.cambiar_a_frame(self.FRAME_SELECCION_CONTRATISTA)
            self.esperar_y_click_por_id(self.LNK_SELECCIONAR, timeout=30)
            self.volver_contenido_principal()

        except Exception as e:
            raise Exception(f"Error al crear/seleccionar el contratista: {str(e)}")

    def _seleccionar_tipo_contrato(self, tipo_contrato_normalizado):
        """Lineas 318-322: Selecciona tipo de contrato y justificacion."""
        self.seleccionar_dropdown(self.SELECT_TIPO_CONTRATO,              tipo_contrato_normalizado)
        self.seleccionar_dropdown("selJustificationTypeOfContractSelected", "Regla aplicable")

    def _configurar_duracion_y_fechas(self, fecha_inicio, fecha_fin):
        """Lineas 324-331: Configura duracion y fecha de terminacion."""
        duracion = obtener_dias(fecha_inicio, fecha_fin)
        self.esperar_y_escribir(self.INPUT_DURACION,          duracion)
        self.esperar_y_escribir(self.INPUT_FECHA_TERMINACION, fecha_fin + " 00:00")
        # Click en duracion para quitar foco de la fecha (lineas 330-331)
        self.esperar_y_click(self.INPUT_DURACION)

    def _configurar_acuerdos_comerciales(self, acuerdos_comerciales):
        """Lineas 332-361: Configura los acuerdos comerciales."""
        print(f"Configurando acuerdos comerciales: {acuerdos_comerciales}...")

        self.ejecutar_js("window.scrollTo(0, 3000)")
        self.esperar_y_click_por_id(self.RADIO_ACUERDOS_SI)
        self.esperar_y_click_por_id(self.BTN_AGREGAR_ACUERDO)

        self.cambiar_a_frame(self.FRAME_ACUERDOS)

        xpath_check_pais = f"//tbody/tr/td[contains(., '{acuerdos_comerciales}')]/preceding-sibling::td/input"
        self.esperar_y_click(xpath_check_pais, timeout=LONG_TIMEOUT)
        self.esperar_y_click_por_id(self.BTN_CONFIRMAR_ACUERDO)

        self.volver_contenido_principal()
        self.esperar_y_click_por_id(self.BTN_UPLOAD_DOC)

    def _guardar_y_obtener_url(self):
        """
        Avanza al siguiente paso (Configuracion) haciendo click en el boton ">".

        Por que BTN_SIGUIENTE_PASO y no BTN_GUARDAR:
          - "Guardar" solo persiste la informacion general en el paso actual.
          - "Siguiente Paso" (>) guarda Y navega al paso Configuracion.
          - La URL resultante es la de Configuracion y se almacena como Proceso 2,
            sirviendo como punto de entrada para el paso siguiente.

        El boton tiene onclick=postForm(...) → requiere JS click.
        Tras el click no hay mensaje de exito — la URL cambia directamente.
        """
        url_antes = self.url_actual
        self.esperar_y_click_js(self.BTN_SIGUIENTE_PASO, timeout=LONG_TIMEOUT)
        nueva_url = self.esperar_cambio_url(url_antes, timeout=SAVE_TIMEOUT)
        print(f"Informacion general completada. URL Proceso 2: {nueva_url}")
        return nueva_url
