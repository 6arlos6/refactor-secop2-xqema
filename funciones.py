# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.alert import Alert
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from tkinter import messagebox
import tkinter as tk
from functools import reduce
import globales
from datetime import datetime
import os
import pyperclip
import pyautogui
import unidecode
from datetime import datetime
import zipfile
import subprocess
import requests
import json
import pygetwindow as gw
import keyboard

# Clase para validar los cambios de las URL (para proceso 1)
class WaitForURLChange:
    def __init__(self, current_url):
        self.current_url = current_url

    def __call__(self, driver):
        return driver.current_url != self.current_url

#calculo de dias basado en la resta de las fechas
def obtener_dias(fecha_inicio, fecha_fin):
    date_time_str1 = fecha_inicio
    date_time_str2 = fecha_fin
    date_time_obj1 = datetime.strptime(date_time_str1, '%d/%m/%Y')
    date_time_obj2 = datetime.strptime(date_time_str2, '%d/%m/%Y')
    date_time_result = date_time_obj2 - date_time_obj1
    date_time_result_string = str(date_time_result).split(" ")[0]
    return date_time_result_string

#Se realiza el login en secop y se controla un estado global para no loguearse cuando ya se encuentre adentro.
def loguearse_secop(driver, timeout=5):
    try:
        #se redirecciona a SECOP II y se ingresan las credenciales
        driver.get(os.getenv('URL_LOGIN_SECOP'))
        time.sleep(2)
        campoUsuarioSecop2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "txtUserName"))
            )
        campoPassSecop2 = driver.find_element(By.ID,"txtPassword")
        botonLogin = driver.find_element(By.ID,"btnLoginButton")
        campoUsuarioSecop2.send_keys(os.getenv('USUARIO_SECOP'))
        campoPassSecop2.send_keys(os.getenv('PASS_SECOP'))
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.click(botonLogin).perform()
        time.sleep(3)
    except Exception as e:
        pass
    else:
        globales.logueado = True

#apartado de creación del proceso
def creacion_proceso(params_creacion_proceso):
    
    #Desempaquetado de parámetros
    driver = params_creacion_proceso['driver']
    sheet = params_creacion_proceso['sheet']
    indice = params_creacion_proceso['indice']
    nombre_proceso = params_creacion_proceso['nombre_proceso']
    unidad_contratacion = params_creacion_proceso['unidad_contratacion']
    try:
        time.sleep(3)
        driver.get(os.getenv('URL_SECOP'))
        time.sleep(4)
        botonCrearContratacion = driver.find_element(By.XPATH, "//input[@id = 'btnCreateProcedureButton12']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonCrearContratacion).click().perform()
        time.sleep(4)
        frameCrearProceso = driver.find_element(By.ID,"CreateProcedure_iframe" )
        driver.switch_to.frame(frameCrearProceso)
        campoNumeroProceso = driver.find_element(By.XPATH,"//input[@id = 'txtProcedureReference']")
        campoNombreProceso = driver.find_element(By.XPATH,"//input[@id = 'txtProcedureName']")
        campoUnidadContratacion = driver.find_element(By.XPATH, "//input[@id = 'txtBusinessOperationText']")
        campoNumeroProceso.send_keys(nombre_proceso)
        campoNombreProceso.send_keys(nombre_proceso)
        campoUnidadContratacion.send_keys(unidad_contratacion)
        time.sleep(3)
        xpath_unidad_contratacion = "//span[contains(text(), '{}')]".format(unidad_contratacion)
        busqueda_unidad_contratacion = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath_unidad_contratacion))
            )
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(busqueda_unidad_contratacion).click().perform()
        current_url = driver.current_url
        time.sleep(4)
        botonConfirmar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'btnSaveCurrentDossierTop']"))
            )
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonConfirmar).click().perform()
        # Usa WebDriverWait para esperar hasta que la URL cambie durante 10 segundos
        wait = WebDriverWait(driver, 20)
        wait.until(WaitForURLChange(current_url))
        new_url = driver.current_url
        url_proceso_1 = new_url
    except Exception as e:
        comentarioCreacionProceso = 'Error en la creación del proceso: {}'.format(e)
        cell_proceso_1='X{}'.format(indice+2)
        sheet.update(cell_proceso_1, comentarioCreacionProceso)
        globales.error = True
    else:
        globales.estado_proceso_1 = url_proceso_1
        cell_proceso_1='C{}'.format(indice+2)
        sheet.update(cell_proceso_1, url_proceso_1)

