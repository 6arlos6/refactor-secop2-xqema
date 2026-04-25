# -*- coding: utf-8 -*-
from datetime import datetime

# === CONSTANTES DE EXCLUSION (extraidas de globales.py) ===
TIPOLOGIAS_EXCLUIDAS = [
    'CERTIFICADO DE ANTECEDENTES',
    'DOCUMENTO DE IDENTIDAD',
    'CERTIFICACIÓN BANCARIA',
    'CERTIFICACION BANCARIA'
]

NOMBRES_EXCLUIDOS = [
    'DELITOSSEXUALES',
    'DELITOS_SEXUALES',
    'DELITOS-SEXUALES',
    'DELITOS SEXUALES',
    'REGISTRO-DEUDORES-MOROSOS-ALIMENTARIOS',
    'REGISTRO_DEUDORES_MOROSOS_ALIMENTARIOS',
    'REGISTRO-DEUDORES-MOROSOS-ALIMENTARIOS',
    'REGISTRODEUDORESMOROSOSALIMENTARIOS',
    'DEUDORES-MOROSOS',
    'DEUDORES_MOROSOS',
    'DEUDORES MOROSOS',
    'DEUDORESMOROSOS',
    'REDAM'
]

# === DICCIONARIO DE NORMALIZACION DE TIPOLOGIA ===
DICCIONARIO_NORMALIZACION_TIPOLOGIA = {
    "Arrendamiento De Inmuebles": "Arrendamiento de muebles",
    "Compraventa": "Compraventa",
    "Prestación De Servicios": "Prestación de servicios",
    "Obra": "Obra",
    "Contrato De Arrendamiento": "Arrendamiento de muebles",
    "Contrato De Compraventa": "Compraventa",
    "Contrato de Prestación de Servicios": "Prestación de servicios",
    "Contrato De Suministro": "Suministro",
    "Suministro": "Suministro"
}

# === CARACTERES INVALIDOS PARA DESCRIPCION ===
INVALID_CHARS = ['"', "'", "<", ">", "&", "%", "@", "$", "-", "#", "_", "–", "°", "º", "*", "±", "[", "]", "+", "•", "|", "–"]


def obtener_dias(fecha_inicio: str, fecha_fin: str) -> str:
    """Calcula la diferencia en dias entre dos fechas en formato dd/mm/YYYY."""
    date_obj1 = datetime.strptime(fecha_inicio, '%d/%m/%Y')
    date_obj2 = datetime.strptime(fecha_fin, '%d/%m/%Y')
    resultado = date_obj2 - date_obj1
    return str(resultado).split(" ")[0]


def contains_invalid_chars(s: str) -> bool:
    """Valida que el objeto del contrato no contenga caracteres no validos."""
    for char in s:
        if char in INVALID_CHARS:
            return True
    return False


def normalizar_tipo_contrato(tipo_contrato: str) -> str:
    """Normaliza el tipo de contrato usando el diccionario de homologacion."""
    return DICCIONARIO_NORMALIZACION_TIPOLOGIA.get(tipo_contrato, "Otro")


def deconstruir_cdps_saldos(valores) -> list:
    """Valida si hay salto de linea en los CDPs/saldos para deconstruirlos en lista."""
    if '\n' in str(valores):
        return valores.split('\n')
    return [str(valores)]


def extraer_datos_fila(row: dict) -> dict:
    """
    Mapea las 21 columnas del spreadsheet a un diccionario limpio.
    Reemplaza la extraccion manual de variables en automatizacion.py lineas 179-201.
    """
    codigo_cdp = deconstruir_cdps_saldos(row.get("Código CDP", ""))
    saldo_cdp = deconstruir_cdps_saldos(row.get("Saldo CDP", ""))

    return {
        'nombre_proceso': str(row.get("Nombre", "")),
        'unidad_contratacion': str(row.get("Unidad de contratación", "")),
        'objeto_descripcion': str(row.get("Objeto (Descripción)", "")),
        'codigo': str(row.get("Clasificación del bien o servicio", "")),
        'documento_proveedor': str(row.get("Numero de documento del proveedor", "")),
        'nombre_proveedor': str(row.get("Nombre del proveedor", "")),
        'tipo_proveedor': str(row.get("Tipo de entidad / Proveedor", "")),
        'tipo_identificador': str(row.get("Tipo de identificador", "")),
        'localizacion': str(row.get("Localización (Ciudad)", "")),
        'tipo_contrato': str(row.get("Tipo de contrato", "")),
        'email': str(row.get("Correo electrónico proveedor", "")),
        'contrato_marco': str(row.get("Contrato Marco", "")),
        'acuerdos_comerciales': str(row.get("Acuerdos comerciales", "")),
        'fecha_inicio': str(row.get("Fecha de incio", "")),
        'fecha_fin': str(row.get("Fecha de terminación", "")),
        'fecha_firma_contrato': str(row.get("Firma Contrato", "")),
        'valor_estimado': str(row.get("Valor estimado", "")),
        'destinacion_gasto': str(row.get("Destinación Gasto", "")),
        'tipo_cdp': str(row.get("Tipo CDP", "")),
        'codigo_cdp': codigo_cdp,
        'saldo_cdp': saldo_cdp,
        # Estados de procesos previos
        'proceso_1': str(row.get("Proceso 1", "")),
        'proceso_2': str(row.get("Proceso 2", "")),
        'proceso_3': str(row.get("Proceso 3", "")),
        'proceso_4': str(row.get("Proceso 4", "")),
        'proceso_5': str(row.get("Proceso 5", "")),
    }
