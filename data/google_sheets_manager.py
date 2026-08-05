# -*- coding: utf-8 -*-
"""
Módulo para la gestión y conexión con Google Sheets.

Este módulo proporciona las herramientas necesarias para autenticarse con la API de Google Sheets, 
manipular el documento principal de la base de datos y realizar operaciones de lectura y escritura.

Clases y Funciones principales:

1. GoogleSheetsConnection: 
   - Propósito: Gestionar la autenticación con la API usando credenciales de cuenta de servicio y mantener la conexión al documento maestro.
   - __init__: Establece la conexión validando el archivo JSON de credenciales, definiendo los scopes y abriendo la base de datos especificada.

2. ContratosRepository: 
   - Propósito: Manejar las operaciones de lectura, escritura y actualización (CRUD) específicamente para la hoja de contratos.
   - __init__: Vincula el repositorio a una hoja específica y crea un mapa de las columnas para fácil acceso.
   - obtener_registros_pendientes: Descarga todos los registros de la hoja, filtrándolos por estación de trabajo que aún no han sido reportados como ejecutados ('SI').
   - actualizar_celda_por_nombre: Modifica el valor de una celda específica, ubicándola a partir de su número de fila y el nombre de la columna en la cabecera.
   - actualizar_estado_ejecucion: Marca la fila correspondiente como "SI" en la columna 'Ejecutado' para indicar que el procesamiento finalizó, ya sea con éxito o con error.
   - reportar_error: Acumula cronológicamente (más reciente arriba, con timestamp) un mensaje de error en la columna 'Log de errores' (o su equivalente legado), detallando el paso donde ocurrió el fallo.

3. ConfigRepository: 
   - Propósito: Proveer métodos para extraer datos de configuración o maestros que se encuentran en otras pestañas auxiliares del documento.
   - __init__: Inicializa el repositorio recibiendo la instancia del documento principal (previamente abierto por GoogleSheetsConnection).
   - obtener_datos_maestros: Obtiene todos los registros presentes en la pestaña indicada y los devuelve como una lista.
   - obtener_ciudades_codigos: Extrae el mapeo de nombres de ciudades con sus códigos desde la hoja "DATA_CIUDADES_CODIGOS", devolviéndolo como un diccionario.
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from utils.execution_context import ExecutionContext


# =========================================================================
# 1. CAPA DE INFRAESTRUCTURA (Conexion)
# =========================================================================
class GoogleSheetsConnection:
    """Gestiona la autenticacion y mantiene el documento maestro abierto."""

    def __init__(self, json_keyfile, db_name, scopes):
        print(f"Estableciendo conexion con la base de datos '{db_name}'...")
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scopes)
        self.client = gspread.authorize(self.creds)
        self.document = self.client.open(db_name)
        print("Conexion establecida con exito.")


# =========================================================================
# 2. REPOSITORIO DE CONTRATOS (Dominio Principal)
# =========================================================================
class ContratosRepository:
    """Maneja las operaciones CRUD de la hoja de contratos."""

    def __init__(self, documento_principal, worksheet_name):
        self.sheet = documento_principal.worksheet(worksheet_name)
        self.headers = self.sheet.row_values(1)
        self.mapa_columnas = {nombre: indice + 1 for indice, nombre in enumerate(self.headers)}
        print(f"Repositorio vinculado a la hoja '{worksheet_name}'.")

    def obtener_registros_pendientes(self, nombre_estacion):
        """Descarga todos los registros y filtra los pendientes por estacion."""
        datos_crudos = self.sheet.get_all_values()
        if not datos_crudos:
            return []

        headers = datos_crudos[0]
        pendientes = []

        try:
            idx_nombre = headers.index("Nombre")
            idx_estacion = headers.index("Estacion de trabajo")
            idx_ejecutado = headers.index("Ejecutado")
        except ValueError as e:
            print(f"Faltan columnas clave en la hoja: {e}")
            return []

        for i in range(1, len(datos_crudos)):
            row = datos_crudos[i]
            if len(row) <= max(idx_nombre, idx_estacion, idx_ejecutado):
                continue

            nombre = row[idx_nombre]
            estacion = row[idx_estacion]
            ejecutado = row[idx_ejecutado]

            if nombre != '' and estacion == nombre_estacion and ejecutado != 'SI':
                registro_dict = dict(zip(headers, row))
                registro_dict['_fila_excel'] = i + 1
                pendientes.append(registro_dict)

        return pendientes

    def actualizar_celda_por_nombre(self, fila_excel, nombre_columna, valor):
        """Actualiza una celda buscando la columna por nombre de header."""
        numero_columna = self.mapa_columnas.get(nombre_columna)
        if not numero_columna:
            raise Exception(f"No se encontro la columna '{nombre_columna}' en la cabecera.")
        self.sheet.update_cell(fila_excel, numero_columna, valor)

    def actualizar_estado_ejecucion(self, fila_excel):
        """
        Marca la fila como ejecutada (finalizada), sin importar si termino con
        exito o con error. Evita que quede reintentandose indefinidamente; el
        detalle del fallo, si lo hubo, queda en la columna de log de errores.
        """
        self.actualizar_celda_por_nombre(fila_excel, 'Ejecutado', 'SI')

    def reportar_error(self, fila_excel, mensaje_error, paso_fallido="Paso no identificado"):
        """
        Acumula el error cronologicamente (mas reciente arriba, con timestamp) en
        la columna 'Log de errores', en vez de sobrescribir el valor anterior.

        Inspirado en agregar_observacion_con_historial() de automation-gt-contracts-v2-udea-main.
        Busca 'Log de errores' primero; si la hoja aun no la tiene, cae a los
        nombres de columna previos ('Comentarios'/'Observaciones'/'Errores') por
        compatibilidad hacia atras.
        """
        from datetime import datetime

        mensaje_completo = f"FALLO EN [{paso_fallido}] -> {mensaje_error}"
        print(f"Error en fila {fila_excel}: {mensaje_completo}")

        nombre_col = next(
            (c for c in ['Log de errores', 'Comentarios', 'Observaciones', 'Errores'] if c in self.mapa_columnas),
            None
        )
        if not nombre_col:
            print("  [AVISO] No se encontro columna de log de errores en la hoja. Error no persistido.")
            return

        numero_columna = self.mapa_columnas[nombre_col]
        timestamp = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        mensaje_con_fecha = f"[{timestamp}] - {mensaje_completo}"

        valor_previo = (self.sheet.cell(fila_excel, numero_columna).value or "").strip()
        texto_final = f"{mensaje_con_fecha}\n{valor_previo}" if valor_previo else mensaje_con_fecha

        self.sheet.update_cell(fila_excel, numero_columna, texto_final)


# =========================================================================
# 3. REPOSITORIO DE CONFIGURACIONES (Datos Maestros)
# =========================================================================
class ConfigRepository:
    """Extrae datos maestros de hojas auxiliares."""

    def __init__(self, documento_principal):
        self.document = documento_principal

    def obtener_datos_maestros(self, nombre_pestania: str) -> list:
        """Descarga cualquier pestania generica y devuelve sus registros."""
        try:
            sheet = self.document.worksheet(nombre_pestania)
            registros = sheet.get_all_records()
            return registros
        except Exception as e:
            print(f"Error al cargar la pestania '{nombre_pestania}': {e}")
            return []

    def obtener_ciudades_codigos(self) -> dict:
        """Carga el mapeo de ciudades a codigos desde la hoja DATA_CIUDADES_CODIGOS."""
        try:
            sheet = self.document.worksheet("DATA_CIUDADES_CODIGOS")
            datos = sheet.get_all_values()
            return {row[0]: row[1] for row in datos[1:]}
        except Exception as e:
            print(f"Error al cargar ciudades/codigos: {e}")
            return {}
