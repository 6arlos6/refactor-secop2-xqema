# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pwinput
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import json
from funciones import *
import globales
import os
from dotenv import load_dotenv
import shutil

# Cargar las variables de .env
load_dotenv()
time.sleep(2)
nombre_estacion = os.getenv('NOMBRE_ESTACION')

#---------INICIALIZACIÓN DE VARIABLES GLOBALES DEL ARCHIVO AUTOMATIZACION--------------------
#base de datos donde se alojan los datos a rendir
bd = os.getenv('HOJA_DATOS')
#variable de scopes de google
scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
#variable de credenciales de acceso con el archivo json descargado desde GCLOUD
creds = ServiceAccountCredentials.from_json_keyfile_name('client_sheet.json',scope)
#autorización de las credenciales de acceso
cliente = gspread.authorize(creds)
#se establece el nombre de la base de datos a trabajar
sheet = cliente.open(bd).worksheet(os.getenv('WORKSHEET'))
#se almacenan todos los valores de la base de datos en un array
globales.array_valores = sheet.get_all_records()


#---------INICIALIZACIÓN DEL DRIVER PARA CONTROLAR CHROME---------
# Configurar las opciones de Chrome
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.maximize_window() 

#---------FUNCION AUXILIAR PARA DECONSTRUIR CDPS Y SALDOS----------
def deconstruir_cdps_saldos(valores):
    if('\n') in str(valores):
        valores = valores.split('\n')
    else:
        valores = [str(valores)]
    return valores

#---------FUNCION AUXILIAR PARA LIMPIAR TEMPORALES----------
def clear_temp_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)  # Delete file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Delete directory
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

# Limpia directorio de temporales y versiones de chromedriver
try:
    clear_temp_directory(r"C:\Users\rpa.reportes\.wdm\drivers\chromedriver")
except:
    pass
time.sleep(1)

#---------FUNCION PARA EJECUCIÓN DE PROCESOS DE MANERA SELECTIVA---
def ejecutar_procesos(proceso1, proceso2, proceso3, proceso4, proceso5):
    if((proceso1 == "" or proceso2 == "" or proceso3 == "" or proceso4 == "" or proceso5 == "") and globales.error == False):
        #---------------------INGRESO A PLATAFORMA SECOP II-----------------------
        if(globales.logueado == False):
            loguearse_secop(driver)
        else:
            pass
    if proceso1 == "" and globales.error == False:
        #-------------------CREACIÓN DE PROCESO EN SECOP II-----------------------
        #Empaquetado de parámetros
        params_creacion_proceso = {
            'driver': driver,
            'sheet': sheet,
            'indice': indice,
            'nombre_proceso': nombre_proceso, 
            'unidad_contratacion': unidad_contratacion
        }
        creacion_proceso(params_creacion_proceso)
    if proceso2 == "" and globales.error == False:
        #-------------------INFORMACIÓN GENERAL DEL PROCESO-------------------------
        #Empaquetado de parámetros
        params_info_general = {
            'driver': driver,
            'sheet': sheet,
            'indice': indice,
            'estado_proceso_1': globales.estado_proceso_1,
            'objeto_descripcion': objeto_descripcion,
            'codigo': codigo,
            'tipo_contrato': tipo_contrato,
            'acuerdos_comerciales': acuerdos_comerciales,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'documento_proveedor': documento_proveedor,
            'nombre_proveedor': nombre_proveedor,
            'tipo_identificador': tipo_identificador,
            'tipo_proveedor': tipo_proveedor,
            'localizacion': localizacion,
            'cliente': cliente,
            'email': email,
            'contrato_marco': contrato_marco
        }
        informacion_general(params_info_general)
    if proceso3 == "" and globales.error == False:
        #--------------------CONFIGURACIÓN DEL PROCESO------------------------------
        #Empaquetado de parámetros
        params_configuracion_proceso = {
            'driver': driver,
            'estado_proceso_2': globales.estado_proceso_2,
            'sheet': sheet,
            'indice': indice,
            'fecha_firma_contrato': fecha_firma_contrato,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'valor_estimado': valor_estimado,
            'destinacion_gasto': destinacion_gasto,
            'tipo_cdp': tipo_cdp,
            'codigo_cdp': codigo_cdp,
            'saldo_cdp': saldo_cdp
        }
        configuracion_proceso(params_configuracion_proceso)
    if proceso4 == "" and globales.error == False:
        #---------------------CONFIGURACIÓN Y COMPLETADO DE CUESTIONARIO-------------
        #Empaquetado de parámetros
        params_completar_cuestionario = {
            'driver': driver,
            'estado_proceso_3': globales.estado_proceso_3,
            'sheet': sheet,
            'indice': indice,
            'codigo': codigo,
            'objeto_descripcion': objeto_descripcion,
            'valor_estimado': valor_estimado
        }
        completar_cuestionario(params_completar_cuestionario)
    if proceso5 == "" and globales.error == False:
        #---------------------CARGA DE DOCUMENTOS Y PUBLICACIÓN----------------------
        #Empaquetado de parámetros
        params_documentos_proceso = {
            'driver': driver,
            'estado_proceso_4': globales.estado_proceso_4,
            'sheet': sheet,
            'indice': indice,
            'nombre_proceso': nombre_proceso
        }
        documentos_proceso(params_documentos_proceso)
    
    #actualiza el estado en la columna "corrido" de tal manera que no se vuelva a ejecutar.
    actualizar_estado_ejecucion(sheet, indice)
        