#apartado de configuracion general
def informacion_general(params_info_general):

    #Desempaquetado de parámetros
    driver = params_info_general['driver']
    sheet = params_info_general['sheet']
    indice = params_info_general['indice']
    url_proceso_1 = params_info_general['estado_proceso_1']
    descripcion = params_info_general['objeto_descripcion']
    codigo = params_info_general['codigo']
    tipo_contrato = params_info_general['tipo_contrato']
    acuerdos_comerciales = params_info_general['acuerdos_comerciales']
    fecha_inicio = params_info_general['fecha_inicio']
    fecha_fin = params_info_general['fecha_fin']
    documento_proveedor = params_info_general['documento_proveedor']
    nombre_proveedor = params_info_general['nombre_proveedor']
    tipo_proveedor = params_info_general['tipo_proveedor']
    tipo_identificador = params_info_general['tipo_identificador']
    localizacion = params_info_general['localizacion']
    cliente = params_info_general['cliente']
    email = params_info_general['email']
    contrato_marco = params_info_general['contrato_marco']

    wait = WebDriverWait(driver, 40)
    try:
        if contains_invalid_chars(descripcion):
            raise Exception("El objeto del contrato tiene caracteres especiales")
        diccionario_normalizacion_tipologia = { "Arrendamiento De Inmuebles" : "Arrendamiento de muebles",
                                                "Compraventa" : "Compraventa", 
                                                "Prestación De Servicios" : "Prestación de servicios",
                                                "Obra" : "Obra",
                                                "Contrato De Arrendamiento" : "Arrendamiento de muebles",
                                                "Contrato De Compraventa" : "Compraventa", 
                                                "Contrato de Prestación de Servicios" : "Prestación de servicios",
                                                "Contrato De Suministro" : "Suministro",
                                                "Suministro":"Suministro"}
        if tipo_contrato in diccionario_normalizacion_tipologia:
            tipo_contrato_normalizado = diccionario_normalizacion_tipologia[tipo_contrato]
        else:
            tipo_contrato_normalizado = "Otro"
        driver.get(url_proceso_1)
        valorDescripcion = descripcion
        valorUNSPSC = codigo
        if(valorUNSPSC == ''):
            raise Exception("El código es incorrecto o no existe")
        campoDescripcion = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//textarea[@id = 'txaDossierDescription']"))
                )    
        campoDescripcion.send_keys(valorDescripcion)
        if(contrato_marco not in ['', 'No Aplica']):
            radioRelacionOtrosProcesos = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "rdbgRelatedToAnotherDossierP2Gen_0"))
                ).click()
            linkAgregarProcesosRel = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "lnkAddRelatedDossiers"))
                ).click()
            frame_relacion_procesos = WebDriverWait(driver, 20).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "RelatedDossierModal_iframe"))
                )
            campo_busqueda = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "txtInputText"))
                )
            campo_busqueda.send_keys(contrato_marco)
            time.sleep(2)
            boton_buscar = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "btnSearch"))
                ).click()
            time.sleep(2)
            boton_resultado = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "chkSelCheck3P3Gen_0"))
                ).click()
            time.sleep(2)
            boton_confirmar = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "btnConfirm2Gen"))
                ).click()    
            driver.switch_to.default_content()    
        campoUNSPSC = driver.find_element(By.ID, "divCategorizationRow_incDossierCategorizationUnspscMain_0_Lookup_LookupText")
        campoUNSPSC.clear()
        time.sleep(2)
        campoUNSPSC.send_keys(valorUNSPSC)
        time.sleep(3)
        try:
            listaUNSPSC = driver.find_element(By.XPATH,"//span[contains(text(), '{}')]".format(valorUNSPSC))
        except:
            raise Exception("El código es incorrecto o no existe")
        time.sleep(3)
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(listaUNSPSC).click().perform()
        time.sleep(3)
        #--------Ajuste para publicidad del proces---------------------------#
        radio_publicidad_proceso = driver.find_element(By.ID, "rdbgOnlyPublicityOptions_0") #Selecciona la opción SI
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(radio_publicidad_proceso).click().perform()
        campo_informacion_proveedor_adjudicado = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "txtAwardedCompanyText"))
                )
        campo_informacion_proveedor_adjudicado.clear()
        time.sleep(2)
        campo_informacion_proveedor_adjudicado.send_keys(documento_proveedor)
        time.sleep(3)
        try:
            primer_resultado = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='ac_results']//li[1]//span[1]//span"))
            ).click()
            time.sleep(3)
        except:
            try:
                boton_buscar_contratista = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "btnAwardedCompanyButton"))
                ).click()
                frame_creacion_contratista = WebDriverWait(driver, 20).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "AwardedCompanySelection_iframe"))
                ) 
                boton_crear_contratista = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "btnCreateCompanyButton"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", boton_crear_contratista)
                time.sleep(2)
                boton_crear_contratista.click()
                driver.switch_to.default_content()
                frame_formulario_datos_contratista = WebDriverWait(driver, 20).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "CreateCompanyModal_iframe"))
                )
                select_elemento = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "selTypeOfDocument"))
                )
                select_identificador_entidad  =  Select(select_elemento)
                
                if (tipo_identificador == "Docu.de identificación Extranj"):
                    select_identificador_entidad.select_by_visible_text("Otro")
                elif (tipo_identificador == "Cédula de Ciudadanía"):
                    select_identificador_entidad.select_by_visible_text("Cédula de Ciudadanía")
                else:
                    select_identificador_entidad.select_by_visible_text("NIT")

                campo_numero_identificacion = driver.find_element(By.ID, "txtCompanyVat")
                campo_numero_identificacion.send_keys(documento_proveedor)
                campo_nombre_proveedor = driver.find_element(By.ID, "txtCompanyName")
                campo_nombre_proveedor.send_keys(nombre_proveedor)
                select_elemento = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "selCompanyType"))
                )
                select_tipo_persona  =  Select(select_elemento)

                opciones = {
                    ("persona jurídica", "docu.de identificación extranj"): "Persona Juridica Extranjera Sin Domicilios",
                    ("persona natural", "docu.de identificación extranj"): "Persona Natural Extranjera",
                    ("persona jurídica", "nit"): "Sociedad por acciones simplificada",
                    ("persona natural", "nit"): "Persona Natural colombiana",
                    ("persona natural", "cédula de ciudadanía"): "Persona Natural colombiana"
                }

                # Selección basada en mapeo
                opcion_seleccionada = opciones.get((tipo_proveedor.lower(), tipo_identificador.lower()))

                if opcion_seleccionada:
                    select_tipo_persona.select_by_visible_text(opcion_seleccionada)
                    
                campo_localizacion = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "txtLocationElement1Text"))
                )
                campo_localizacion.clear()
                time.sleep(2)
                data_ciudades_codigos = cliente.open(os.getenv('HOJA_DATOS')).worksheet("DATA_CIUDADES_CODIGOS").get_all_values()
                ciudades_codigos = {row[0]: row[1] for row in data_ciudades_codigos[1:]}
                if(tipo_identificador == 'Docu.de identificación Extranj'):
                    codigo_busqueda = ciudades_codigos.get('MEDELLIN', '')  
                else:   
                    codigo_busqueda = ciudades_codigos.get(localizacion, '')
                campo_localizacion.send_keys(codigo_busqueda)
                primer_resultado = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@class='ac_results']//li[1]//span[1]//span"))
                ).click()
                campo_email = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "txtEmail"))
                )
                campo_email.send_keys(email)
                boton_crear = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "frmMainForm_tblContent_trButtons_tdCell1_tbToolBarPlaceHolder_btnCreateButton"))
                ).click()
                driver.switch_to.default_content()
                frame_creacion_contratista = WebDriverWait(driver, 30).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "AwardedCompanySelection_iframe"))
                )
                boton_seleccionar = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.ID, "lnkSelectItemP3Gen_0"))
                ).click()
                driver.switch_to.default_content()
            except Exception as e:
                raise Exception("Error al crear el contratista:{}".format(str(e)))
        
        #-------Fin del ajuste para publicidad del proceso-------------------#
        selectTipoContrato  =  Select(driver.find_element(By.ID,'selTypeOfContractSelect'))
        selectTipoContrato.select_by_visible_text(tipo_contrato_normalizado)
        time.sleep(3)
        selectJustificacion  =  Select(driver.find_element(By.XPATH,"//select[@id = 'selJustificationTypeOfContractSelected']"))
        selectJustificacion.select_by_visible_text("Regla aplicable")
        time.sleep(3)
        campoDuracionContrato = driver.find_element(By.XPATH, "//input[@id = 'nbxDurationGen']")
        valorDuracion = obtener_dias(fecha_inicio, fecha_fin)
        campoDuracionContrato.send_keys(valorDuracion)
        campoFechaTerminacionContrato = driver.find_element(By.XPATH, "//input[@id = 'dtmbContractEndDateGen_txt']")
        valorFechaTerminacionContrato = fecha_fin + " 00:00"
        campoFechaTerminacionContrato.send_keys(valorFechaTerminacionContrato)
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(campoDuracionContrato).click().perform()
        if(acuerdos_comerciales != ""):
            driver.execute_script("window.scrollTo(0, 3000)")
            radio_acuerdos_si = driver.find_element(By.ID, "rdbgCommercialAgreementRadio_0")
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(radio_acuerdos_si).click().perform()
            time.sleep(2)
            boton_agregar_acuerdo = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnAddCommercialAgreementGen"))
                )
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(boton_agregar_acuerdo).click().perform()
            time.sleep(2)
            xpath_check_pais = "//tbody/tr/td[contains(., '{}')]/preceding-sibling::td/input".format(acuerdos_comerciales)
            frame_acuerdos = driver.find_element(By.ID, "AddCommercialAgreementModal_iframe")
            driver.switch_to.frame(frame_acuerdos)
            check_seleccionar_acuerdo = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, xpath_check_pais))
                )
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(check_seleccionar_acuerdo).click().perform()
            boton_agregar = driver.find_element(By.ID, "btnConfirmGen")
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(boton_agregar).click().perform()
            time.sleep(3)
            driver.switch_to.default_content()
            btn_upload_doc = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnUploadDocumentGen"))
                )
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(btn_upload_doc).click().perform()
        botonGuardarProceso2 = driver.find_element(By.XPATH, "//input[@id = 'tbToolBarPlaceHolder_btnSaveProcedureTop']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonGuardarProceso2).click().perform()
        tag_errores_validacion = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Proceso guardado con éxito')]")))
        time.sleep(5)
        url_proceso_2 = driver.current_url
    except Exception as e:
        if(str(e) == "El código es incorrecto o no existe" or
            str(e) == "El objeto del contrato tiene caracteres especiales" or
            "Error al crear el contratista" in str(e)):
            comentarioInfoGeneral = str(e)
        else:
            comentarioInfoGeneral = 'Error al ingresar información general del contrato: '.format(str(e))
        cell_proceso_1='X{}'.format(indice+2)
        sheet.update(cell_proceso_1, comentarioInfoGeneral)
        globales.error = True
    else:
        globales.estado_proceso_2 = url_proceso_2
        cell_proceso_2='J{}'.format(indice+2)
        sheet.update(cell_proceso_2, url_proceso_2)
        
#apartado de configuración del proceso
def configuracion_proceso(params_configuracion_proceso):
    
    #Desempaquetado de parámetros
    driver = params_configuracion_proceso['driver']
    url_proceso_2 = params_configuracion_proceso['estado_proceso_2']
    sheet = params_configuracion_proceso['sheet']
    indice = params_configuracion_proceso['indice']
    fecha_firma_contrato = params_configuracion_proceso['fecha_firma_contrato']
    fecha_inicio_contrato = params_configuracion_proceso['fecha_inicio']
    fecha_plazo_ejecucion = params_configuracion_proceso['fecha_fin']
    valor_estimado = params_configuracion_proceso['valor_estimado']
    destinacion_gasto = params_configuracion_proceso['destinacion_gasto']
    tipo_cdp = params_configuracion_proceso['tipo_cdp']
    codigo_cdp = params_configuracion_proceso['codigo_cdp']
    saldo_cdp = params_configuracion_proceso['saldo_cdp']

    wait = WebDriverWait(driver, 40)
    try:
        driver.get(url_proceso_2)
        try:
            time.sleep(4)
            botonContinuarProceso2 = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@id = 'btnApproveDossier']"))
                )
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(botonContinuarProceso2).click().perform()
            time.sleep(2)
            botonAceptarContinuarProceso2 = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@id = 'btnNoPAAPublishedCurrentYearConfirmDialogModal']"))
                )
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(botonAceptarContinuarProceso2).click().perform()
        except:
            time.sleep(2)
            flecha_continuar = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@id = 'lnk_stpmStepManager3']"))
                )
            action  =  webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element(flecha_continuar).click().perform()
        try:
            time.sleep(3)
            frame_acuerdo_marco_disponible = driver.find_element(By.ID, "ActiveFrameworkAgreementModal_iframe")
            driver.switch_to.frame(frame_acuerdo_marco_disponible)
            time.sleep(3)
            botonCerrarAcuerdoMarcoDisponible = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@id ='btnCloseAndContinue']"))
                ).click()
        except Exception as e:
            pass
        time.sleep(7)
        driver.switch_to.default_content()
        time.sleep(1)
        radio_decreto_248 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgComplyWithMinimalPurchaseValue_1']"))
            ).click()
        time.sleep(3)
        radio_sentencia_T302 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgProcessAssociatedWithSentenceT302Value_1']"))
            ).click()
        time.sleep(3)
        radioAcuerdosPaz = driver.find_element(By.XPATH, "//input[@id = 'rdbgFrameworkAgreementValue_1']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(radioAcuerdosPaz).click().perform()
        time.sleep(2)
        valorFirmaContrato = fecha_firma_contrato
        campoFirmaContrato = driver.find_element(By.XPATH, "//input[@id = 'dtmbContractSignatureDate_txt']")
        campoFirmaContrato.send_keys(valorFirmaContrato)
        valorFechaInicioEjec = fecha_inicio_contrato
        campoFechaInicioEjec = driver.find_element(By.XPATH, "//input[@id = 'dtmbStartDateExecutionOfContract_txt']")
        campoFechaInicioEjec.send_keys(valorFechaInicioEjec)
        valorPlazoEjec = fecha_plazo_ejecucion
        campoPlazoEjec = driver.find_element(By.XPATH, "//input[@id = 'dtmbExecutionOfContractTerm_txt']")
        campoPlazoEjec.send_keys(valorPlazoEjec)
        time.sleep(2)
        campoValorEstimado = driver.find_element(By.XPATH, "//input[@id = 'cbxBasePrice']")
        campoValorEstimado.send_keys(valor_estimado)
        time.sleep(2)
        if(str(destinacion_gasto) == "1"):
            time.sleep(3)
            select_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'selExpenseTypeSelect')))
            selectDestGasto = Select(select_element)
            selectDestGasto.select_by_visible_text("Funcionamiento")
            time.sleep(2)
            radio_png = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginGNBCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_sgp =  WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginGSPCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_sgr = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginGRSCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_recursos_propios = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginOwnResourcesAGRICheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_recursos_credito = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginCreditResourcesCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_otros_recursos =  WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginOwnResourcesCheckValueP2Gen_0']"))
            ).click()

            time.sleep(1)
            campo_otros_recursos = driver.find_element(By.ID, "cbxBudgetOriginOwnResourcesValue")
            time.sleep(1)
            campo_otros_recursos.send_keys(valor_estimado)
        elif(str(destinacion_gasto) == "2"):
            time.sleep(3)
            select_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'selExpenseTypeSelect')))
            selectDestGasto = Select(select_element)
            selectDestGasto.select_by_visible_text("Inversion")
            time.sleep(2)
            radio_png = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginGNBCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_sgp =  WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginGSPCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_sgr = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginGRSCheckValueP2Gen_0']"))
            ).click()
            time.sleep(2)
            radio_recursos_propios = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginOwnResourcesAGRICheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_recursos_credito = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginCreditResourcesCheckValueP2Gen_1']"))
            ).click()
            time.sleep(2)
            radio_otros_recursos =  WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@id = 'rdbgBudgetOriginOwnResourcesCheckValueP2Gen_1']"))
            ).click()
            time.sleep(1)
            campo_sgr = driver.find_element(By.ID, "cbxBudgetOriginGRSValue")
            time.sleep(1)
            campo_sgr.send_keys(valor_estimado)
        time.sleep(1)
        radioSIIF = driver.find_element(By.XPATH, "//input[@id = 'rdbgCompanyRegisteredInSIIFValue_1']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(radioSIIF).click().perform()
        #evaluar si la longitud de los cdps y los saldos coinciden, sino, lanza excepción
        if(len(codigo_cdp) != len(saldo_cdp)):
            raise Exception("Error de cdps: La cantidad de cdps no coinciden con la cantidad de saldos")
        try:
            #bloque para rendir cdps
            for i in range(len(codigo_cdp)):
                codigo_cdp_actual = codigo_cdp[i].replace(" ", "")
                saldo_cdp_actual = saldo_cdp[i]
                time.sleep(1)
                boton_agregar_CDP = driver.find_element(By.ID, "btnAddCode")
                action  =  webdriver.common.action_chains.ActionChains(driver)
                action.move_to_element(boton_agregar_CDP).click().perform()
                time.sleep(1)
                iframe_CDP = driver.find_element(By.ID, "SIIFModal_iframe")
                driver.switch_to.frame(iframe_CDP)
                time.sleep(3)
                if (str(tipo_cdp) == "1"):
                    radio_cdp = driver.find_element(By.ID, "rdbgOptionsToSelectRadioButton_0")
                    action  =  webdriver.common.action_chains.ActionChains(driver)
                    action.move_to_element(radio_cdp).click().perform()
                elif(str(tipo_cdp) == "2"):
                    radio_vigencias_futuras = driver.find_element(By.ID, "rdbgOptionsToSelectRadioButton_1")
                    action  =  webdriver.common.action_chains.ActionChains(driver)
                    action.move_to_element(radio_vigencias_futuras).click().perform()
                
                campo_codigo_cdp = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@id = 'txtSIIFIntegrationItemTextbox']"))
                    ).send_keys(codigo_cdp_actual)
                campo_saldo_cdp = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@id = 'cbxSIIFIntegrationItemBalanceTextbox']"))
                    ).send_keys(saldo_cdp_actual)
                campo_saldo_comprometer = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@id = 'cbxSIIFIntegrationItemUsedValueTextbox']"))
                    ).send_keys(saldo_cdp_actual)
                campo_subunidad_ejecutora = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@id = 'txtSIIFIntegrationItemPCICodebox']"))
                    ).send_keys("00-00-00")
                btn_crear_CDP = driver.find_element(By.ID, "btnSIIFIntegrationItemButton")
                action  =  webdriver.common.action_chains.ActionChains(driver)
                action.move_to_element(btn_crear_CDP).click().perform()
                driver.switch_to.default_content()
            #fin del bloque para rendir cdps
        except:
            raise Exception("Error de cdps: No fue posible agregar CDP")
        time.sleep(3)
        botonGuardarProceso3=WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@id = 'btnSaveProcedureTop']"))
                )
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonGuardarProceso3).click().perform()
        tag_errores_validacion = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Proceso guardado con éxito')]")))
        time.sleep(5)
        url_proceso_3 = driver.current_url
    except Exception as e:
        if(str(e) == 'Error de cdps: La cantidad de cdps no coinciden con la cantidad de saldos' or 
            str(e) == 'Error de cdps: No fue posible agregar CDP'):
            comentarioConfigProceso = str(e)
        else:
            comentarioConfigProceso = 'Error al ejecutar la configuración del proceso: {}'.format(str(e))
        cell_proceso_1='X{}'.format(indice+2)
        sheet.update(cell_proceso_1, comentarioConfigProceso)
        globales.error = True
    else:
        globales.estado_proceso_3 = url_proceso_3
        cell_proceso_3='Q{}'.format(indice+2)
        sheet.update(cell_proceso_3, url_proceso_3)

