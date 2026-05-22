import os
from seleniumbase import SB
from data.google_sheets_manager import GoogleSheetsConnection, ContratosRepository, ConfigRepository
from datetime import datetime
from utils.execution_context import ExecutionContext
from config.settings import (
    USER_GT, PASS_GT, DOWNLOAD_DIR, 
    BD_NAME, 
    WORKSHEET_CONTRACTS_NAME, 
    NOMBRE_ESTACION, 
    CREDENCIALES_JSON, 
    ONBASE_URL, 
    ONBASE_USER, 
    ONBASE_PASSWORD, 
    WORKSHEET_DEPTOS_NAME,
    HEADLESS_MODE
)

from pages.login_page import LoginPage
from pages.contract_page import ContractPage
from pages.controler_page import ControlerPage
from pages.budget_page import BudgetPage
from pages.budget_link_page import BudgetLinkPage
from pages.budget_register_page import BudgetRegisterPage
from pages.additional_dates_page import AdditionalDatesPage
from pages.file_reported_page import FileReportedPage
from pages.onbase_page import OnBasePage
from utils.mappers import (
    ajustar_rubro, 
    formatear_fecha_gt, 
    homologar_archivo_a_tipologia, 
    obtener_malla_documental, 
    obtener_rubros_unicos_por_contrato,
    construir_diccionario_homologacion,
    construir_datos_contratista,
    construir_datos_formulario
)