#--------------LÓGICA DEL BOT----------------------
inicializarLogeadoPorErrores = False #Variable que controla si al siguiente ciclo inicializa logueado

for indice in range(len(globales.array_valores)):
    
    valor_actual = globales.array_valores[indice]
    if (
        valor_actual["Nombre"] == '' or
        valor_actual["Estacion de trabajo"] != nombre_estacion or
        valor_actual["Ejecutado"] == "SI"
    ):
        continue
    #se establecen las variables para los valores que se van a usar de cada campo
    nombre_proceso = globales.array_valores[indice]["Nombre"]
    unidad_contratacion = globales.array_valores[indice]["Unidad de contratación"]
    objeto_descripcion = globales.array_valores[indice]["Objeto (Descripción)"]
    codigo = globales.array_valores[indice]["Clasificación del bien o servicio"]
    documento_proveedor = globales.array_valores[indice]["Numero de documento del proveedor"]
    nombre_proveedor = globales.array_valores[indice]["Nombre del proveedor"]
    tipo_proveedor = globales.array_valores[indice]["Tipo de entidad / Proveedor"]
    tipo_identificador = globales.array_valores[indice]["Tipo de identificador"]
    localizacion = globales.array_valores[indice]["Localización (Ciudad)"]
    tipo_contrato = globales.array_valores[indice]["Tipo de contrato"]
    email = globales.array_valores[indice]["Correo electrónico proveedor"]
    contrato_marco = globales.array_valores[indice]["Contrato Marco"]
    acuerdos_comerciales = globales.array_valores[indice]["Acuerdos comerciales"]
    fecha_inicio = globales.array_valores[indice]["Fecha de incio"]
    fecha_fin = globales.array_valores[indice]["Fecha de terminación"]
    fecha_firma_contrato = globales.array_valores[indice]["Firma Contrato"]
    valor_estimado = globales.array_valores[indice]["Valor estimado"]
    destinacion_gasto = globales.array_valores[indice]["Destinación Gasto"]
    tipo_cdp = globales.array_valores[indice]["Tipo CDP"]
    codigo_cdp = globales.array_valores[indice]["Código CDP"]
    saldo_cdp = globales.array_valores[indice]["Saldo CDP"]
    codigo_cdp = deconstruir_cdps_saldos(codigo_cdp) #valida si hay salto de linea en los cdps para saber si son multiples y los deconstruye
    saldo_cdp = deconstruir_cdps_saldos(saldo_cdp) #valida si hay salto de linea en los saldos para saber si son multiples y los deconstruye
    #inicia variables globales
    globales.init()
    #asigna a las variables globales el valor de la base de datos
    globales.estado_proceso_1 = globales.array_valores[indice]["Proceso 1"]
    globales.estado_proceso_2 = globales.array_valores[indice]["Proceso 2"]
    globales.estado_proceso_3 = globales.array_valores[indice]["Proceso 3"]
    globales.estado_proceso_4 = globales.array_valores[indice]["Proceso 4"]
    globales.estado_proceso_5 = globales.array_valores[indice]["Proceso 5"]
    #envia los parámetros de los estados para ejecutar las diferentes funciones
    ejecutar_procesos( globales.estado_proceso_1,  globales.estado_proceso_2,  globales.estado_proceso_3,  globales.estado_proceso_4, globales.estado_proceso_5)
    
mostrarMensaje("Se ha terminado de realizar la operación. Sugerencia: revisa la base de datos para verificar el proceso.")