#Realiza el completado del apartado de cuestionario
def completar_cuestionario(params_completar_cuestionario):
    
    #Desempaquetado de parámetros
    driver = params_completar_cuestionario['driver']
    url_proceso_3 = params_completar_cuestionario['estado_proceso_3']
    sheet = params_completar_cuestionario['sheet']
    indice = params_completar_cuestionario['indice']
    codigo = params_completar_cuestionario['codigo']
    objeto = params_completar_cuestionario['objeto_descripcion']
    valor = params_completar_cuestionario['valor_estimado']

    try:
        wait = WebDriverWait(driver, 40)
        valorUNSPSC = codigo
        driver.get(url_proceso_3)
        time.sleep(10)
        botonCuestionario = driver.find_element(By.XPATH, "//span[@id = 'lnk_stpmStepManager4']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonCuestionario).click().perform()
        time.sleep(5)
        botonMas = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@class = 'FtlExpandAll']"))
                ).click()
        time.sleep(5)
        campoUNSPSC = driver.find_element(By.XPATH, "//input[contains(@id,'CategoryCode_LookupText')]")
        campoUNSPSC.clear()
        time.sleep(1)
        campoUNSPSC.send_keys(valorUNSPSC)
        time.sleep(1)
        xpath_lista_codigos = "//span[contains(text(), '{}')]".format(codigo)
        listaUNSPSC = driver.find_element(By.XPATH,xpath_lista_codigos)
        time.sleep(2)
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(listaUNSPSC).click().perform()
        time.sleep(1)
        campoDescripcion = driver.find_element(By.XPATH, "//input[contains(@id,'_Description')]")
        campoDescripcion.send_keys(objeto)
        campoPrecioUnitarioEstimado = driver.find_element(By.XPATH, "//input[contains(@id,'_CeilingPrice')]")
        campoPrecioUnitarioEstimado.send_keys(valor)
        campoCantidad=driver.find_element(By.XPATH, "//input[contains(@id,'_Quantity')]")
        campoCantidad.send_keys("1")
        botonGuardarProceso4=WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//input[@id = 'tbToolBarPlaceHolder_btnSaveProcedureTop']"))
                    )
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonGuardarProceso4).click().perform()
        tag_errores_validacion = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Proceso guardado con éxito')]")))
        time.sleep(2)
        url_proceso_4 = driver.current_url
    except Exception as e:
        comentarioCuestionario = 'Error en el proceso de completar cuestionario'
        cell_proceso_1='X{}'.format(indice+2)
        sheet.update(cell_proceso_1, comentarioCuestionario)
        globales.error = True
    else:
        globales.estado_proceso_4 = url_proceso_4
        cell_proceso_4='R{}'.format(indice+2)
        sheet.update(cell_proceso_4, url_proceso_4)

