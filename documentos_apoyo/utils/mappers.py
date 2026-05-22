from datetime import datetime
import re
import unicodedata

def normalizar_tipologia(tipo_contrato_sap: str) -> str:
    """
    Convierte la tipología proveniente del ERP (SAP) a la 
    opción exacta requerida por los selects de Gestión Transparente.
    """
    if not tipo_contrato_sap:
        return "Atípicos"

    diccionario = {   
        "Compraventa": "Compraventa", 
        "Prestación De Servicios": "Contrato de Prestación de Servicios",
        "Obra": "Contrato de Obra",
        "Contrato De Compraventa": "Compraventa", 
        "Contrato de Prestación de Servicios": "Contrato de Prestación de Servicios",
        "Contrato De Suministro": "Suministro",
        "Suministro": "Suministro"
    }
    
    # Busca la clave; si no existe, devuelve "Atípicos" por defecto
    return diccionario.get(tipo_contrato_sap.strip(), "Atípicos")


def ajustar_rubro(rubro: str) -> str:
    """
    Convierte un rubro numérico plano en su formato contable con puntos.
    Ej: '21201010030301' -> '2.1.2.01.01.003.03.01'
    """
    rubro = str(rubro).strip()
    
    if not rubro or "." in rubro:
        return rubro
        
    if len(rubro) == 1:
        return rubro

    tramos = [1, 1, 1, 2, 2, 3, 2, 2, 2, 2] 
    
    resultado = []
    indice_actual = 0
    
    for tamano_tramo in tramos:
        tramo_extraido = rubro[indice_actual : indice_actual + tamano_tramo]
        
        if tramo_extraido:
            resultado.append(tramo_extraido)
            indice_actual += tamano_tramo
            
        if indice_actual >= len(rubro):
            break
            
    return ".".join(resultado)

def formatear_fecha_gt(fecha_cruda: str) -> str:
    """
    Garantiza que la fecha SIEMPRE salga en formato YYYY-MM-DD 
    (ej. "2026-02-23") que es el que exige el sistema de Gestión Transparente.
    """
    fecha_cruda = str(fecha_cruda).strip()
    if not fecha_cruda:
        return ""

    fecha_limpia = fecha_cruda.split(" ")[0] 

    # Si ya viene en el formato correcto (ej. 2026-02-23), la dejamos pasar intacta
    if "-" in fecha_limpia and len(fecha_limpia) == 10:
        return fecha_limpia

    # Si viene en formato latino (ej. 23/02/2026), la convertimos al ISO
    if "/" in fecha_limpia:
        try:
            obj_fecha = datetime.strptime(fecha_limpia, "%d/%m/%Y")
            return obj_fecha.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return fecha_cruda

def obtener_malla_documental(grupo_compra: str) -> dict:
    """
    Retorna el diccionario de mapeo Regex -> Tipología en GT
    dependiendo del grupo de compras del contrato.
    """
    grupo = str(grupo_compra).strip().upper()
    international_groups = ['E01', 'E02', 'E03']
    national_groups = ['C01', 'C02', 'C03']

    mapping_international = {
        '(?i)^Certificado-de-Registro-Presupuestal.*': 'Registro presupuestal.',
        '(?i)^Estudio-de-necesidad-y-conveniencia.*': 'Estudio y documentos previos.',
        '(?i)^Certificado-de-disponibilidad-presupuestal.*': 'Disponibilidad presupuestal en contrato inicial, Artículo 71 Decreto 111 de 1996 y Artículo 21 Decreto 115 de 1996'
    }

    mapping_national = {
        '(?i)^Certificado-de-Registro-Presupuestal.*': 'Registro presupuestal.',
        '(?i)^Estudio-de-necesidad-y-conveniencia.*': 'Estudio y documentos previos.',
        '(?i)^Certificado-de-disponibilidad-presupuestal.*': 'Disponibilidad presupuestal en contrato inicial, Artículo 71 Decreto 111 de 1996 y Artículo 21 Decreto 115 de 1996',
        '(?i)^Contrato.*': 'Pedido UdeA AMP'
    }

    mapping_complete = {
        '(?i)^Certificado-de-Registro-Presupuestal.*': 'Registro presupuestal.',
        '(?i)^Registro-Unico-Tributario.*': 'RUT Registro Unico Tributario.',
        '(?i)^Documento-de-identidad.*': 'Fotocopia de la Cedula contratista o Representante Legal',
        '(?i)^Estudio-de-necesidad-y-conveniencia.*': 'Estudio y documentos previos.',
        '(?i)^Contrato.*': 'Minuta del contrato.',
        '(?i)^Certificado-de-disponibilidad-presupuestal.*': 'Disponibilidad presupuestal en contrato inicial, Artículo 71 Decreto 111 de 1996 y Artículo 21 Decreto 115 de 1996',
        '(?i)^Certificado-de-seguridad-social-y-parafiscales.*': 'Constancia de afiliación de seguridad social integral en salud, riesgos y pensiones.'
    }

    if grupo in international_groups:
        return mapping_international
    elif grupo in national_groups:
        return mapping_national
    else:
        return mapping_complete