class OrquestadorRPA:
    """Servicio puro de procesamiento de contratos."""
    
    def __init__(self):
        print("🔌 Inicializando conexiones a bases de datos...")
        conexion = GoogleSheetsConnection(CREDENCIALES_JSON, BD_NAME)
        self.db_contratos = ContratosRepository(conexion.document, WORKSHEET_CONTRACTS_NAME)
        self.config_db = ConfigRepository(conexion.document)

    def ejecutar_flujo_maestro_cascada(self):
        """Orquesta el procesamiento End-to-End de todos los contratos pendientes."""
        
        # 1. Registros pendientes con lectura optimizada en RAM
        registros = self.db_contratos.obtener_registros_pendientes(NOMBRE_ESTACION)
        print(f"\n🚀 Iniciando Lote: {len(registros)} contratos pendientes para la estación {NOMBRE_ESTACION}")

        if not registros:
            print("✅ No hay tareas pendientes. Finalizando ejecución exitosamente.")
            return    

        # 2. CARGA CONFIGURACIONES EN CACHÉ
        datos_crudos_deptos = self.config_db.obtener_datos_maestros(WORKSHEET_DEPTOS_NAME)
        diccionario_deptos = construir_diccionario_homologacion(datos_crudos_deptos)
        
        # =========================================================
        # INICIO DEL CICLO DE VIDA DEL NAVEGADOR (ARQUITECTURA PURA)
        # =========================================================
        print("🌐 Levantando motor de automatización web...")

        #Activación de modo sin ventanas
        headless_mode = (HEADLESS_MODE == "1")

        if headless_mode:
            print("👻 Ejecutando en modo sin ventana (Headless)")
        else:
            print("🖥️ Ejecutando con interfaz gráfica visible")

        with SB(headless=headless_mode, window_size="1920,1080") as sb: 

            # Inicializar Page Objects inyectando el contexto de SeleniumBase (sb)
            login_page = LoginPage(sb)
            contract_page = ContractPage(sb)
            controler_page = ControlerPage(sb)
            budget_page = BudgetPage(sb)
            budget_link_page = BudgetLinkPage(sb)
            budget_register_page = BudgetRegisterPage(sb)
            additional_dates_page = AdditionalDatesPage(sb)
            file_reported_page = FileReportedPage(sb)
            onbase_page = OnBasePage(sb, DOWNLOAD_DIR)

            # Pipeline Principal
            for data in registros:
                ExecutionContext.clear()
                fila = data['_fila_excel']
                contrato_id = data['Número']
                observacion_actual = str(data.get('OBSERVACIONES', ''))

                print(f"\n=======================================================")
                print(f"⚙️ PROCESANDO CONTRATO: {contrato_id} (Fila Excel: {fila})")
                print(f"=======================================================")

                try:
                    # Actualizamos el estado para que, si falla aquí, sepamos exactamente por qué
                    ExecutionContext.set_step("Iniciando sesión y navegando al menú principal")
                    
                    login_page.verificar_o_iniciar_sesion(USER_GT, PASS_GT)

                    # ---------------------------------------------------------
                    # PROCESO 1: CREAR CONTRATO
                    # ---------------------------------------------------------
                    if data.get('PROCESO1') != 'REALIZADO':
                        print("\n>> PASO 1: Creación del Contrato")
                        
                        # MAPEO DE DATOS (Delegado a constructores)
                        contrato_num = str(data.get('Número', ''))
                        codigo_proyecto = str(data.get('Código del Proyecto', ''))
                        
                        lista_rubros = obtener_rubros_unicos_por_contrato(registros, contrato_id)
                        datos_contratista = construir_datos_contratista(data, diccionario_deptos)
                        datos_formulario = construir_datos_formulario(data, lista_rubros)
                        
                        # EJECUCIÓN DE INTERFAZ WEB (UI)
                        contract_page.navegar_a_crear_contrato()
                        contract_page.llenar_datos_basicos(contrato_num)
                        
                        if not contract_page.gestionar_contratista(datos_contratista):
                            raise Exception(f"Fallo en la gestión del contratista ID: {datos_contratista['identificacion']}")
                            
                        if not contract_page.seleccionar_proyecto(codigo_proyecto):
                            raise Exception(f"Fallo al encontrar o seleccionar el proyecto: {codigo_proyecto}")
                            
                        if not contract_page.diligenciar_formulario_principal_contrato(datos_formulario):
                            raise Exception("Fallo durante el diligenciamiento del formulario principal.")
                        
                        # ACTUALIZACIÓN DEL ESTADO EN BASE DE DATOS
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO1', 'REALIZADO')
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'FECHA PUBLICACION GT', fecha_hoy)
                        data['PROCESO1'] = 'REALIZADO'
                        data['FECHA PUBLICACION GT'] = fecha_hoy

                        # HOMOLOGACIÓN
                        self.db_contratos.homologar_proceso(contrato_id, 'PROCESO1', 'REALIZADO', registros)
                        self.db_contratos.homologar_proceso(contrato_id, 'FECHA PUBLICACION GT', fecha_hoy, registros)
                        
                    # ---------------------------------------------------------
                    # PROCESO 2: VINCULAR SUPERVISOR
                    # ---------------------------------------------------------
                    if data.get('PROCESO1') == 'REALIZADO' and data.get('PROCESO2') != 'REALIZADO':
                        print("\n>> PASO 2: Vincular Supervisor / Interventor")
                        
                        id_interventor = str(data.get('Interventor','')).strip()
                        tipo_vinculacion = str(data.get('Tipo', 'Interno')).strip().capitalize()

                        controler_page.navegar_a_vincular_interventor()

                        if not controler_page.consultar_y_continuar_contrato(contrato_id):
                            raise Exception(f"No se pudo encontrar el contrato {contrato_id} en el módulo de Interventoría.")
                        
                        controler_page.asociar_y_vincular_interventor(id_interventor, tipo_vinculacion)

                        self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO2', 'REALIZADO')
                        data['PROCESO2'] = 'REALIZADO'
                        self.db_contratos.homologar_proceso(contrato_id, 'PROCESO2', 'REALIZADO', registros)

                    # ---------------------------------------------------------
                    # PROCESO 3: DISPONIBILIDAD PRESUPUESTAL (CDP)
                    # ---------------------------------------------------------
                    if data.get('PROCESO2') == 'REALIZADO' and data.get('PROCESO3') != 'REALIZADO':
                        print("\n>> PASO 3: Disponibilidad Presupuestal")
                        
                        numero_cdp = str(data.get('Número de Disponibilidad Pptal:', '')).strip()
                        fecha_cdp = str(data.get('Fecha Disponibilidad Pptal', '')).strip()
                        valor_cdp = str(data.get('Valor Disponibilidad Ppat', '')).strip()
                        rubro_formateado = ajustar_rubro(str(data.get('Rubro Presupuestal', '')))

                        budget_page.navegar_a_gestion_cdp()
                        budget_page.configurar_periodo()

                        cdp_existe = budget_page.buscar_cdp(numero_cdp)

                        if cdp_existe:
                            budget_page.entrar_a_edicion_cdp(numero_cdp)
                            if not budget_page.seleccionar_rubro(rubro_formateado):
                                raise Exception(f"El rubro {rubro_formateado} no está disponible para el CDP {numero_cdp}.")
                            
                            if not budget_page.finalizar_vinculacion(valor_cdp):
                                raise Exception(f"Fallo al actualizar el valor del rubro {rubro_formateado} en el CDP {numero_cdp}.")
                        else:
                            budget_page.iniciar_creacion_cdp()
                            if not budget_page.seleccionar_rubro(rubro_formateado):
                                raise Exception(f"El rubro {rubro_formateado} no está disponible para crear el CDP {numero_cdp}.")
                            
                            if not budget_page.llenar_formulario_detalle_cdp(numero_cdp, fecha_cdp, valor_cdp):
                                raise Exception(f"Error al guardar la creación del nuevo CDP {numero_cdp}.")
                        
                        budget_link_page.navegar_a_vincular_cdp()

                        exito_vinculo = budget_link_page.vincular_disponibilidad_presupuestal(
                            num_contrato=contrato_id,
                            codigo_cdp=numero_cdp, 
                            valor_cdp=valor_cdp
                        )

                        if not exito_vinculo:
                            raise Exception(f"Fallo al vincular el CDP {numero_cdp} al contrato {contrato_id}.")
                        
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO3', 'REALIZADO')
                        data['PROCESO3'] = 'REALIZADO'

                    # ---------------------------------------------------------
                    # PROCESO 4: REGISTRO PRESUPUESTAL (RP)
                    # ---------------------------------------------------------
                    if data.get('PROCESO3') == 'REALIZADO' and data.get('PROCESO4') != 'REALIZADO':
                        print("\n>> PASO 4: Vinculación de Registro Presupuestal (RP)")
                        
                        numero_rp = str(data.get('Número Registro Pptal:', '')).strip()
                        fecha_rp_cruda = str(data.get('Fecha Registro Pptal:', '')).strip()
                        fecha_rp = formatear_fecha_gt(fecha_rp_cruda)
                        cdp_origen = str(data.get('Número de Disponibilidad Pptal:', '')).strip()
                        rubro_formateado = ajustar_rubro(str(data.get('Rubro Presupuestal', '')))

                        valor_rp = str(data.get('Valor RP', '')).strip()
                        if not valor_rp or valor_rp == '0':
                            valor_rp = str(data.get('Valor', '')).strip()

                        budget_register_page.navegar_a_vincular_rp()
                        
                        exito_rp = budget_register_page.vincular_registro_presupuestal(
                            num_contrato=contrato_id,
                            num_rp=numero_rp,
                            fecha_rp=fecha_rp,
                            cdp_asociado=cdp_origen,
                            total_bruto=valor_rp,
                            rubro=rubro_formateado
                        )
                        
                        if not exito_rp:
                            raise Exception(f"Fallo al vincular el RP {numero_rp} (CDP base: {cdp_origen}) al contrato {contrato_id}.")
                        
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO4', 'REALIZADO')
                        data['PROCESO4'] = 'REALIZADO'

                    # ---------------------------------------------------------
                    # PROCESO 5: REPORTE DE FECHAS
                    # ---------------------------------------------------------
                    if data.get('PROCESO4') == 'REALIZADO' and data.get('PROCESO5') != 'REALIZADO':
                        print("\n>> PASO 5: Reporte de Fechas")
                        
                        fecha_secop_cruda = str(data.get('Publicación Secop', '')).strip()
                        fecha_secop_real = formatear_fecha_gt(fecha_secop_cruda)

                        additional_dates_page.navegar_a_fechas_adicionales()

                        exito_fechas = additional_dates_page.vincular_fecha_secop(
                            num_contrato=contrato_id,
                            fecha_secop=fecha_secop_real
                        )

                        if not exito_fechas:
                            raise Exception(f'Fallo al vincular la fecha de SECOP al contrato {contrato_id}')
                        
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO5', 'REALIZADO')
                        data['PROCESO5'] = 'REALIZADO'
                        self.db_contratos.homologar_proceso(contrato_id, 'PROCESO5', 'REALIZADO', registros)

                    # ---------------------------------------------------------
                    # PROCESO 6: CARGA DE ANEXOS (ONBASE + GT)
                    # ---------------------------------------------------------
                    if data.get('PROCESO5') == 'REALIZADO' and data.get('PROCESO6') != 'REALIZADO':
                        print("\n>> PASO 6: Gestión Documental (OnBase -> Gestión Transparente)")
                        
                        grupo_compras = str(data.get('Grupo de Compras', '')).strip()
                        malla_documental = obtener_malla_documental(grupo_compras)
                        print(f"📋 Malla documental cargada para el Grupo: '{grupo_compras}'")

                        print(f"📥 Conectando con OnBase para el contrato {contrato_id}...")
                        onbase_page.autenticar_y_preparar(ONBASE_URL, ONBASE_USER, ONBASE_PASSWORD)
                        onbase_page.buscar_expediente(contrato_id)
                        
                        descarga_iniciada = onbase_page.seleccionar_y_descargar()

                        if not descarga_iniciada:
                            raise Exception(f'No se ha podido descargar correctamente los archivos para el contrato: {contrato_id}')
                        
                        archivos_limpios_rutas = onbase_page.procesar_descarga()
                        
                        cerrar_ventana_descargas = onbase_page.cerrar_ventana_descarga()

                        if not cerrar_ventana_descargas:
                            raise Exception(f'Error al cerrar la ventana de descargas para el contrato: {contrato_id}')
                        
                        onbase_page.cerrar_cesion()

                        if not archivos_limpios_rutas:
                            raise Exception(f"No se ha procesado correctamente los archivos para el contrato: {contrato_id}.")

                        print(f"📤 Conectando con Módulo de Anexos en Gestión Transparente...")
                        file_reported_page.navegar_a_cargue_registros()
                        
                        if not file_reported_page.consultar_contrato(contrato_id):
                            raise Exception(f"El contrato {contrato_id} no está disponible para anexar documentos.")

                        archivos_subidos_count = 0
                        archivos_fallidos = []

                        # 2. FILTRADO Y EJECUCIÓN
                        for ruta_archivo in archivos_limpios_rutas:
                            nombre_archivo = os.path.basename(ruta_archivo)
                            tipologia_gt = homologar_archivo_a_tipologia(nombre_archivo, malla_documental)

                            if tipologia_gt:
                                print(f"\n✅ Homologación de tipología realizada para: '{nombre_archivo}'")
                                
                                exito_subida = file_reported_page.anexar_documento(ruta_archivo, tipologia_gt)
                                
                                if not exito_subida:
                                    print(f"⚠️ Falló la subida del archivo '{nombre_archivo}'. Continuando con los demás...")
                                    archivos_fallidos.append(nombre_archivo)
                                else:
                                    archivos_subidos_count += 1
                            else:
                                print(f"⏭️ IGNORADO (No requerido en malla): '{nombre_archivo}'")

                        if archivos_subidos_count == 0:
                            mensaje_fatal = "Fallo Crítico: No se pudo adjuntar NINGÚN documento (malla vacía o fallaron todos)."
                            raise Exception(mensaje_fatal)
                            
                        elif len(archivos_fallidos) > 0:
                            mensaje_alerta = f"Carga parcial: Se subieron {archivos_subidos_count} documento(s), pero fallaron {len(archivos_fallidos)}"
                            print(f"⚠️ Atención: {mensaje_alerta}")
                            ExecutionContext.add_warning(mensaje_alerta)
                            
                            self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO6', 'REALIZADO')
                            data['PROCESO6'] = 'REALIZADO'
                            self.db_contratos.homologar_proceso(contrato_id, 'PROCESO6', 'REALIZADO', registros)
                            
                        else:
                            print("✅ Todos los documentos homologados fueron subidos con éxito.")
                            self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO6', 'REALIZADO')
                            data['PROCESO6'] = 'REALIZADO'
                            self.db_contratos.homologar_proceso(contrato_id, 'PROCESO6', 'REALIZADO', registros)

                    # ---------------------------------------------------------
                    # VÁLVULA 7: FINALIZAR REPORTE E INYECTAR URL
                    # ---------------------------------------------------------
                    if data.get('PROCESO6') == 'REALIZADO' and data.get('PROCESO7') == '':
                        print("\n>> PASO 7: Generar URL de Reporte Final")
                        url_final = "Publicado - Consultar en GT"
                        
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'PROCESO7', url_final)
                        data['PROCESO7'] = 'REALIZADO'

                    # ---------------------------------------------------------
                    # CHECKPOINT FINAL
                    # ---------------------------------------------------------
                    if data.get('PROCESO7') != '':
                        self.db_contratos.actualizar_celda_por_nombre(fila, 'EJECUTADO', 'SI')

                        alertas_guardadas = ExecutionContext.get_warnings()
                        
                        if alertas_guardadas:
                            print(f"\n⚠️ CONTRATO {contrato_id} COMPLETADO CON OBSERVACIONES.")

                            texto_observaciones = " | ".join(alertas_guardadas)
                            
                            nueva_obs = self.db_contratos.agregar_observacion_con_historial(
                                fila, observacion_actual, f"Completado con alertas: {texto_observaciones}"
                            )

                            data['OBSERVACIONES'] = nueva_obs

                            self.db_contratos.pintar_fila_semaforo(fila, 'amarillo')
                            
                        else:
                            print(f"\n🏆 ¡CONTRATO {contrato_id} COMPLETADO PERFECTAMENTE!")

                            nueva_obs = self.db_contratos.agregar_observacion_con_historial(
                                fila, observacion_actual, "Procesado exitosamente al 100%"
                            )

                            data['OBSERVACIONES'] = nueva_obs
                            self.db_contratos.pintar_fila_semaforo(fila, 'verde')

                except Exception as e:
                    # -----------------------------------------------------
                    # MANEJO DE ERRORES Aislando el Navegador
                    # -----------------------------------------------------
                    paso_actual = ExecutionContext.get_step()
                    ExecutionContext.set_color('rojo')

                    self.db_contratos.reportar_error_y_saltar(
                        fila=fila, 
                        mensaje_error=str(e), 
                        paso_fallido=paso_actual,
                        observacion_previa=observacion_actual
                    )
                    print(f"⚠️ Saltando al siguiente contrato del lote...")