#se direcciona al apartado donde se adjuntan los documentos del proceso
def documentos_proceso (params_documentos_proceso):
    
    #Desempaquetado de parámetros
    driver = params_documentos_proceso['driver']
    url_proceso_4 = params_documentos_proceso['estado_proceso_4']
    sheet = params_documentos_proceso['sheet']
    indice = params_documentos_proceso['indice']
    numero_contrato = params_documentos_proceso['nombre_proceso']

    #captura fecha para constancia del proceso
    ahora = datetime.now()
    try:
        eliminar_archivo_comprimido()
    except:
        pass
    try:
        wait = WebDriverWait(driver, 20)
        driver.get(url_proceso_4)
        time.sleep(6)
        boton_documentos_proceso = driver.find_element(By.XPATH, "//span[@id = 'lnk_stpmStepManager5']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(boton_documentos_proceso).click().perform()
        lista_documentos = descargar_onbase(numero_contrato)
        if(len(lista_documentos) == 0):
            raise Exception("Parece que hubo un problema en OnBase o no fue posible adjuntar los documentos")
        boton_anexar_documentos = wait.until(EC.element_to_be_clickable((By.ID, "incContractDocumentsbtnUploadDocumentGen"))).click()
        time.sleep(5)
        handles = driver.window_handles
        driver.switch_to.window(handles[-1])
        driver.maximize_window()
        time.sleep(6)

        # Simulación de click para no perder el foco
        try:
            element_to_click = driver.find_element(By.XPATH, '//*[@id="spnPageTitle"]')

            # Hace clic en el elemento
            element_to_click.click()
        except Exception as e:
            print(e)
        else:
            print('Clic en ventana')
        
        time.sleep(4)
        pathFolderDocumentos="C:\\scriptAutomatizacionSecop2\\documentos\\"
        
        #----------------------ADJUNTE DE ARCHIVOS CON GUI-----------------------
        pyautogui.hotkey('win', 'r')  
        time.sleep(3)  
        pyautogui.write(pathFolderDocumentos)
        pyautogui.press('enter') 
        time.sleep(5)
        pyautogui.hotkey('ctrl', 'e')
        time.sleep(3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(5)
        pyautogui.hotkey('alt', 'f4')
        time.sleep(2)
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(1)
        # Simular un clic en la nueva ventana
        # Obtén las dimensiones de la pantalla
        screen_width, screen_height = pyautogui.size()

        # Calcula el centro horizontal
        center_x = screen_width // 2

        # La coordenada 'y' será la que ya tienes (200 en tu ejemplo)
        y = 200  # Reemplaza con la coordenada real donde quieres hacer clic

        # Ahora haz clic en el centro horizontalmente, pero en la 'y' que has especificado
        pyautogui.click(center_x, y)
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(8)
        boton_anexar = driver.find_element(By.ID, "btnUploadFilesButtonBottom")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(boton_anexar).click().perform()
        time.sleep(3)

        #Ubica el tbody donde están todos los documentos
        tbody_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tblFilesTable"]/tbody[2]'))
        )
        
        # Contar cuántos hijos tr tiene
        tr_elements = tbody_element.find_elements(By.TAG_NAME, 'tr')
        num_tr = len(tr_elements)

        while (True):
            
            # Ubicar todos los elementos span con texto "Documento anexo"
            span_elements = driver.find_elements(By.XPATH, '//span[text()="Documento anexo"]')
            num_span = len(span_elements)
            
            # Comparar y retornar resultado
            if num_tr == num_span:
                break

        time.sleep(3)
        boton_cerrar = driver.find_element(By.ID, "btnCancelBottomButtom")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(boton_cerrar).click().perform()
        driver.switch_to.window(handles[0])
        time.sleep(5)
        documentos_anexados = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div[1]/table/tbody/tr/td[2]"))
            )
        time.sleep(5)
        botonIrPublicar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id = 'btnOption_trRowToolbarTop_tdCell1_tbToolBar_Finish']"))
            )
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonIrPublicar).click().perform()
        documentos_anexados = WebDriverWait(driver, 60).until(
            EC.invisibility_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div[1]/table/tbody/tr/td[2]"))
            )
        time.sleep(3)
        botonPublicar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id = 'tbToolBarPlaceHolder_btnPublishRequest']"))
            )
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonPublicar).click().perform()
        time.sleep(3)
        try:
            #se acepta la alerta generada para vincular el rubro como principal
            alert = Alert(driver)
            alert.accept()
        except:
            pass

        try:
            url = driver.current_url
            # wait until the URL changes to a new value
            WebDriverWait(driver, 50).until(EC.url_changes(url))

        except TimeoutException:
            # handle the error here
            print("Error: la URL no cambió durante el tiempo estipulado")

        texto_enlace_real = obtener_enlace(url, sheet, indice)
        if(texto_enlace_real == ''):
            raise Exception("Elementos de la URL no fueron encontrados correctamente")
    except Exception as e:
        if(str(e) == 'Parece que hubo un problema en OnBase o no fue posible adjuntar los documentos'):
            comentarioDocumentosProceso = str(e)
        else:
            comentarioDocumentosProceso = 'Error general en la etapa de los documentos del proceso' + str(e)
        cell_proceso_1='X{}'.format(indice+2)
        sheet.update(cell_proceso_1, comentarioDocumentosProceso)
        globales.error = True
    else:
        globales.estado_proceso_5 = texto_enlace_real
        cell_proceso_5='S{}'.format(indice+2)
        sheet.update(cell_proceso_5, texto_enlace_real)
        cell_fecha_publicacion='U{}'.format(indice+2)
        fecha = ahora.strftime("%#d/%m/%Y")
        sheet.update(cell_fecha_publicacion, fecha)