def homologar_archivo_a_tipologia(nombre_archivo: str, malla_documental: dict) -> str:
    """
    Evalúa el nombre de un archivo físico contra las expresiones regulares de la malla.
    Si hace match, retorna el string exacto de la tipología en GT. Si no, retorna None.
    """
    for regex_file, tipologia_gt in malla_documental.items():
        if re.search(regex_file, nombre_archivo):
            return tipologia_gt
    return None

def formatear_valor_gt(valor_crudo) -> str:
    """
    Convierte un valor plano al formato entero de Gestión Transparente: "$ 4.944.050"
    Ignora y elimina cualquier decimal que provenga del Excel.
    """
    if valor_crudo is None or str(valor_crudo).strip() == "":
        return ""

    try:
        valor_limpio = str(valor_crudo).replace('$', '').replace(' ', '').replace(',', '').strip()
        
        valor_entero = int(float(valor_limpio))
        
        valor_formateado = f"{valor_entero:,}".replace(',', '.')

        return f"$ {valor_formateado}"
        
    except ValueError:
        print(f"⚠️ Advertencia: No se pudo formatear el valor '{valor_crudo}'. Se usará tal cual.")
        return str(valor_crudo).strip()
    

def obtener_rubros_unicos_por_contrato(registros: list, contrato_id: str) -> list:
    """
    Filtra una lista de diccionarios (filas de Excel) buscando un contrato específico,
    y devuelve una lista deduplicada de sus rubros y años.
    """
    lista_rubros = []
    rubros_vistos = set()

    for fila in registros:
        if str(fila.get('Número', '')).strip() == str(contrato_id).strip():
            
            anio = str(fila.get('Año Rubro', '')).strip()
            rubro_crudo = str(fila.get('Rubro Presupuestal', '')).strip()
            
            rubro_formateado = ajustar_rubro(rubro_crudo)
            
            if rubro_formateado:
                llave_unica = f"{anio}-{rubro_formateado}"
                
                if llave_unica not in rubros_vistos:
                    rubros_vistos.add(llave_unica)
                    lista_rubros.append({
                        'anio_rubro': anio,
                        'rubro': rubro_formateado
                    })

    return lista_rubros

def normalizar_texto(texto: str) -> str:
    """
    Procesa nombres de departamentos o ciudades:
    1. Convierte a minúsculas.
    2. Corta el texto en la primera coma o punto.
    3. Elimina tildes y diacríticos.
    4. Limpia espacios residuales.
    """
    if not texto:
        return ""
        
    # 1. Convertir a minúsculas
    texto_limpio = str(texto).lower()
    
    # 2. Eliminar todo lo que esté después de una coma o un punto
    # re.split corta el texto usando ',' o '.' y nos quedamos con la posición [0]
    texto_limpio = re.split(r'[,.]', texto_limpio)[0]
    
    # 3. Quitar tildes (Normalización Unicode)
    # NFD separa la vocal de la tilde (ej: 'á' se vuelve 'a' + '´')
    # Luego filtramos e ignoramos los caracteres de tipo 'Mn' (Marcas no espaciadas / tildes)
    texto_limpio = ''.join(
        letra for letra in unicodedata.normalize('NFD', texto_limpio)
        if unicodedata.category(letra) != 'Mn'
    )
    
    # 4. Limpiar espacios en blanco al inicio o al final
    return texto_limpio.strip()