#se utiliza para descargar los archivos de OnBase
def descargar_onbase(numero_contrato):
    time.sleep(3)
    if type(numero_contrato) == int:
        numero_contrato = str(numero_contrato)
    if ("-" in numero_contrato):
            numero_contrato = numero_contrato.split("-")[0] #elimina lo que vaya después del - para los contratos de prueba.
    limpiar_directorio_documentos()
    download_dir = 'C:\\scriptAutomatizacionSecop2\\documentos'
    options = Options()
    # Configurar opciones experimentales para las descargas
    options.add_experimental_option('prefs', {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    # Inicializar el driver de Chrome
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    driver.get(os.getenv('URL_ONBASE'))
    driver.execute_script("document.body.style.zoom='97%'")
    wait = WebDriverWait(driver, 20)
    campo_usuario_onbase = wait.until(EC.element_to_be_clickable((By.ID, "username")))
    campo_contrasena_onbase = wait.until(EC.element_to_be_clickable((By.ID, "password")))
    campo_usuario_onbase.send_keys(os.getenv('USER_ONBASE'))
    campo_contrasena_onbase.send_keys(os.getenv('PASS_ONBASE'))
    wait.until(EC.element_to_be_clickable((By.ID, "loginButton"))).click()
    try:
        time.sleep(1)
        boton_cerrar_bloqueo = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "dialog-close"))).click()
    except Exception as e:
        print(e)
    boton_menu_navegacion = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/header/section[1]/div[1]"))).click()
    time.sleep(2)
    boton_consulta_personalizada = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="customquery"]'))).click()
    time.sleep(2)
    frameNavegacion = driver.find_element(By.ID,"NavPanelIFrame" )
    driver.switch_to.frame(frameNavegacion)
    time.sleep(2)
    boton_buscar_documentos_expediente = wait.until(EC.element_to_be_clickable((By.ID, 'itemLabel133'))).click()
    driver.switch_to.default_content()
    time.sleep(5)
    wait = WebDriverWait(driver, 50)
    frameFormViewer = driver.find_element(By.ID,"frmViewer")
    driver.switch_to.frame(frameFormViewer)
    frameHtmlForm = wait.until(EC.element_to_be_clickable((By.ID, 'html_form')))
    driver.switch_to.frame(frameHtmlForm)
    campo_nombre_expediente = driver.find_element(By.ID, 'Nombre expediente')
    campo_nombre_expediente.send_keys(numero_contrato)

    wait.until(EC.element_to_be_clickable((By.ID, "save"))).click()
    driver.switch_to.default_content()
    frameResultados = wait.until(EC.element_to_be_clickable((By.ID, 'frmViewer')))
    driver.switch_to.frame(frameResultados)
    frameQuery = wait.until(EC.element_to_be_clickable((By.ID, 'customQueryResultsFrame')))
    driver.switch_to.frame(frameQuery)
    frameDocumentos = wait.until(EC.element_to_be_clickable((By.ID, 'frameDocSelect')))
    driver.switch_to.frame(frameDocumentos)
    tabla_documentos_anexos = wait.until(EC.element_to_be_clickable((By.ID, 'primaryHitlist_grid')))
    #----------------CAMBIO PARA QUE EXCLUYA LOS DOCUMENTOS EN LA LISTA DE EXCLUIDOS
    filas = tabla_documentos_anexos.find_elements(By.TAG_NAME, "tr")
    dict_info_archivo ={}
    array_nombres_documentos = []

    #quita la selección por defecto del primer elemento
    action = webdriver.common.action_chains.ActionChains(driver)
    action.key_down(Keys.CONTROL).perform()
    filas[0].click()
    time.sleep(1)
    
    last_selected = None  # Esta variable almacenará el último documento seleccionado

    for item in range(len(filas)):
        # Asumimos que la tipología está en la primera celda de cada fila
        tipologia = driver.find_element(By.XPATH, f'//*[@id="primaryHitlist_grid"]/tbody/tr[{item + 1}]/td[1]').get_attribute('textContent')
        nombre_documento = driver.find_element(By.XPATH, f'//*[@id="primaryHitlist_grid"]/tbody/tr[{item + 1}]/td[2]').get_attribute('textContent')
        nombre_excluido_en_nombre = any([nombre_excluido in nombre_documento.strip() for nombre_excluido in globales.nombres_excluidos])
        tipologia_excluida_en_tipologia = any([tipologia_excluida == tipologia.strip() for tipologia_excluida in globales.tipologias_excluidas])

        if (not tipologia_excluida_en_tipologia) or (tipologia.strip() == "CERTIFICADO DE ANTECEDENTES" and not nombre_excluido_en_nombre):
            action = webdriver.common.action_chains.ActionChains(driver)
            action.key_down(Keys.CONTROL).perform()
            driver.execute_script("arguments[0].scrollIntoView(true);", filas[item])
            time.sleep(1)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(filas[item]))
            filas[item].click()
            time.sleep(1)
            last_selected = filas[item]  # Almacena la fila seleccionada

    # Asegúrate de que tengas un documento seleccionado antes de realizar la acción
    if last_selected:
        time.sleep(3)
        driver.execute_script("arguments[0].scrollIntoView(true);", last_selected)
        time.sleep(1)  # Añade una pausa breve para asegurar que el scroll se complete

        # Realiza la acción de clic derecho
        action = webdriver.common.action_chains.ActionChains(driver)
        action.context_click(last_selected).perform()

    #time to customize
    time.sleep(3)
    driver.switch_to.default_content()
    menu_item_enviar = driver.find_element(By.XPATH, '//*[@id="menuControl_25"]')
    action  =  webdriver.common.action_chains.ActionChains(driver)
    action.click(menu_item_enviar).perform()
    time.sleep(3)
    menu_item_archivo = driver.find_element(By.XPATH, '//*[@id="menuControl_13"]')
    
    action  =  webdriver.common.action_chains.ActionChains(driver)
    action.click(menu_item_archivo).perform()
    #driver.switch_to.window(driver.window_handles[1])
    wait = WebDriverWait(driver, 20)
    boton_guardar_archivos = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Guardar')]"))).click()
    path_archivo_zip = download_dir + "\\SavedDocument.zip"
    lista_documentos_sin_repetidos = []
    while not os.path.exists(path_archivo_zip):
        try:
            errorEnDescarga = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Error')]")))
        except:
            pass
        else:
            return lista_documentos_sin_repetidos
        time.sleep(2)
    if os.path.isfile(path_archivo_zip):
        driver.close()
        time.sleep(2)
        #driver.switch_to.window(driver.window_handles[0])
        extraer_archivo_zip(path_archivo_zip, download_dir)
        lista_documentos = os.listdir(download_dir)
        lista_documentos.remove("SavedDocument.zip")
        lista_documentos_sin_repetidos = []
        for i, v in enumerate(lista_documentos):
            totalcount = lista_documentos.count(v)
            count = lista_documentos[:i].count(v)
            if(totalcount > 1):
                old_name = r"C:\\scriptAutomatizacionSecop2\\documentos\\{}".format(v)
                new_name = r"C:\\scriptAutomatizacionSecop2\\documentos\\{}".format(v + str(count + 1))
                os.rename(old_name, new_name)
                lista_documentos_sin_repetidos.append(v + str(count + 1))
            else:
                lista_documentos_sin_repetidos.append(v)

        for i in range(len(lista_documentos_sin_repetidos)):
            try:
                item_sin_acentos = unidecode.unidecode(lista_documentos_sin_repetidos[i])
                old_name = r"C:\\scriptAutomatizacionSecop2\\documentos\\{}".format(lista_documentos_sin_repetidos[i])
                new_name = r"C:\\scriptAutomatizacionSecop2\\documentos\\{}".format(item_sin_acentos)
                os.rename(old_name, new_name)
                lista_documentos_sin_repetidos[i] = item_sin_acentos
            except:
                continue
        os.remove(path_archivo_zip)
    return lista_documentos_sin_repetidos

#función para extraer archivo
def extraer_archivo_zip(path_to_zip_file, directory_to_extract_to):
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(directory_to_extract_to)
#se utiliza para limpiar la carpeta de descargas cada vez que se comienza un nuevo proceso
def limpiar_directorio_documentos():
    path = r"C:\\scriptAutomatizacionSecop2\\documentos\\"
    for file_name in os.listdir(path):
        # construct full file path
        file = path + file_name
        if os.path.isfile(file):
            os.remove(file)
def eliminar_archivo_comprimido():
    path = r"C:\\scriptAutomatizacionSecop2\\documentos\\"
    file = path + "SavedDocument.zip"
    os.remove(file)
#actualiza el estado para saber si el registro ya se ejecutó
def actualizar_estado_ejecucion(sheet, indice):
    cell_ejecutado='T{}'.format(indice+2)
    sheet.update(cell_ejecutado, "SI")

#function smart waiter
def notExistElement(driver, number_tries, xpath):
    count_try = 0
    not_found = False
    while (True):
        try:
            element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        except:
            count_try += 1
            if(count_try == number_tries):
                not_found = True
                break
            else:
                continue
        else:
            break
    return not_found
def mostrarMensaje(mensaje):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Información: ", mensaje)

def obtener_enlace(url, sheet, indice):
    # Configurar las opciones de Edge
    options = Options()
    options.add_argument("--incognito")  # Añadir el argumento para abrir Edge en modo incógnito

    # Inicializar el driver de Edge
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window() 
    loguearse_secop(driver)
    driver.get(url)
    time.sleep(5)
    texto_enlace_real = ''
    noExisteLinkExpediente = notExistElement(driver, 50, "//*[@id='breadcrumb']/a[4]")
    if (noExisteLinkExpediente):
        driver.close()
        return texto_enlace_real
    else:
        linkExpediente = driver.find_element(By.XPATH, "//*[@id='breadcrumb']/a[4]")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(linkExpediente).click().perform()

    time.sleep(5)
    noExisteVerEnlace = notExistElement(driver, 20, "//input[@id = 'btnSeePublicContractNoticeLink']")
    if (noExisteVerEnlace):
        driver.close()
        return texto_enlace_real
    else:
        botonVerEnlace = driver.find_element(By.XPATH, "//input[@id = 'btnSeePublicContractNoticeLink']")
        action  =  webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(botonVerEnlace).click().perform()

    time.sleep(5)
    noExisteTextoEnlace = notExistElement(driver, 20, "//span[@id = 'spnPublicContractNoticeLink']")
    if (noExisteTextoEnlace):
        driver.close()
        return texto_enlace_real
    else:
        textoEnlace = driver.find_element(By.XPATH, "//span[@id = 'spnPublicContractNoticeLink']").text
        time.sleep(3)
        driver.get(textoEnlace)
        time.sleep(5)
        texto_enlace_real = driver.find_element(By.XPATH, "//label[@id = 'lblDisplayPhaseLink_0']").text
        driver.close()
        return texto_enlace_real

#funcion auxiliar para validar que el objeto del contrato no contenga caracteres no validos
def contains_invalid_chars(s):
    invalid_chars = ['"', "'", "<", ">", "&", "%", "@", "$", "-", "#", "_", "–", "°", "º", "*", "±", "[", "]", "+", "•", "|", "–"]
    for char in s:
        if char in invalid_chars:
            return True
    return False

def set_foreground_window(name):
    windows = gw.getWindowsWithTitle(name)
    if windows:
        window = windows[0]  # Tomamos la primera ventana que coincide con el título
        window.activate()
        # Si también quieres mover el mouse al centro de la ventana, puedes hacerlo con:
        pyautogui.moveTo(window.center)