def construir_diccionario_homologacion(datos_crudos: list[dict], col_llave="Buscado", col_valor="Equivalente") -> dict:
    """Convierte datos crudos en un diccionario de búsqueda O(1)."""
    return {
        str(row[col_llave]).strip(): str(row[col_valor]).strip()
        for row in datos_crudos 
        if str(row.get(col_llave, '')).strip() != ""
    }

def homologar_departamento(depto_buscado: str, mapa_deptos: dict) -> str:
    """
    Busca el departamento exacto en el diccionario de excepciones (DEPTOS_ESPECIALES).
    Si existe, retorna el equivalente de GT tal cual está. 
    Si no, retorna el string original.
    """
    if not depto_buscado:
        return ""
    
    return mapa_deptos.get(depto_buscado, depto_buscado)

def extraer_solo_numeros(texto: str) -> str:
    """
    Limpia cualquier string y retorna únicamente los caracteres numéricos.
    """
    if not texto:
        return ""
    
    # \D significa "todo lo que NO sea un dígito". 
    # Lo reemplazamos por nada ('')
    texto_limpio = re.sub(r'\D', '', str(texto))
    
    return texto_limpio

def construir_datos_contratista(data: dict, diccionario_deptos: dict) -> dict:
    """Extrae y formatea toda la lógica relacionada con el contratista."""
    tipo_id = str(data.get('Tipo identificación', ''))
    identificacion_cruda = str(data.get('Identificación', ''))
    identificacion_procesada = extraer_solo_numeros(identificacion_cruda)
    es_juridica = tipo_id.upper() in ['NIT']
    
    depto_crudo = str(data.get('Departamento', 'Antioquia'))
    depto_normalizado = normalizar_texto(depto_crudo)
    
    return {
        'identificacion': identificacion_cruda,
        'es_juridica': es_juridica,
        'tipo_identificacion_juridica': tipo_id if es_juridica else '',
        'identificacion_juridica': identificacion_procesada if es_juridica else '',
        'tipo_identificacion_natural': 'cedula de ciudadania' if es_juridica else normalizar_texto(tipo_id),
        'identificacion_natural': extraer_solo_numeros(str(data.get('Documento representante legal', ''))) if es_juridica else identificacion_procesada,
        'razon_social': str(data.get('Nombre del proveedor', '')),
        'nombre_cont_o_rep': str(data.get('Nombre representante legal', '')) or str(data.get('Nombre del proveedor', '')),
        'direccion': str(data.get('Dirección', '')),
        'pais': str(data.get('Pais', '')).strip().upper(),
        'departamento': depto_normalizado,
        'departamento_telefonos': homologar_departamento(depto_normalizado, diccionario_deptos),
        'ciudad': normalizar_texto(str(data.get('Ciudad', 'Medellín'))),
        'telefono': extraer_solo_numeros(str(data.get('Número del proveedor', '')))
    }

def construir_datos_formulario(data: dict, lista_rubros: list) -> dict:
    """Calcula la lógica de moneda y ensambla el diccionario del formulario."""
    tipo_moneda = str(data.get('Moneda', 'COP')).strip().upper()
    valor_normal = str(data.get('Valor', 0)).strip()
    valor_rp = str(data.get('Valor RP', 0)).strip()
    
    aplica_moneda_extranjera = "SI" if tipo_moneda not in ["COP", ""] else "NO"
    valor_contrato_final = valor_rp if aplica_moneda_extranjera == "SI" else valor_normal
    valor_extranjera_final = valor_normal if aplica_moneda_extranjera == "SI" else "0"

    return {
        'objeto': str(data.get('Objeto del Contrato', '')),
        'fecha_suscripcion': str(data.get('Fecha de suscripción', '')),
        'fecha_inicio': str(data.get('Fecha Inicio', '')),
        'fecha_fin': str(data.get('Fecha Fin', '')),
        'valor': valor_contrato_final,
        'tipologia': str(data.get('Procedimiento / Causal', '')),
        'tipo_contrato': normalizar_tipologia(str(data.get('Tipo de Contrato', ''))),
        'moneda_extranjera': aplica_moneda_extranjera,
        'tipo_moneda': tipo_moneda,
        'valor_moneda': valor_extranjera_final,
        'url_secop': str(data.get('URL del Contrato en el SECOP', '')),
        'rubros': lista_rubros
    }